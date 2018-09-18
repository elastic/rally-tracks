import time


def wait_for_ml_lookback(es, params):
    while True:
        response = es.xpack.ml.get_datafeed_stats(datafeed_id=params["datafeed-id"])
        if response["datafeeds"][0]["state"] == "stopped":
            break
        time.sleep(5)


def register(registry):
    registry.register_runner("wait-for-ml-lookback", wait_for_ml_lookback)
