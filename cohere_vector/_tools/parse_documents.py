import json
import sys

import numpy as np
from datasets import load_dataset

DATASET_NAME: str = f"Cohere/miracl-en-corpus-22-12"
OUTPUT_FILENAME: str = "cohere-documents.json"
DEFAULT_MAX_DOCS = -1
TOTAL_DOCS = 32893221
PROGRESS_EVERY = 100


def progress_bar(count, total):
    bar_length = 100
    filled_length = int(round(bar_length * count / float(total)))
    percentage = round(100.0 * count / float(total), 1)
    bar = "=" * filled_length + "-" * (bar_length - filled_length)
    sys.stdout.write("[{}] {}{} ... {:,}/{:,}\r".format(bar, percentage, "%", count, total))
    sys.stdout.flush()


def output_documents(docs_file):
    max_documents = int(sys.argv[1]) if len(sys.argv) >= 2 else DEFAULT_MAX_DOCS
    partial_index = max_documents != DEFAULT_MAX_DOCS

    if partial_index:
        print("Parsing {} documents".format(max_documents))
    else:
        print("Parsing entire {} dataset".format(DATASET_NAME))
    docs = load_dataset(DATASET_NAME, split="train")
    doc_count = 0
    progress_bar(doc_count, max_documents if partial_index else TOTAL_DOCS)
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
            progress_bar(doc_count, max_documents if partial_index else TOTAL_DOCS)

        if partial_index and doc_count >= max_documents:
            return


if __name__ == "__main__":
    print("Outputing documents to {}".format(OUTPUT_FILENAME))
    with open(OUTPUT_FILENAME, "w") as documents_file:
        output_documents(documents_file)
