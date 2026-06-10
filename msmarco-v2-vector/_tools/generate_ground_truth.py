#!/usr/bin/env python3
"""
Generate brute-force ground truth files for msmarco-v2-vector recall measurement.

Loads query embeddings from the existing queries-recall.json.bz2, streams document
vectors from the Hugging Face Cohere/msmarco-v2-embed-english-v3 dataset, computes
exact dot-product similarities, and writes per-query top-K nearest neighbors in the
format expected by the Rally track's KnnRecallRunner.

Setup:
    python3 -m venv ground-truth-env
    source ground-truth-env/bin/activate
    pip install datasets numpy huggingface_hub

Usage:
    python generate_ground_truth.py --doc-count 18000000 --output queries-recall-18m.json
    python generate_ground_truth.py --doc-count 36000000 --output queries-recall-36m.json

The output is uncompressed JSONL.  Compress with bzip2 afterwards:
    bzip2 queries-recall-18m.json

Parallelism:
    --workers controls how many processes decode Arrow batches in parallel.
    numpy matmul uses all available cores via OpenBLAS/MKL automatically.
    Set OMP_NUM_THREADS or MKL_NUM_THREADS to tune numpy thread count.

AWS instance recommendation:
    c7i.8xlarge (32 vCPU, 64 GB RAM, 12.5 Gbps) is a good balance.
    See scaling-benchmark-plan.md for details.
"""

import argparse
import bz2
import json
import os
import time

import numpy as np

TRACK_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUERIES_RECALL_FILE = os.path.join(TRACK_DIR, "queries-recall.json.bz2")

DATASET_NAME = "Cohere/msmarco-v2-embed-english-v3"
DIMS = 1024
TOP_K = 1000
BATCH_SIZE = 50_000
PROGRESS_INTERVAL = 500_000


def sigmoid_score(dot_product, out=None):
    """Replicate ES script_score: sigmoid(1, Math.E, -dotProduct(q, d))"""
    if out is None:
        return 1.0 / (1.0 + np.exp(-dot_product))
    np.negative(dot_product, out=out)
    np.exp(out, out=out)
    out += 1.0
    np.reciprocal(out, out=out)
    return out


def load_queries():
    """Load the 76 recall queries (embeddings + metadata) from the track."""
    queries = []
    with bz2.open(QUERIES_RECALL_FILE, "r") as f:
        for line in f:
            q = json.loads(line)
            queries.append(q)
    print(f"Loaded {len(queries)} queries from {QUERIES_RECALL_FILE}")
    return queries


def build_query_matrix(queries):
    """Stack query embeddings into a (n_queries, dims) float64 matrix.

    float64 matches Java double precision used by ES script_score, reducing
    tie-break differences at score boundaries.  The (76, 1024) matrix is tiny
    so the memory cost is negligible, and numpy auto-promotes the matmul result
    to float64 when multiplied with float32 document vectors.
    """
    embs = [q["emb"] for q in queries]
    return np.array(embs, dtype=np.float64)


def normalize_rows(matrix):
    """L2-normalize each row in-place (matching vg.normalize in parse_documents.py)."""
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    matrix /= norms
    return matrix


class TopKAccumulator:
    """
    Maintains per-query top-K results using numpy arrays.  Merges each batch
    with argpartition — no Python-level per-document loops.
    """

    def __init__(self, n_queries, top_k):
        self.n_queries = n_queries
        self.top_k = top_k
        self.scores = np.full((n_queries, top_k), -np.inf, dtype=np.float64)
        self.doc_ids = np.empty((n_queries, top_k), dtype=object)
        self.filled = 0  # how many columns have real data (0..top_k)

    def add_batch(self, query_matrix, doc_ids_batch, doc_vecs_batch):
        """
        query_matrix: (n_queries, dims) float32
        doc_vecs_batch: (batch_size, dims) float32
        doc_ids_batch: list of str, length batch_size
        """
        batch_scores = query_matrix @ doc_vecs_batch.T  # (n_queries, batch_size)
        sigmoid_score(batch_scores, out=batch_scores)
        batch_size = batch_scores.shape[1]
        doc_ids_arr = np.array(doc_ids_batch, dtype=object)

        if self.filled < self.top_k:
            take = min(batch_size, self.top_k - self.filled)
            end = self.filled + take
            self.scores[:, self.filled:end] = batch_scores[:, :take]
            self.doc_ids[:, self.filled:end] = doc_ids_arr[:take]
            self.filled = end
            if take < batch_size:
                remaining_scores = batch_scores[:, take:]
                remaining_ids = doc_ids_arr[take:]
                self._merge(remaining_scores, remaining_ids)
            return

        self._merge(batch_scores, doc_ids_arr)

    def _merge(self, batch_scores, doc_ids_arr):
        """Merge batch results with current top-K using argpartition."""
        k = self.top_k
        combined_scores = np.concatenate([self.scores, batch_scores], axis=1)

        batch_ids_2d = np.tile(doc_ids_arr, (self.n_queries, 1))
        combined_ids = np.concatenate([self.doc_ids, batch_ids_2d], axis=1)

        n_total = combined_scores.shape[1]
        top_k_indices = np.argpartition(combined_scores, n_total - k, axis=1)[:, -k:]

        rows = np.arange(self.n_queries)[:, None]
        self.scores = combined_scores[rows, top_k_indices].copy()
        self.doc_ids = combined_ids[rows, top_k_indices].copy()

    def get_results(self):
        """Return list of (doc_id, score) lists, sorted descending by score."""
        results = []
        for qi in range(self.n_queries):
            order = np.argsort(-self.scores[qi])
            items = [
                [str(self.doc_ids[qi, idx]), round(float(self.scores[qi, idx]), 7)]
                for idx in order
                if self.scores[qi, idx] > -np.inf
            ]
            results.append(items)
        return results


