import asyncio

from elasticsearch import BadRequestError, NotFoundError


class ParamSource:
    def __init__(self, track, params):
        # choose a suitable index: if there is only one defined for this track
        # choose that one, but let the user always override index
        if len(track.indices) == 1:
            default_index = track.indices[0].name
        else:
            default_index = "_all"

        self._index_name = params.get("index", default_index)
        self._cache = params.get("cache", False)
        self._size = params.get("size", 10)
        self._field = params.get("field", "ml.tokens")
        self._num_terms = params.get("num-terms", 10)
        self._track_total_hits = params.get("track_total_hits", False)
        self._params = params


async def get_xpack_capabilities(es):
    print()
    print("=" * 50)
    print(await es.perform_request(method="GET", path="/_xpack"))
    print("=" * 50)


elser_v1_model_id = ".elser_model_1"
elser_v2_model_id = ".elser_model_2"
elser_v2_platform_specific_model_id = ".elser_model_2_linux-x86_64"


# TODO enable this function once rally upgrades the elasticsearch python client to >=8.9.0
# async def put_elser(es, params):
#     try:
#         await es.ml.put_trained_model(model_id=elser_v1_model_id, input={"field_names": "text_field"})
#         return True
#     except BadRequestError as bre:
#         if (
#             bre.body["error"]["root_cause"][0]["reason"]
#             == f"Cannot create model [{model_id}] the id is the same as an current model deployment"
#             or bre.body["error"]["root_cause"][0]["reason"]
#             == f"Trained machine learning model [{model_id}] already exists"
#         ):
#             return True
#         else:
#             print(bre)
#             return False
#     except Exception as e:
#         print(e)
#         return False


async def put_elser(es, params):
    model_id = params["model_id"]

    try:
        await es.perform_request(method="PUT", path=f"/_ml/trained_models/{model_id}",
                                 body={"input": {"field_names": ["text_field"]}})
        return True
    except BadRequestError as bre:
        try:
            if (model_already_downloaded(bre, model_id)):
                return True
            else:
                print(bre)
                return False
        except Exception as e:
            print(e)
            return False
    except Exception as e:
        print(e)
        return False


async def delete_elser(es, params):
    model_id = params["model_id"]

    try:
        await es.perform_request(method="DELETE", path=f"/_ml/trained_models/{model_id}", params={"force": "true"})
        return True
    except BadRequestError as bre:
        try:
            if (model_already_downloaded(bre, model_id)):
                return True
            else:
                print(bre)
                return False
        except Exception as e:
            print(e)
            return False
    except Exception as e:
        print(e)
        return False


async def poll_for_elser_completion(es, params):
    model_id = params["model_id"]
    try_count = 0
    max_wait_time_seconds = 120
    wait_time_per_cycle_seconds = 5
    while wait_time_per_cycle_seconds * try_count < max_wait_time_seconds:
        try:
            response = await es.ml.get_trained_models(model_id=model_id, include="definition_status")
            if is_model_fully_defined(response):
                return True
        except NotFoundError:
            print("\nwaiting... try count:", try_count, end="")
            await asyncio.sleep(wait_time_per_cycle_seconds)
            try_count += 1
    print()
    return False


def is_model_fully_defined(response):
    return response["trained_model_configs"][0]["fully_defined"]


async def stop_trained_model_deployment(es, params):
    model_id = params["model_id"]
    try:
        await es.ml.stop_trained_model_deployment(model_id=model_id, force=True)
        return True
    except BadRequestError as bre:
        try:
            if model_deployment_already_exists(bre, model_id):
                return True
            else:
                print(bre)
                return False
        except Exception as e:
            print(e)
            return False


async def start_trained_model_deployment(es, params):
    number_of_allocations = params["number_of_allocations"]
    threads_per_allocation = params["threads_per_allocation"]
    queue_capacity = params["queue_capacity"]
    model_id = params["model_id"]
    try:
        await es.ml.start_trained_model_deployment(
            model_id=model_id,
            wait_for="fully_allocated",
            number_of_allocations=number_of_allocations,
            threads_per_allocation=threads_per_allocation,
            queue_capacity=queue_capacity,
            cache_size="0b",
        )
        return True
    except BadRequestError as bre:
        try:
            if model_deployment_already_exists(bre, model_id):
                return True
            else:
                print(bre)
                return False
        except Exception as e:
            print(e)
            return False
    except Exception as e:
        print("Exception", e)
        return False


def model_deployment_already_exists(bad_request_error, model_id):
    try:

        return (bad_request_error.body["error"]["root_cause"][0]["reason"]
            == f"Could not start model deployment because an existing deployment with the same id [{model_id}] exist")

    except Exception as e:
        print(e)
        return False


def model_already_downloaded(bre, model_id):
    try:
        return (
            bre.body["error"]["root_cause"][0]["reason"]
            == f"Cannot create model [{model_id}] the id is the same as an current model deployment"
            or bre.body["error"]["root_cause"][0]["reason"]
            == f"Trained machine learning model [{model_id}] already exists")

    except Exception as e:
        print(e)
        return False

async def create_elser_model(es, params):
    await get_xpack_capabilities(es)
    if await put_elser(es, params) == False:
        return False
    if await poll_for_elser_completion(es, params) == False:
        return False

    return True


def register(registry):
    registry.register_param_source("param-source", ParamSource)
    registry.register_runner("put-elser", create_elser_model, async_runner=True)
    registry.register_runner("delete-elser", delete_elser, async_runner=True)
    registry.register_runner("stop-trained-model-deployment", stop_trained_model_deployment, async_runner=True)
    registry.register_runner("start-trained-model-deployment", start_trained_model_deployment, async_runner=True)
