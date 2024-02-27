import json
from os import environ

import cohere
from datasets import load_dataset

DATASET_NAME: str = 'Cohere/msmarco-v2-embed-english-v3'
DATASET_SPLIT: str = 'train'
OUTPUT_FILENAME: str = 'queries.json'
MAX_DOCS = 20_000

# Get your production Cohere API key from https://dashboard.cohere.com/api-keys
co = cohere.Client(environ['COHERE_API_KEY'])

def output_queries(queries_file):
    queries = load_dataset(DATASET_NAME, split=DATASET_SPLIT, streaming=True)

    queries_count = 0
    for query in queries:
        if queries_count > MAX_DOCS:
            break

        response = co.embed(texts=[query['text']], model='embed-english-v3.0',
                            input_type='search_query')
        queries_file.write(json.dumps(response.embeddings ))
        queries_file.write("\n")
        queries_count += 1


if __name__ == '__main__':
    with open(OUTPUT_FILENAME, 'w') as queries_file:
        output_queries(queries_file)