def stream_dataset_arrow(doc_count, num_workers, batch_size):
    """
    Load the dataset, then yield batches by slicing the underlying Arrow table
    directly — avoids the expensive ds.select() per-batch overhead.

    Vectors are extracted by flattening the Arrow list column into a single
    contiguous float array, then reshaping — much faster than per-row conversion.
    """
    from datasets import load_dataset

    print(f"Loading dataset split train[:{doc_count}] with {num_workers} workers ...")
    t0 = time.time()
    ds = load_dataset(
        DATASET_NAME,
        split=f"train[:{doc_count}]",
        num_proc=num_workers if num_workers > 1 else None,
        columns=["_id", "emb"],
    )
    print(f"Dataset loaded in {time.time() - t0:.1f}s  ({len(ds):,} rows)")

    table = ds.data  # pyarrow.Table — zero-copy access to backing data
    total = table.num_rows
    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        chunk = table.slice(start, end - start)
        doc_ids = chunk.column("_id").to_pylist()
        emb_col = chunk.column("emb").combine_chunks()
        flat = emb_col.values.to_numpy(zero_copy_only=False).astype(np.float32)
        n_rows = end - start
        vecs = flat.reshape(n_rows, -1)
        normalize_rows(vecs)
        yield doc_ids, vecs


def write_output(queries, accumulator, output_path):
    """Write ground truth JSONL matching the format of queries-recall.json.bz2."""
    all_results = accumulator.get_results()
    with open(output_path, "w") as f:
        for qi, q in enumerate(queries):
            line = {
                "query_id": q["query_id"],
                "text": q["text"],
                "emb": q["emb"],
                "ids": all_results[qi],
            }
            f.write(json.dumps(line) + "\n")
    print(f"Wrote {len(queries)} queries to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate brute-force ground truth for msmarco-v2-vector subsets"
    )
    parser.add_argument(
        "--doc-count", type=int, required=True,
        help="Number of documents from the dataset to use (e.g. 18000000)"
    )
    parser.add_argument(
        "--output", type=str, required=True,
        help="Output JSONL file path (e.g. queries-recall-18m.json)"
    )
    parser.add_argument(
        "--top-k", type=int, default=TOP_K,
        help=f"Number of nearest neighbors per query (default: {TOP_K})"
    )
    parser.add_argument(
        "--batch-size", type=int, default=BATCH_SIZE,
        help=f"Documents per batch for matmul (default: {BATCH_SIZE})"
    )
    parser.add_argument(
        "--workers", type=int, default=4,
        help="Number of parallel workers for dataset loading (default: 4)"
    )
    args = parser.parse_args()

    batch_size = args.batch_size

    queries = load_queries()
    query_matrix = build_query_matrix(queries)
    n_queries = len(queries)

    accumulator = TopKAccumulator(n_queries, args.top_k)

    print(f"Computing top-{args.top_k} neighbors for {n_queries} queries "
          f"over {args.doc_count:,} documents ...")
    print(f"Batch size: {batch_size:,}, Workers: {args.workers}")

    docs_processed = 0
    t_start = time.time()

    for doc_ids_batch, doc_vecs_batch in stream_dataset_arrow(args.doc_count, args.workers, batch_size):
        accumulator.add_batch(query_matrix, doc_ids_batch, doc_vecs_batch)
        docs_processed += len(doc_ids_batch)

        if docs_processed % PROGRESS_INTERVAL < batch_size or docs_processed == args.doc_count:
            elapsed = time.time() - t_start
            rate = docs_processed / elapsed if elapsed > 0 else 0
            eta = (args.doc_count - docs_processed) / rate if rate > 0 else 0
            print(f"  {docs_processed:>12,} / {args.doc_count:,} docs  "
                  f"({100*docs_processed/args.doc_count:5.1f}%)  "
                  f"{rate:,.0f} docs/s  ETA {eta:.0f}s")

    elapsed = time.time() - t_start
    print(f"Brute-force search completed in {elapsed:.1f}s "
          f"({docs_processed/elapsed:,.0f} docs/s)")

    write_output(queries, accumulator, args.output)
    print(f"Done. Compress with:  bzip2 {args.output}")


if __name__ == "__main__":
    main()
