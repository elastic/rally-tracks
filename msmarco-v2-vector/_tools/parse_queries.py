import asyncio
import json
from os import environ

import ir_datasets
import numpy
import vg
from cohere import AsyncClient

DATASET_NAME: str = "msmarco-passage-v2/train"
OUTPUT_FILENAME: str = "queries.json"
MAX_DOCS = 12_000


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
            print(query)
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


async def main():
    with open(OUTPUT_FILENAME, "w") as queries_file:
        await output_queries(queries_file)


if __name__ == "__main__":
    asyncio.run(main())
