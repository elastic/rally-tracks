#!/usr/bin/env python3

import json
import random
import struct
import sys
import uuid

# Constants used in event randomization
num_sessions = 1000000
num_paths = 50000
num_query_params = 1000
num_queries = 10000
num_docs = 50000
num_index = 3
num_queries = 20000
num_search_apps = 2
num_result = 10
search_ratio = 30


# Function used to generate random events parts.
def random_identifier():
    return str(uuid.uuid4())


random_paths = list(map(lambda _: random_identifier(), range(1, num_paths)))
random_query_params = list(map(lambda _: random_identifier(), range(1, num_query_params)))
random_titles = list(map(lambda _: random_identifier(), range(1, num_paths)))
random_docs = list(map(lambda _: random_identifier(), range(1, num_docs)))
random_indices = list(map(lambda i: "index-%sd" % (i), range(1, num_index)))
random_search_applications = list(map(lambda i: "index-%sd" % (i), range(1, num_search_apps)))
random_queries = list(map(lambda _: random_identifier(), range(1, num_queries)))


def random_url():
    return "http://elastic.co/%s?%s" % (random.choice(random_paths), random.choice(random_query_params))


def base_event_payload(session_id, user_id):
    return {"session": {"id": session_id}, "user": {"id": user_id}}


def random_page_view_event(session_id, user_id):
    return {
        "event_type": "page_view",
        "payload": {
            **base_event_payload(session_id, user_id),
            **{
                "page": {"url": random_url(), "title": random.choice(random_titles), "referrer": random_url()},
                "document": {"id": random.choice(random_docs), "index": random.choice(random_indices)},
            },
        },
    }


def random_search_event(session_id, user_id):
    return {
        "event_type": "search",
        "payload": {
            **base_event_payload(session_id, user_id),
            **{
                "search": {
                    "query": random.choice(random_queries),
                    "search_application": random.choice(random_search_applications),
                    "page": {"current": random.randint(1, 100), "size": random.choice([10, 20, 50])},
                    "sort": {"name": random.choice(["relevance", "name", "price"]), "direction": random.choice(["asc", "desc"])},
                    "results": {
                        "total_results": random.randint(1, 10000),
                        "items": list(
                            map(
                                lambda _: {
                                    "page": {"url": random_url()},
                                    "document": {"id": random.choice(random_docs), "index": random.choice(random_indices)},
                                },
                                range(num_result),
                            )
                        ),
                    },
                }
            },
        },
    }


def random_event(session_id, user_id):
    if random.randint(1, 100) < search_ratio:
        return random_search_event(session_id, user_id)
    return random_page_view_event(session_id, user_id)


try:
    from tqdm import tqdm

    iterate = lambda i: tqdm(range(i))
except ModuleNotFoundError:
    print("Warning: [tqdm] package is not available and you won't be able to see progress.", file=sys.stderr)
    iterate = range

for _ in iterate(num_sessions):
    session_id = random_identifier()
    user_id = random_identifier()
    for i in range(1, random.randint(1, 50)):
        print(json.dumps(random_event(session_id, user_id), ensure_ascii=False))
