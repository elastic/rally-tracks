#!/usr/bin/env python3
"""
Generate corpus files for the ES|QL unmapped fields benchmark.

Outputs four bz2-compressed NDJSON files in --output-dir:
  unmapped_bench_dense.json.bz2       1 M docs, all 998 fields per doc
  unmapped_bench_dense-1k.json.bz2    first 1,000 docs (Rally --test-mode)
  unmapped_bench_sparse.json.bz2      1 M docs, 10 fields per doc (~1 % density)
  unmapped_bench_sparse-1k.json.bz2   first 1,000 docs (Rally --test-mode)

The -1k files are generated with the same seed and in the same order as the full
files, so their documents are byte-for-byte identical to the first N rows of the
corresponding full corpus.
"""

import argparse
import bz2
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

N_FIELDS = 998  # field_0 through field_997; fits within ES default mapping limit (1000)
N_DOCS_FULL = 1_000_000
N_DOCS_TEST = 1_000
SPARSE_FIELDS_PER_DOC = 10  # ~1 % of N_FIELDS

DEFAULT_SEED = 42
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parents[1] / "_data"

# Timestamps spread over one calendar year starting 2024-01-01
BASE_TS = datetime(2024, 1, 1, tzinfo=timezone.utc)
TS_RANGE_SECONDS = 365 * 24 * 3600

# Value pool: every 4-char lowercase hex string (0000-ffff = 65,536 values).
# Small vocabulary gives excellent bz2 compression on the 12+ GB dense corpus.
VALUE_POOL = [format(i, "04x") for i in range(65536)]
FIELD_NAMES = [f"field_{i}" for i in range(N_FIELDS)]

# Pre-built JSON key fragments to avoid repeated f-string work in the hot loop.
# Each element is the literal bytes  ,"field_NNN":"  ready to be followed by
# the 4-char value and a closing quote.
_FIELD_FRAGS = [f',"field_{i}":"' for i in range(N_FIELDS)]


def _ts(rng: random.Random) -> str:
    offset = rng.randint(0, TS_RANGE_SECONDS)
    return (BASE_TS + timedelta(seconds=offset)).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def dense_line(doc_id: int, rng: random.Random) -> str:
    """Return one NDJSON line for a dense document (all 998 fields present)."""
    ts = _ts(rng)
    values = rng.choices(VALUE_POOL, k=N_FIELDS)
    # Build the JSON string directly to avoid dict creation and json.dumps
    # overhead; safe because timestamps and hex values need no escaping.
    parts = [f'{{"@timestamp":"{ts}","id":{doc_id}']
    for frag, val in zip(_FIELD_FRAGS, values):
        parts.append(frag)
        parts.append(val)
        parts.append('"')
    parts.append("}")
    return "".join(parts)


def sparse_line(doc_id: int, rng: random.Random) -> str:
    """Return one NDJSON line for a sparse document (~10 fields present)."""
    ts = _ts(rng)
    chosen_names = rng.sample(FIELD_NAMES, SPARSE_FIELDS_PER_DOC)
    values = rng.choices(VALUE_POOL, k=SPARSE_FIELDS_PER_DOC)
    # Sparse docs are small enough that building a dict and using json-style
    # manual encoding is straightforward.
    pairs = [f',"@timestamp":"{ts}","id":{doc_id}']
    for name, val in zip(chosen_names, values):
        pairs.append(f',"{name}":"{val}"')
    # Replace first spurious comma: open brace + drop leading comma
    return "{" + "".join(pairs)[1:] + "}"


def write_corpus(path: Path, n_docs: int, line_fn, rng: random.Random, label: str) -> None:
    print(f"  [{label}] writing {n_docs:,} docs -> {path}", flush=True)
    with bz2.open(path, "wt", encoding="utf-8") as fh:
        for doc_id in range(n_docs):
            fh.write(line_fn(doc_id, rng))
            fh.write("\n")
            if (doc_id + 1) % 100_000 == 0:
                pct = 100.0 * (doc_id + 1) / n_docs
                print(f"    {doc_id + 1:>9,} / {n_docs:,}  ({pct:5.1f} %)", end="\r", flush=True)
    size = path.stat().st_size
    print(f"    done  {size:,} bytes  ({size / 1024 ** 2:.1f} MB)          ")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help="Directory to write corpus files into (default: esql/_data/)",
    )
    ap.add_argument("--n-docs", type=int, default=N_DOCS_FULL, help=f"Documents in full corpus files (default {N_DOCS_FULL:,})")
    ap.add_argument("--n-test-docs", type=int, default=N_DOCS_TEST, help=f"Documents in test-mode (-1k) files (default {N_DOCS_TEST:,})")
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED, help=f"Random seed for reproducibility (default {DEFAULT_SEED})")
    args = ap.parse_args()

    d = Path(args.output_dir)
    d.mkdir(parents=True, exist_ok=True)

    print("\n=== Dense corpus (all fields) ===")
    # Test-mode file first; full file uses the same seed so docs 0 through N_TEST-1 match.
    write_corpus(d / "unmapped_bench_dense-1k.json.bz2", args.n_test_docs, dense_line, random.Random(args.seed), "dense-1k")
    write_corpus(d / "unmapped_bench_dense.json.bz2", args.n_docs, dense_line, random.Random(args.seed), "dense-full")

    print("\n=== Sparse corpus (~10 fields/doc) ===")
    write_corpus(d / "unmapped_bench_sparse-1k.json.bz2", args.n_test_docs, sparse_line, random.Random(args.seed), "sparse-1k")
    write_corpus(d / "unmapped_bench_sparse.json.bz2", args.n_docs, sparse_line, random.Random(args.seed), "sparse-full")

    print("\n=== Summary ===")
    files = [
        "unmapped_bench_dense-1k.json.bz2",
        "unmapped_bench_dense.json.bz2",
        "unmapped_bench_sparse-1k.json.bz2",
        "unmapped_bench_sparse.json.bz2",
    ]
    for fname in files:
        path = d / fname
        size = path.stat().st_size
        print(f"  {fname:<45}  {size:>15,} bytes  ({size / 1024**2:7.1f} MB)")

    print(f"\nUpload the files in {d}/ to rally-tracks.elastic.co/esql_unmapped/")


if __name__ == "__main__":
    main()
