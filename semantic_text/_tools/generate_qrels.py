"""
Generate a TREC-style qrels TSV (no header) from a HuggingFace dataset.

Output: TSV with columns: query_id, corpus_id, score
"""

import argparse
import csv
import os
import sys

from datasets import load_dataset
from tqdm import tqdm


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a qrels TSV from a HuggingFace dataset."
    )
    parser.add_argument("--dataset", required=True, help="HuggingFace dataset name")
    parser.add_argument(
        "--subset",
        default=None,
        help="Dataset subset/config name (default: qrels). Omit for datasets without subsets.",
    )
    parser.add_argument(
        "--split",
        default="train",
        help="Dataset split (default: train)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output TSV file path (default: /tmp/{dataset}-qrels.tsv)",
    )
    parser.add_argument(
        "--query-id-field",
        default="query-id",
        help="Dataset field for query ID (default: query-id)",
    )
    parser.add_argument(
        "--corpus-id-field",
        default="corpus-id",
        help="Dataset field for corpus ID (default: corpus-id)",
    )
    parser.add_argument(
        "--score-field",
        default="score",
        help="Dataset field for relevance score (default: score)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    dataset_name = args.dataset
    subset = args.subset
    split = args.split
    output = args.output or f"/tmp/{dataset_name.replace('/', '-')}-qrels.tsv"
    query_id_field = args.query_id_field
    corpus_id_field = args.corpus_id_field
    score_field = args.score_field

    os.makedirs(os.path.dirname(output) or ".", exist_ok=True)

    print(f"Loading {dataset_name} (subset={subset or 'none'}, split={split}, streaming)...")
    load_args = [dataset_name]
    if subset:
        load_args.append(subset)
    qrels = load_dataset(*load_args, split=split, streaming=True)

    total = 0
    with open(output, "w", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        for row in tqdm(qrels, desc="Writing qrels"):
            writer.writerow([
                str(row[query_id_field]),
                str(row[corpus_id_field]),
                row[score_field],
            ])
            total += 1

    print(f"Wrote {total:,} qrel rows to {output}")


if __name__ == "__main__":
    main()
