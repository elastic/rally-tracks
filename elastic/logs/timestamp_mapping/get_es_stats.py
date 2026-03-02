import argparse
import json
import os
from elasticsearch import Elasticsearch

def get_es_client(host, port, user, password):
    """Establishes a connection to the Elasticsearch cluster."""
    try:
        es = Elasticsearch(
            hosts=[f"http://{host}:{port}"],
            basic_auth=(user, password),
            request_timeout=30
        )
        if not es.ping():
            raise ConnectionError("Could not connect to Elasticsearch.")
        return es
    except Exception as e:
        print(f"Error connecting to Elasticsearch: {e}")
        exit(1)

def save_to_json_file(data, filename):
    """Saves a Python dictionary to a specified JSON file."""
    output_dir = "out"
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)
    if os.path.exists(filepath):
        print(f"Error: Output file {filepath} already exists.")
        exit(1)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Saved report to {filepath}")

def get_disk_usage(es):
    """Retrieves disk usage statistics."""
    print("-> Fetching disk usage...")
    response = es.perform_request(
        method="POST",
        path="/_all/_disk_usage",
        params={"run_expensive_tasks": "true"}
    )
    return response.body

def get_index_counts(es):
    """Retrieves document counts per index."""
    print("-> Fetching index counts...")
    response = es.cat.indices(index="logs-*", h="index,docs.count")
    
    index_data = {}
    lines = response.strip().split('\n')
    for line in lines:
        parts = line.split()
        if len(parts) == 2:
            index_name, docs_count = parts
            index_data[index_name] = {"docs.count": int(docs_count)}
    return index_data

def get_unique_timestamps(es):
    """Retrieves unique timestamp counts per index."""
    print("-> Fetching unique timestamp counts per index...")
    body = {
        "size": 0,
        "aggs": {
            "indices_agg": {
                "terms": {
                    "field": "_index",
                    "size": 100
                },
                "aggs": {
                    "unique_timestamps": {
                        "cardinality": {
                            "field": "@timestamp"
                        }
                    }
                }
            }
        }
    }
    response = es.search(index=".ds-logs-*", body=body)
    
    unique_ts_data = {}
    for bucket in response['aggregations']['indices_agg']['buckets']:
        unique_ts_data[bucket['key']] = bucket['unique_timestamps']['value']
    return unique_ts_data

def main():
    """Main function to parse arguments and run the stat collection."""
    parser = argparse.ArgumentParser(description="Collect Elasticsearch stats into separate JSON files.")
    parser.add_argument("host", help="Elasticsearch host (e.g., localhost)")
    parser.add_argument("port", type=int, help="Elasticsearch port (e.g., 9200)")
    parser.add_argument("username", help="Username for authentication (e.g., elastic-admin)")
    parser.add_argument("password", help="Password for authentication")
    parser.add_argument("type", help="Type for the filename (e.g., prod, dev)")
    parser.add_argument("test_name", help="Test name for the filename (e.g., test_run_1)")
    args = parser.parse_args()

    file_prefix = f"{args.type}_{args.test_name}"

    es_client = get_es_client(args.host, args.port, args.username, args.password)

    # Fetch and save disk usage in its own file
    disk_usage_data = get_disk_usage(es_client)
    save_to_json_file(disk_usage_data, f"disk_usage_{file_prefix}.json")

    # Fetch and combine index-specific stats
    index_counts_data = get_index_counts(es_client)
    unique_timestamps_data = get_unique_timestamps(es_client)

    per_index_stats = {}
    all_indices = set(index_counts_data.keys()).union(set(unique_timestamps_data.keys()))
    
    for index_name in sorted(list(all_indices)):
        per_index_stats[index_name] = {
            "docs.count": index_counts_data.get(index_name, {}).get("docs.count", 0),
            "unique_timestamps": unique_timestamps_data.get(index_name, 0)
        }
    
    # Save combined index stats to its own file
    save_to_json_file(per_index_stats, f"index_stats_{file_prefix}.json")

if __name__ == "__main__":
    main()
