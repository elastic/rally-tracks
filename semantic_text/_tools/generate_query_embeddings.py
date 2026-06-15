"""
Generate query-level embeddings for any HuggingFace dataset using
configurable models and fields.

Output: JSONL, one record per query with fields:
  query_id, text, embedding
"""

import argparse
import gc
import json
import os
import time

import numpy as np
import torch
from datasets import load_dataset
from tqdm import tqdm
from transformers import AutoModel


DEFAULT_MODEL_NAME = "jinaai/jina-embeddings-v5-text-small"
DEFAULT_MAX_ROWS_PER_FILE = 1_000_000

FLUSH_EVERY = 20_000


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate query-level embeddings for a HuggingFace dataset."
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL_NAME,
        help=f"Embedding model name (default: {DEFAULT_MODEL_NAME})",
    )
    parser.add_argument("--dataset", required=True, help="HuggingFace dataset name")
    parser.add_argument(
        "--subset",
        default="queries",
        help="Dataset subset/config name (default: queries)",
    )
    parser.add_argument(
        "--split",
        default="queries",
        help="Dataset split (default: queries)",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory (default: /tmp/{dataset}-query-embeddings)",
    )
    parser.add_argument(
        "--max-rows-per-file",
        type=int,
        default=DEFAULT_MAX_ROWS_PER_FILE,
        help=f"Max rows per output file (default: {DEFAULT_MAX_ROWS_PER_FILE:,})",
    )
    parser.add_argument(
        "--id-field",
        default="_id",
        help="Dataset field to use as query_id (default: _id)",
    )
    parser.add_argument(
        "--text-field",
        default="text",
        help="Dataset field to use as text (default: text)",
    )
    return parser.parse_args()


def load_model(model_name):
    print(f"Loading model {model_name}...")
    model = AutoModel.from_pretrained(
        model_name,
        trust_remote_code=True,
        torch_dtype=torch.bfloat16,
    )
    model = model.to("cuda")
    model.eval()
    print(f"Model loaded. VRAM used: {torch.cuda.memory_allocated() / 1e9:.2f} GB")
    return model


def _try_batch(model, texts, batch_size):
    try:
        torch.cuda.empty_cache()
        gc.collect()
        with torch.no_grad():
            _ = model.encode(texts[:batch_size], task="retrieval", prompt_name="query")
        torch.cuda.empty_cache()
        return True
    except torch.cuda.OutOfMemoryError:
        torch.cuda.empty_cache()
        gc.collect()
        return False


def find_optimal_batch_size(model, sample_texts):
    """Binary search for the largest batch that fits. Calibrates on the
    longest real texts so we match worst-case memory."""
    print("Binary searching for optimal batch size...")

    sorted_texts = sorted(sample_texts, key=len, reverse=True)
    n_long = max(len(sorted_texts) // 4, 64)
    test_texts = sorted_texts[:n_long]
    while len(test_texts) < 4096:
        test_texts = test_texts + test_texts
    test_texts = test_texts[:4096]

    lo, hi = 1, 256
    best = 1

    while hi <= 4096:
        if _try_batch(model, test_texts, hi):
            lo = hi
            best = hi
            print(f"  batch_size={best} OK, trying {hi * 2}...")
            hi *= 2
        else:
            print(f"  batch_size={hi} OOM")
            break

    while lo <= hi:
        mid = (lo + hi) // 2
        if _try_batch(model, test_texts, mid):
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1

    safe = max(1, int(best * 0.70))
    print(f"  Max working batch size: {best}, using safe batch size: {safe}")
    return safe


def _encode_batch(model, texts):
    with torch.no_grad():
        embs = model.encode(texts, task="retrieval", prompt_name="query")
    if isinstance(embs, torch.Tensor):
        return embs.cpu().float().numpy()
    if isinstance(embs, list):
        return torch.stack(embs).cpu().float().numpy()
    return np.array(embs, dtype=np.float32)


def encode_texts(model, texts, batch_size):
    out = []
    total = len(texts)
    i = 0
    with tqdm(total=total, desc="  Encoding queries", unit="query") as pbar:
        while i < total:
            batch = texts[i : i + batch_size]
            try:
                out.append(_encode_batch(model, batch))
                pbar.update(len(batch))
                i += batch_size
            except torch.cuda.OutOfMemoryError:
                torch.cuda.empty_cache()
                gc.collect()
                if len(batch) == 1:
                    tqdm.write(f"  WARNING: OOM on single query at index {i}, writing zero vector")
                    out.append(np.zeros((1, out[0].shape[1] if out else 512), dtype=np.float32))
                    i += 1
                    pbar.update(1)
                else:
                    batch_size = max(1, len(batch) // 2)
                    tqdm.write(f"  OOM at offset {i}, reducing batch_size to {batch_size}")
    return np.concatenate(out, axis=0)


def _output_path(output_dir: str, part: int) -> str:
    return os.path.join(output_dir, f"query_with_embeddings_part{part:03d}.jsonl")


def main():
    args = parse_args()

    model_name = args.model
    dataset_name = args.dataset
    subset = args.subset
    split = args.split
    output_dir = args.output_dir or f"/tmp/{dataset_name.replace('/', '-')}-query-embeddings"
    max_rows_per_file = args.max_rows_per_file
    id_field = args.id_field
    text_field = args.text_field

    os.makedirs(output_dir, exist_ok=True)

    print(f"Loading {dataset_name} (subset={subset}, split={split}, streaming)...")
    queries = load_dataset(dataset_name, subset, split=split, streaming=True)

    model = load_model(model_name)

    file_part = 1
    rows_in_file = 0
    total_queries = 0
    batch_size = None
    t_enc = time.time()

    f = open(_output_path(output_dir, file_part), "w")
    print(f"  Opened {_output_path(output_dir, file_part)}")

    def flush_buffer(buf):
        nonlocal batch_size, file_part, rows_in_file, total_queries, f

        if batch_size is None:
            sample = [t for _, t in buf[:4096]]
            batch_size = find_optimal_batch_size(model, sample)
            print(f"Encoding in blocks of {FLUSH_EVERY:,} queries (streaming to {output_dir}/query_with_embeddings_part*.jsonl)...")

        embs = encode_texts(model, [t for _, t in buf], batch_size)
        for (query_id, text), emb in zip(buf, embs):
            if rows_in_file >= max_rows_per_file:
                f.close()
                file_part += 1
                rows_in_file = 0
                f = open(_output_path(output_dir, file_part), "w")
                print(f"  Opened {_output_path(output_dir, file_part)}")

            record = {
                "query_id": str(query_id),
                "text": text,
                "embedding": emb.tolist(),
            }
            f.write(json.dumps(record) + "\n")
            rows_in_file += 1

        total_queries += len(buf)
        del embs
        gc.collect()
        print(f"  Flushed {total_queries:,} queries so far")

    buffer = []
    try:
        for row in tqdm(queries, desc="Processing queries"):
            query_id = row[id_field]
            text = row[text_field]
            buffer.append((query_id, text))

            if len(buffer) >= FLUSH_EVERY:
                flush_buffer(buffer)
                buffer.clear()

        if buffer:
            flush_buffer(buffer)
            buffer.clear()
    finally:
        f.close()

    print(f"Encoded {total_queries:,} queries in {time.time() - t_enc:.1f}s")
    print(f"Wrote {file_part} output file(s) to {output_dir}/")


if __name__ == "__main__":
    main()
