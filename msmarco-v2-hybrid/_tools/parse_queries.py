import argparse
import asyncio
import json
import sys
from os import environ

import ir_datasets
import numpy
import vg
from cohere import AsyncClient
from elasticsearch import AsyncElasticsearch

DATASET_NAME: str = "msmarco-passage-v2/train"
RECALL_DATASET_NAME: str = "msmarco-passage-v2/trec-dl-2022/judged"
OUTPUT_FILENAME: str = "queries.json"
OUTPUT_RECALL_FILENAME: str = "queries-recall.json"
MAX_DOCS: int = 12_000
REQUEST_TIMEOUT: int = 60 * 60 * 5


def get_brute_force_query(emb):
    return {
        "script_score": {
            "query": {"match_all": {}},
            "script": {
                "source": "double value = dotProduct(params.query_vector, 'emb'); return sigmoid(1, Math.E, -value);",
                "params": {"query_vector": emb},
            },
        }
    }


async def retrieve_embed_for_query(co, text):
    response = await co.embed(texts=[text], model="embed-english-v3.0", input_type="search_query")
    return vg.normalize(numpy.array(response.embeddings[0])).tolist()


async def output_queries(queries_file):
    output = []
    dataset = ir_datasets.load(DATASET_NAME)

    # Get your production Cohere API key from https://dashboard.cohere.com/api-keys
    async with AsyncClient(environ["COHERE_API_KEY"]) as co:
        co_queries = []
        for query in dataset.queries_iter():
            co_queries.append(query.text)

            # Run our async requests every 100 queries *or* as soon as we
            # have enough to fill our output list
            output_left = MAX_DOCS - len(output)
            if len(co_queries) in (100, output_left):
                cos = (retrieve_embed_for_query(co, q) for q in co_queries)
                co_queries = []
                output += [v for v in await asyncio.gather(*cos) if not isinstance(v, Exception)]

            if len(output) == MAX_DOCS:
                break

    queries_file.write("\n".join(json.dumps(embed) for embed in output))


async def output_recall_queries(queries_file):
    async with AsyncElasticsearch(
        "https://localhost:19200/", basic_auth=("esbench", "super-secret-password"), verify_certs=False, request_timeout=REQUEST_TIMEOUT
    ) as es:
        dataset = ir_datasets.load("msmarco-passage-v2/trec-dl-2022/judged")
        async with AsyncClient(environ["COHERE_API_KEY"]) as co:
            count = 0
            for query in dataset.queries_iter():
                emb = await retrieve_embed_for_query(co, query[1])
                resp = await es.search(
                    index="msmarco-v2", query=get_brute_force_query(emb), size=1000, _source=["_none_"], fields=["docid"]
                )
                ids = [(hit["fields"]["docid"][0], hit["_score"]) for hit in resp["hits"]["hits"]]
                line = {"query_id": query[0], "text": query[1], "emb": emb, "ids": ids}
                queries_file.write(json.dumps(line) + "\n")
                count += 1


async def create_queries():
    with open(OUTPUT_FILENAME, "w") as queries_file:
        await output_queries(queries_file)


async def create_recall_queries():
    with open(OUTPUT_RECALL_FILENAME, "w") as queries_file:
        await output_recall_queries(queries_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create queries for throughput or recall operations")
    parser.add_argument("-t", "--throughput", help="Create queries for throughput operations", action="store_true")
    parser.add_argument("-r", "--recall", help="Create queries for recall operations", action="store_true")

    if len(sys.argv) == 1:
        # Neither -t or -r was called, show the options
        parser.print_help(sys.stderr)
    args = parser.parse_args()
    loop = asyncio.get_event_loop()
    if args.throughput:
        loop.run_until_complete(create_queries())
    if args.recall:
        loop.run_until_complete(create_recall_queries())
