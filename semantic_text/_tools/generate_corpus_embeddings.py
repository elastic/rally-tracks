"""
Generate chunk-level embeddings for any HuggingFace dataset using
configurable models and fields.

Output: JSONL, one record per chunk with fields:
  doc_id, chunk_id, chunk_start, chunk_end, chunk_text, embedding
"""

import argparse
import bz2
import gc
import json
import os
import time

import numpy as np
import torch
from datasets import load_dataset
from tqdm import tqdm
from transformers import AutoModel

from sentence_boundary_chunker import SentenceBoundaryChunker


DEFAULT_MODEL_NAME = "jinaai/jina-embeddings-v5-text-small"
DEFAULT_MAX_ROWS_PER_FILE = 1_000_000

CHUNK_MAX_WORDS = 250
CHUNK_INCLUDE_PRECEDING = True

FLUSH_EVERY = 20_000


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate chunk-level embeddings for a HuggingFace dataset."
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL_NAME,
        help=f"Embedding model name (default: {DEFAULT_MODEL_NAME})",
    )
    parser.add_argument("--dataset", required=True, help="HuggingFace dataset name")
    parser.add_argument(
        "--subset",
        default="corpus",
        help="Dataset subset/config name (default: corpus)",
    )
    parser.add_argument(
        "--split",
        default="corpus",
        help="Dataset split (default: corpus)",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory (default: /tmp/{dataset}-embeddings)",
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
        help="Dataset field to use as doc_id (default: _id)",
    )
    parser.add_argument(
        "--text-field",
        default="text",
        help="Dataset field to use as text (default: text)",
    )
    parser.add_argument(
        "--title-field",
        default=None,
        help="Optional dataset field to prepend to text as '<title>\\n<text>' (default: disabled)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from existing output files, skipping already-processed doc_ids",
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
            _ = model.encode(texts[:batch_size], task="retrieval", prompt_name="document")
        torch.cuda.empty_cache()
        return True
    except torch.cuda.OutOfMemoryError:
        torch.cuda.empty_cache()
        gc.collect()
        return False


def find_optimal_batch_size(model, sample_texts):
    """Binary search for the largest batch that fits. Calibrates on the
    longest real chunks so we match worst-case memory."""
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
        embs = model.encode(texts, task="retrieval", prompt_name="document")
    if isinstance(embs, torch.Tensor):
        return embs.cpu().float().numpy()
    if isinstance(embs, list):
        return torch.stack(embs).cpu().float().numpy()
    return np.array(embs, dtype=np.float32)


def encode_texts(model, texts, batch_size):
    out = []
    total = len(texts)
    i = 0
    with tqdm(total=total, desc="  Encoding chunks", unit="chunk") as pbar:
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
                    tqdm.write(f"  WARNING: OOM on single chunk at index {i}, writing zero vector")
                    out.append(np.zeros((1, out[0].shape[1] if out else 512), dtype=np.float32))
                    i += 1
                    pbar.update(1)
                else:
                    batch_size = max(1, len(batch) // 2)
                    tqdm.write(f"  OOM at offset {i}, reducing batch_size to {batch_size}")
    return np.concatenate(out, axis=0)


def _output_path(output_dir: str, part: int) -> str:
    return os.path.join(output_dir, f"corpus_with_embeddings_part{part:03d}.jsonl")


def load_resume_state(output_dir):
    """Scan existing output files and return (seen_doc_ids, next_file_part).

    Recognises both plain .jsonl and bz2-compressed .jsonl.bz2 output files.
    Always starts a new file part on resume to avoid appending to a
    potentially truncated last file left by an interrupted run.
    """
    seen_ids = set()
    part = 0
    while True:
        base = _output_path(output_dir, part + 1)
        if os.path.exists(base):
            path, opener = base, open
        elif os.path.exists(base + ".bz2"):
            path, opener = base + ".bz2", bz2.open
        else:
            break
        part += 1
        print(f"  Scanning {path}...")
        with opener(path, "rt", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    seen_ids.add(json.loads(line)["doc_id"])
                except (json.JSONDecodeError, KeyError):
                    pass
    print(f"  Resume: {len(seen_ids):,} doc_ids already processed across {part} file(s), continuing from part {part + 1:03d}")
    return seen_ids, part + 1


def main():
    args = parse_args()

    model_name = args.model
    dataset_name = args.dataset
    subset = args.subset
    split = args.split
    output_dir = args.output_dir or f"/tmp/{dataset_name.replace('/', '-')}-embeddings"
    max_rows_per_file = args.max_rows_per_file
    id_field = args.id_field
    text_field = args.text_field
    title_field = args.title_field

    print(f"Loading {dataset_name} (subset={subset}, split={split}, streaming)...")
    try:
        corpus = load_dataset(dataset_name, subset, split=split, streaming=True)
    except RuntimeError as e:
        if "Dataset scripts are no longer supported" not in str(e):
            raise
        # Fall back to loading raw parquet/jsonl files from the Hub
        print(f"  Script-based loading failed ({e}). Trying parquet fallback...")
        corpus = load_dataset(
            "parquet",
            data_files=f"hf://datasets/{dataset_name}/{subset}/*.parquet",
            split="train",
            streaming=True,
        )

    os.makedirs(output_dir, exist_ok=True)

    seen_ids = set()
    if args.resume:
        seen_ids, file_part = load_resume_state(output_dir)
    else:
        file_part = 1

    model = load_model(model_name)
    chunker = SentenceBoundaryChunker()

    rows_in_file = 0
    total_chunks = 0
    batch_size = None
    t_enc = time.time()

    f = open(_output_path(output_dir, file_part), "w")
    print(f"  Opened {_output_path(output_dir, file_part)}")

    def flush_buffer(buf):
        nonlocal batch_size, file_part, rows_in_file, total_chunks, f

        if batch_size is None:
            sample = [c[4] for c in buf[:4096]]
            batch_size = find_optimal_batch_size(model, sample)
            print(f"Encoding in blocks of {FLUSH_EVERY:,} chunks (streaming to {output_dir}/corpus_with_embeddings_part*.jsonl)...")

        embs = encode_texts(model, [c[4] for c in buf], batch_size)
        for (doc_id, chunk_id, chunk_start, chunk_end, chunk_text), emb in zip(buf, embs):
            if rows_in_file >= max_rows_per_file:
                f.close()
                file_part += 1
                rows_in_file = 0
                f = open(_output_path(output_dir, file_part), "w")
                print(f"  Opened {_output_path(output_dir, file_part)}")

            record = {
                "doc_id": str(doc_id),
                "chunk_id": chunk_id,
                "chunk_start": chunk_start,
                "chunk_end": chunk_end,
                "chunk_text": chunk_text,
                "embedding": emb.tolist(),
            }
            f.write(json.dumps(record) + "\n")
            rows_in_file += 1

        total_chunks += len(buf)
        del embs
        gc.collect()
        print(f"  Flushed {total_chunks:,} chunks so far")

    buffer = []
    try:
        for row in tqdm(corpus, desc="Processing docs"):
            doc_id = row[id_field]
            if doc_id in seen_ids:
                continue
            text = row[text_field]
            if title_field and row.get(title_field):
                text = row[title_field] + "\n" + text
            offsets = chunker.chunk(text, CHUNK_MAX_WORDS, CHUNK_INCLUDE_PRECEDING)
            for chunk_id, (start, end) in enumerate(offsets):
                buffer.append((doc_id, chunk_id, start, end, text[start:end]))

            if len(buffer) >= FLUSH_EVERY:
                flush_buffer(buffer)
                buffer.clear()

        if buffer:
            flush_buffer(buffer)
            buffer.clear()
    finally:
        f.close()

    print(f"Encoded {total_chunks:,} chunks in {time.time() - t_enc:.1f}s")
    print(f"Wrote {file_part} output file(s) to {output_dir}/")


if __name__ == "__main__":
    main()
