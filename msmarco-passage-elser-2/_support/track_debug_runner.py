import asyncio

from elasticsearch import AsyncElasticsearch
from track import poll_for_elser_completion, start_trained_model_deployment

CLOUD_ID = "elser-benchmark:dXMtY2VudHJhbDEuZ2NwLmNsb3VkLmVzLmlvOjQ0MyQzYjY4NTVjNTFjODk0OGJkOTAzY2ZhYzg0ZjAzZTY0MiQxNWViZmZkZjU4NGI0YmI1OTY4OWRmMjk4MDNlODljYg=="

ELASTIC_PASSWORD = "ELs0PCTul1bJoH7k1AqSPVpC"

es = AsyncElasticsearch(
    cloud_id=CLOUD_ID,
    basic_auth=("elastic", ELASTIC_PASSWORD))

async def debug_runner():
    params = {"id":CLOUD_ID, "pass":ELASTIC_PASSWORD}
    # print(await poll_for_elser_completion(es, params))
    print(await start_trained_model_deployment(es, params))

asyncio.run(debug_runner())

