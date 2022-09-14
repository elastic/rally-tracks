#!/usr/bin/env python3

####################################################################
#
# A tool that dedupes a sorted anonymized metricbeat dump.
#
####################################################################
#
# Expects sorted anonymized metricbeat dump as input via standard
# in and returns a deduped sorted anonymized metric beat output via
# standard out. Also seperately generates 'dupes-' prefixed files
# per metric set name containing the dupes for manual inspection.
#
####################################################################

import json
import sys


def generate_event_key(parsed_line):
    return parsed_line["kubernetes"]["event"]["involved_object"]["uid"]


def generate_state_container_key(parsed_line):
    key = parsed_line["kubernetes"]["container"]["name"]
    key += parsed_line["kubernetes"]["pod"]["name"]
    key += parsed_line["kubernetes"]["node"]["name"]
    container_id = parsed_line.get("kubernetes", {}).get("container", {}).get("id")
    if container_id is not None:
        key += container_id
    return key


def generate_state_pod_key(parsed_line):
    return parsed_line["kubernetes"]["pod"]["name"] + generate_node_key(parsed_line)


def generate_container_key(parsed_line):
    return parsed_line["kubernetes"]["container"]["name"] + parsed_line["kubernetes"]["pod"]["name"] + generate_node_key(parsed_line)


def generate_volume_key(parsed_line):
    return parsed_line["kubernetes"]["volume"]["name"] + parsed_line["kubernetes"]["pod"]["name"] + generate_node_key(parsed_line)


def generate_pod_key(parsed_line):
    return parsed_line["kubernetes"]["pod"]["name"] + generate_node_key(parsed_line)


def generate_node_key(parsed_line):
    return parsed_line["kubernetes"]["node"]["name"]


def generate_system_key(parsed_line):
    return generate_node_key(parsed_line) + parsed_line["kubernetes"]["system"]["container"]


def generate_state_node_key(parsed_line):
    return generate_node_key(parsed_line)


generate_key_functions = {
    "event": generate_event_key,
    "state_container": generate_state_container_key,
    "state_pod": generate_state_pod_key,
    "container": generate_container_key,
    "volume": generate_volume_key,
    "pod": generate_pod_key,
    "node": generate_node_key,
    "system": generate_system_key,
    "state_node": generate_state_node_key,
}

in_count = 0
error_count = 0
out_count = 0
current_timestamp = None
keys = set()

dupe_files = {}

with open("error_lines.json", "a") as error_file:
    for line in sys.stdin:
        in_count += 1
        try:
            parsed = json.loads(line)
            line_timestamp = parsed["@timestamp"]
            metric_set_name = parsed["metricset"]["name"]
            if parsed.get("error") is not None:
                error_count += 1
                print(line, file=error_file)
                continue

            generate_key_function = generate_key_functions[metric_set_name]
            key = metric_set_name + generate_key_function(parsed)
            if current_timestamp == line_timestamp:
                if key in keys:
                    dupe_file_name = f"dupes-{metric_set_name}.json"
                    dupe_file = dupe_files.get(dupe_file_name)
                    if dupe_file is None:
                        dupe_file = open(dupe_file_name, "a")
                        dupe_files[dupe_file_name] = dupe_file

                    print(line, file=dupe_file)
                    continue
                else:
                    keys.add(key)
            else:
                current_timestamp = line_timestamp
                keys = set()
                keys.add(key)

            print(line, end="")
            out_count += 1
            if out_count % 100000 == 0:
                print(
                    f"in {in_count:012d} docs, out {out_count:012d} docs, errors {error_count:012d}",
                    file=sys.stderr,
                )
        except Exception as e:
            raise Exception(f"Error processing {line}") from e

    for dupe_file in dupe_files:
        dupe_files[dupe_file].close()
