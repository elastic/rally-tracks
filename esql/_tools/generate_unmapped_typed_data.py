#!/usr/bin/env python3
"""
Generate the corpus file for the ES|QL unmapped PUNK probes.

PotentiallyUnmappedSingleTypeEsField (PUNK) applies to a field that is mapped to
exactly one non-keyword type in some indices and unmapped in others. This script
generates the corpus feeding both legs of that scenario:

  unmapped_bench_typed_mapped      fields mapped to their real type (long/double/
                                    boolean/ip/date); ES coerces the string value at
                                    index time
  unmapped_bench_typed_no_mapping  dynamic: false; the same string sits untouched in
                                    _source and gets auto-cast on `SET unmapped_fields
                                    ="load"`

Outputs two bz2-compressed NDJSON files in --output-dir:
  unmapped_bench_typed.json.bz2       100k docs
  unmapped_bench_typed-1k.json.bz2    first 1,000 docs (Rally --test-mode)
"""

import argparse
import bz2
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

N_DOCS_FULL = 100_000
N_DOCS_TEST = 1_000

DEFAULT_SEED = 42
GCP_CORPUS_URI = "gs://rally-tracks/esql_unmapped"
PUBLIC_CORPUS_URL = "https://rally-tracks.elastic.co/esql_unmapped"

BASE_TS = datetime(2024, 1, 1, tzinfo=timezone.utc)
TS_RANGE_SECONDS = 365 * 24 * 3600


def _ts(rng: random.Random) -> str:
    offset = rng.randint(0, TS_RANGE_SECONDS)
    return (BASE_TS + timedelta(seconds=offset)).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def _ip(rng: random.Random) -> str:
    return ".".join(str(rng.randint(0, 255)) for _ in range(4))


def typed_line(doc_id: int, rng: random.Random) -> str:
    """One NDJSON line with a string-encoded value for each PUNK-probed type."""
    ts = _ts(rng)
    typed_long = rng.randint(0, 1_000_000)
    typed_double = round(rng.uniform(0, 1_000_000), 3)
    typed_boolean = "true" if rng.random() < 0.5 else "false"
    typed_ip = _ip(rng)
    typed_datetime = _ts(rng)
    return (
        f'{{"@timestamp":"{ts}","id":{doc_id},'
        f'"typed_long":"{typed_long}",'
        f'"typed_double":"{typed_double}",'
        f'"typed_boolean":"{typed_boolean}",'
        f'"typed_ip":"{typed_ip}",'
        f'"typed_datetime":"{typed_datetime}"}}'
    )


def write_corpus(path: Path, n_docs: int, rng: random.Random, label: str) -> None:
    print(f"  [{label}] writing {n_docs:,} docs -> {path}", flush=True)
    with bz2.open(path, "wt", encoding="utf-8") as fh:
        for doc_id in range(n_docs):
            fh.write(typed_line(doc_id, rng))
            fh.write("\n")
    size = path.stat().st_size
    print(f"    done  {size:,} bytes  ({size / 1024 ** 2:.1f} MB)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--output-dir", required=True, help="Directory to write corpus files into.")
    ap.add_argument("--n-docs", type=int, default=N_DOCS_FULL, help=f"Documents in the full corpus file (default {N_DOCS_FULL:,})")
    ap.add_argument("--n-test-docs", type=int, default=N_DOCS_TEST, help=f"Documents in the test-mode (-1k) file (default {N_DOCS_TEST:,})")
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED, help=f"Random seed for reproducibility (default {DEFAULT_SEED})")
    args = ap.parse_args()

    d = Path(args.output_dir)
    d.mkdir(parents=True, exist_ok=True)

    print("\n=== Typed-fields corpus (PUNK single-type probes) ===")
    # Test-mode file first; full file uses the same seed so docs 0..N_TEST-1 match.
    write_corpus(d / "unmapped_bench_typed-1k.json.bz2", args.n_test_docs, random.Random(args.seed), "typed-1k")
    write_corpus(d / "unmapped_bench_typed.json.bz2", args.n_docs, random.Random(args.seed), "typed-full")

    print("\n=== Summary ===")
    for fname in ["unmapped_bench_typed-1k.json.bz2", "unmapped_bench_typed.json.bz2"]:
        path = d / fname
        size = path.stat().st_size
        print(f"  {fname:<35}  {size:>12,} bytes  ({size / 1024**2:7.1f} MB)")

    print(f"\nUpload the files in {d}/ with the GCP track data upload process:")
    print(f"  {GCP_CORPUS_URI}/")
    print(f"Rally downloads them from {PUBLIC_CORPUS_URL}/")


if __name__ == "__main__":
    main()
