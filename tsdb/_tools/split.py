#!/usr/bin/env python3

# Split a documents.json files in X parts
# https://github.com/elastic/rally/issues/1650#issuecomment-1378344368

import contextlib
import sys

path = sys.argv[1]
# This is the number of documents in the default corpus
TOTAL_DOCS = 116633698
n_splits = int(sys.argv[2])
q, r = divmod(total_docs, n_splits)
wanted_docs = q * n_splits


with contextlib.ExitStack() as stack, open(path, "r") as f:
    full_filenames = [f"documents-split-{i}.json" for i in range(n_splits)]
    full_output_files = [stack.enter_context(open(fname, "w")) for fname in full_filenames]

    for i, line in enumerate(f):
        if i % 1_000_000 == 0:
            print(i)

        full_output_files[i % n_splits].write(line)

        if i + 1 == wanted_docs:
            break
