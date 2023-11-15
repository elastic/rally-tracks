#!/usr/bin/env python3
import bz2
import json
import sys
import typing

import pyarrow as pa

BATCH_SIZE: int = 1000
QUERY_COLUMN: str = "embedding"
OUTPUT_FILENAME: str = "queries.json.bz2"


def output_queries(input_filename: str, queries_file: typing.TextIO):
    with pa.memory_map(input_filename, "rb") as source:
        query_table = pa.ipc.open_stream(source).read_all()
        for record_batch in query_table.to_batches(max_chunksize=BATCH_SIZE):
            query_list = record_batch.column(QUERY_COLUMN)
            for query in query_list:
                queries_file.write(json.dumps(query.as_py()))
                queries_file.write("\n")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: {} <input_file_path>".format(sys.argv[0]))
        exit(1)

    input_filename = sys.argv[1]

    with bz2.open(OUTPUT_FILENAME, "wt") as queries_file:
        output_queries(input_filename, queries_file)
