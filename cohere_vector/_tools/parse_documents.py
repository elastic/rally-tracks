import json
import sys

import numpy as np
from datasets import DownloadMode, load_dataset

DATASET_NAME: str = f"Cohere/miracl-en-corpus-22-12"
DATASET_DL_PROCS: int = 6
OUTPUT_FILENAME: str = "cohere-documents"
DEFAULT_MAX_DOCS = -1
TOTAL_DOCS = 32893221
MAX_DOCS_PER_FILE = 3_000_000
TOTAL_PAGES = 11
PROGRESS_EVERY = 100


def progress_bar(count, total):
    bar_length = 100
    filled_length = int(round(bar_length * count / float(total)))
    percentage = round(100.0 * count / float(total), 1)
    bar = "=" * filled_length + "-" * (bar_length - filled_length)
    sys.stdout.write("[{}] {}{} ... {:,}/{:,}\r".format(bar, percentage, "%", count, total))
    sys.stdout.flush()


def output_pages(start_page, end_page):
    for page in range(start_page, end_page + 1):
        start_index = (page - 1) * MAX_DOCS_PER_FILE
        end_index = start_index + MAX_DOCS_PER_FILE
        if end_index > TOTAL_DOCS:
            end_index = TOTAL_DOCS
        output_filename = f"{OUTPUT_FILENAME}-{page:02d}.json"
        print(f"Outputing page {page} documents to {output_filename}")
        with open(output_filename, "w") as documents_file:
            output_documents(documents_file, start_index, end_index)


def output_documents(docs_file, start_index, end_index):
    doc_count = 0
    dataset_size = end_index - start_index
    print(f"Parsing {dataset_size} documents from {DATASET_NAME} [{start_index}:{end_index}]")
    docs = load_dataset(
        DATASET_NAME,
        split=f"train[{start_index}:{end_index}]",
        num_proc=DATASET_DL_PROCS,
        download_mode=DownloadMode.REUSE_DATASET_IF_EXISTS,
    )

    progress_bar(doc_count, dataset_size)
    for doc in docs:
        v = np.array(doc["emb"])
        v_unit = v / np.linalg.norm(v)
        docs_file.write(
            json.dumps(
                {
                    "docid": doc["docid"],
                    "title": doc["title"],
                    "text": doc["text"],
                    "emb": v_unit.tolist(),
                },
                ensure_ascii=True,
            )
        )
        docs_file.write("\n")
        doc_count += 1
        if doc_count % PROGRESS_EVERY == 0:
            progress_bar(doc_count, dataset_size)
    print(f"Wrote {doc_count} documents to output file.")


def parse_arguments():
    if len(sys.argv) >= 3:
        return (DEFAULT_MAX_DOCS, int(sys.argv[1]), int(sys.argv[2]))

    if len(sys.argv) >= 2:
        return (int(sys.argv[1]), 1, TOTAL_PAGES)
    return (DEFAULT_MAX_DOCS, 1, TOTAL_PAGES)


if __name__ == "__main__":
    (max_documents, start_page, end_page) = parse_arguments()
    if max_documents == DEFAULT_MAX_DOCS:
        output_pages(start_page, end_page)
    else:
        print("Outputing documents to {}.json".format(OUTPUT_FILENAME))
        with open(f"{OUTPUT_FILENAME}.json", "w") as documents_file:
            output_documents(documents_file, 0, max_documents)
