#!/usr/bin/env python3
import bz2
import json
import os
import sys

import pyarrow as pa

OUTPUT_DIR: str = "openai-documents"
INITIAL_INDEXING_DOCS_FILENAME: str = "open_ai_corpus-initial-indexing.json.bz2"
PARALLEL_INDEXING_DOCS_FILENAME: str = "open_ai_corpus-parallel-indexing.json.bz2"
DEFAULT_MAX_INITIAL_INDEXING_DOCS: int = -1
DEFAULT_MAX_PARALLEL_INDEXING_DOCS: int = 100_000
PROGRESS_EVERY = 100


def progress_bar(count, total):
    bar_length = 100
    filled_length = int(round(bar_length * count / float(total)))
    percentage = round(100.0 * count / float(total), 1)
    bar = "=" * filled_length + "-" * (bar_length - filled_length)
    sys.stdout.write("[{}] {}{} ... {:,}/{:,}\r".format(bar, percentage, "%", count, total))
    sys.stdout.flush()


def output_documents(input_file_path: str, max_initial_indexing_docs: int, max_parallel_indexing_docs: int):
    if max_parallel_indexing_docs < 0:
        raise ValueError("max_parallel_indexing_docs must be >= 0")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with pa.memory_map(input_file_path, "rb") as source:
        doc_table = pa.ipc.open_stream(source).read_all()

        if max_initial_indexing_docs < 0:
            # Create as many initial indexing docs as possible while still meeting parallel indexing docs requirements
            initial_indexing_docs = max(0, doc_table.num_rows - max_parallel_indexing_docs)
        else:
            initial_indexing_docs = min(doc_table.num_rows, max_initial_indexing_docs)

        parallel_indexing_docs = min(doc_table.num_rows - initial_indexing_docs, max_parallel_indexing_docs)

        parse_documents(doc_table, initial_indexing_docs, 0, INITIAL_INDEXING_DOCS_FILENAME)
        parse_documents(doc_table, parallel_indexing_docs, initial_indexing_docs, PARALLEL_INDEXING_DOCS_FILENAME)


def parse_documents(doc_table: pa.Table, doc_count: int, table_offset: int, output_filename: str):
    output_file_path = os.path.join(OUTPUT_DIR, output_filename)
    print(f"Writing {doc_count} documents to {output_file_path}")

    with bz2.open(output_file_path, "wt") as output_file:
        if doc_count <= 0:
            # Return here so we always create the output file
            return

        doc_table_sliced = doc_table.slice(offset=table_offset, length=doc_count)

        docs_written = 0
        progress_bar(docs_written, doc_count)

        for record_batch in doc_table_sliced.to_batches(max_chunksize=PROGRESS_EVERY):
            docid_col = record_batch.column("_id")
            title_col = record_batch.column("title")
            text_col = record_batch.column("text")
            emb_col = record_batch.column("embedding")
            for docid, title, text, emb in zip(docid_col, title_col, text_col, emb_col):
                output_file.write(
                    json.dumps(
                        {"docid": docid.as_py(), "title": title.as_py(), "text": text.as_py(), "emb": emb.as_py()}, ensure_ascii=True
                    )
                )
                output_file.write("\n")

            docs_written += record_batch.num_rows
            progress_bar(docs_written, doc_count)

    # Print newline so that progress bar is not overwritten by next print statement
    print()


def parse_arguments():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <input_file_path> [<max_initial_indexing_docs> <max_parallel_indexing_docs>]")
        exit(1)

    if len(sys.argv) == 2:
        return (sys.argv[1], DEFAULT_MAX_INITIAL_INDEXING_DOCS, DEFAULT_MAX_PARALLEL_INDEXING_DOCS)
    elif len(sys.argv) == 3:
        return (sys.argv[1], int(sys.argv[2]), DEFAULT_MAX_PARALLEL_INDEXING_DOCS)
    elif len(sys.argv) >= 4:
        return (sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))


if __name__ == "__main__":
    input_file_path, max_initial_indexing_docs, max_parallel_indexing_docs = parse_arguments()
    output_documents(input_file_path, max_initial_indexing_docs, max_parallel_indexing_docs)
