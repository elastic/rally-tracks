#!/usr/bin/env python3
"""
Compare two ground truth files to verify correctness.

Usage:
    python compare_ground_truth.py queries-recall-10m.json.bz2 queries-recall-10m-generated.json.bz2
"""

import bz2
import json
import sys


def load_ground_truth(path):
    opener = bz2.open if path.endswith(".bz2") else open
    queries = {}
    with opener(path, "r") as f:
        for line in f:
            q = json.loads(line)
            queries[q["query_id"]] = q
    return queries


def compare(path_a, path_b):
    print(f"A: {path_a}")
    print(f"B: {path_b}")
    print()

    a = load_ground_truth(path_a)
    b = load_ground_truth(path_b)

    print(f"Queries in A: {len(a)}")
    print(f"Queries in B: {len(b)}")

    if set(a.keys()) != set(b.keys()):
        print(f"MISMATCH: query IDs differ")
        print(f"  Only in A: {set(a.keys()) - set(b.keys())}")
        print(f"  Only in B: {set(b.keys()) - set(a.keys())}")
        return

    print(f"Query IDs match: YES")
    print()

    k_a = min(len(a[qid]["ids"]) for qid in a)
    k_b = min(len(b[qid]["ids"]) for qid in b)
    print(f"Top-K in A: {k_a}")
    print(f"Top-K in B: {k_b}")
    compare_k = min(k_a, k_b)
    print(f"Comparing top-{compare_k} per query")
    print()

    total_overlap = 0
    total_items = 0
    max_score_diff = 0.0
    worst_overlap_qid = None
    worst_overlap_val = compare_k + 1

    for qid in sorted(a.keys()):
        ids_a = a[qid]["ids"][:compare_k]
        ids_b = b[qid]["ids"][:compare_k]

        set_a = {doc_id for doc_id, _ in ids_a}
        set_b = {doc_id for doc_id, _ in ids_b}
        overlap = len(set_a & set_b)
        total_overlap += overlap
        total_items += compare_k

        if overlap < worst_overlap_val:
            worst_overlap_val = overlap
            worst_overlap_qid = qid

        score_map_a = {doc_id: score for doc_id, score in ids_a}
        score_map_b = {doc_id: score for doc_id, score in ids_b}
        for doc_id in set_a & set_b:
            diff = abs(score_map_a[doc_id] - score_map_b[doc_id])
            max_score_diff = max(max_score_diff, diff)

        if overlap < compare_k:
            only_a = set_a - set_b
            only_b = set_b - set_a
            # show score of the boundary docs for debugging
            rank_a = {doc_id: i for i, (doc_id, _) in enumerate(ids_a)}
            rank_b = {doc_id: i for i, (doc_id, _) in enumerate(ids_b)}
            print(f"  query {qid}: overlap {overlap}/{compare_k}")
            for doc_id in sorted(only_a):
                r = rank_a[doc_id]
                s = ids_a[r][1]
                print(f"    only in A: {doc_id}  rank={r}  score={s}")
            for doc_id in sorted(only_b):
                r = rank_b[doc_id]
                s = ids_b[r][1]
                print(f"    only in B: {doc_id}  rank={r}  score={s}")

    avg_overlap = total_overlap / len(a)
    print()
    print(f"Average overlap: {avg_overlap:.1f}/{compare_k} ({100*avg_overlap/compare_k:.2f}%)")
    print(f"Worst overlap:   {worst_overlap_val}/{compare_k} (query {worst_overlap_qid})")
    print(f"Max score diff on shared docs: {max_score_diff:.10f}")

    if avg_overlap == compare_k:
        print("\nPERFECT MATCH on doc IDs.")
    elif avg_overlap / compare_k > 0.99:
        print("\nNEAR MATCH — tiny differences likely from float precision in score ties.")
    else:
        print("\nSIGNIFICANT DIFFERENCES — investigate.")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <file_a> <file_b>")
        sys.exit(1)
    compare(sys.argv[1], sys.argv[2])
