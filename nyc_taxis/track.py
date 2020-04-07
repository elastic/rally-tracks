import asyncio
import time


def wait_for_ml_lookback(es, params):
    while True:
        response = es.transport.perform_request("GET", "/_xpack/ml/datafeeds/%s/_stats" % params["datafeed-id"])
        if response["datafeeds"][0]["state"] == "stopped":
            break
        time.sleep(5)


async def wait_for_ml_lookback_async(es, params):
    while True:
        response = await es.transport.perform_request("GET", "/_xpack/ml/datafeeds/%s/_stats" % params["datafeed-id"])
        if response["datafeeds"][0]["state"] == "stopped":
            break
        await asyncio.sleep(5)


def register(registry):
    async_runner = registry.meta_data.get("async_runner", False)
    if async_runner:
        registry.register_runner("wait-for-ml-lookback", wait_for_ml_lookback_async, async_runner=True)
    else:
        registry.register_runner("wait-for-ml-lookback", wait_for_ml_lookback)
