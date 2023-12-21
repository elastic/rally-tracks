import json

from datasets import load_dataset

DATASET_NAME: str = f"Cohere/miracl-en-queries-22-12"
DATASET_SPLIT: str = "train"
OUTPUT_FILENAME: str = "queries.json"


def output_queries(queries_file):
    queries = load_dataset(DATASET_NAME, split=DATASET_SPLIT)
    for query in queries:
        queries_file.write(json.dumps(query["emb"]))
        queries_file.write("\n")


if __name__ == "__main__":
    with open(OUTPUT_FILENAME, "w") as queries_file:
        output_queries(queries_file)
