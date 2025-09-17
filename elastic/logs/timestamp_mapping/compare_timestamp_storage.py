import json
import sys
import os
from collections import defaultdict

def read_index_stats(file_path):
    """
    Reads a JSON file with index stats and returns a dictionary of doc counts and unique timestamps.
    """
    stats_data = {}
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            for index_name_long, stats in data.items():
                # Remove the date and suffix from the index name
                index_name = "-".join(index_name_long.split('-')[:-2])
                doc_count = stats.get('docs.count', 0)
                unique_timestamps = stats.get('unique_timestamps', 0)
                stats_data[index_name] = {'docs.count': doc_count, 'unique_timestamps': unique_timestamps}
    except FileNotFoundError:
        print(f"Warning: Stats file not found at {file_path}. Stats will be 0.")
    except json.JSONDecodeError:
        print(f"Warning: Could not decode JSON from {file_path}. Stats will be 0.")
    return stats_data

def extract_timestamp_data(json_data):
    """
    Extracts non-zero @timestamp field data for each index from the JSON.
    """
    extracted_data = defaultdict(dict)
    for index_name_long, index_data in json_data.items():
        if not index_name_long.startswith('_'):  # Skip non-index fields like '_shards'
            index_name = "-".join(index_name_long.split('-')[:-2])
            timestamp_data = index_data.get('fields', {}).get('@timestamp', {})
            if timestamp_data:
                for key, value in timestamp_data.items():
                    if isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                            if isinstance(sub_value, int) and sub_value > 0:
                                extracted_data[index_name][f"{key}.{sub_key}"] = sub_value
                    elif isinstance(value, int) and value > 0:
                        extracted_data[index_name][key] = value
    return extracted_data

def compare_data(data1, data2, counts1, counts2):
    """
    Compares the extracted data from two files and returns a comparison table,
    including document counts and overhead.
    """
    comparison = {}
    all_indices = set(data1.keys()) | set(data2.keys())
    all_metrics = set()
    for index in all_indices:
        all_metrics.update(data1.get(index, {}).keys())
        all_metrics.update(data2.get(index, {}).keys())

    for index in sorted(all_indices):
        comparison[index] = {}
        doc_count_date = counts1.get(index, {}).get('docs.count', 0)
        doc_count_date_nanos = counts2.get(index, {}).get('docs.count', 0)
        comparison[index]['docs.count'] = (doc_count_date, doc_count_date_nanos)

        unique_ts_date = counts1.get(index, {}).get('unique_timestamps', 0)
        unique_ts_date_nanos = counts2.get(index, {}).get('unique_timestamps', 0)
        comparison[index]['unique_timestamps'] = (unique_ts_date, unique_ts_date_nanos)

        for metric in sorted(all_metrics):
            val_date = data1.get(index, {}).get(metric, 0)
            val_date_nanos = data2.get(index, {}).get(metric, 0)

            comparison[index][metric] = {
                'date_val': val_date,
                'date_nanos_val': val_date_nanos,
                'overhead_per_doc': 0.0
            }

            if doc_count_date_nanos > 0:
                overhead = (val_date_nanos - val_date) / doc_count_date_nanos
                comparison[index][metric]['overhead_per_doc'] = overhead

    return comparison

def print_markdown_table(comparison, file1_label, file2_label):
    """
    Prints a Markdown table of the comparison data with dynamic headers and overhead.
    """
    if not comparison:
        print("No data to compare.")
        return

    all_metrics = sorted([m for m in list(comparison.values())[0].keys() if m not in ['docs.count', 'unique_timestamps']])

    header = [
        "Index",
        f"docs.count ({file1_label})",
        f"docs.count ({file2_label})",
        f"unique_timestamps ({file1_label})",
        f"unique_timestamps ({file2_label})"
    ]
    for metric in all_metrics:
        header.append(f"{metric} ({file1_label})")
        header.append(f"{metric} ({file2_label})")
        header.append(f"Overhead (+/-byte/doc)")

    print("| " + " | ".join(header) + " |")
    print("| " + "--- |" * len(header))

    for index, metrics in comparison.items():
        row = [index]
        doc_count_date, doc_count_date_nanos = metrics['docs.count']
        row.append(str(doc_count_date))
        row.append(str(doc_count_date_nanos))

        unique_ts_date, unique_ts_date_nanos = metrics['unique_timestamps']
        row.append(str(unique_ts_date))
        row.append(str(unique_ts_date_nanos))

        for metric in all_metrics:
            vals = metrics.get(metric, {})
            row.append(str(vals.get('date_val', 0)))
            row.append(str(vals.get('date_nanos_val', 0)))

            overhead = vals.get('overhead_per_doc', 0.0)
            sign = "+" if overhead >= 0 else "-"
            formatted_overhead = f"{sign}{abs(overhead):.4f}"
            row.append(formatted_overhead)

        print("| " + " | ".join(row) + " |")

def find_file(file_path):
    """
    Checks for the file locally first, then looks for the full path.
    Returns the resolved file path or None if not found.
    """
    local_path = os.path.join(os.getcwd(), file_path)
    if os.path.exists(local_path):
        return local_path

    if os.path.exists(file_path):
        return file_path

    return None

def main(test_name):
    """
    Main function to read, process, and compare the JSON files based on a test name.
    """
    file1_arg_json = os.path.join("out", f"disk_usage_date_{test_name}.json")
    file2_arg_json = os.path.join("out", f"disk_usage_date_nanos_{test_name}.json")
    file1_arg_stats = os.path.join("out", f"index_stats_date_{test_name}.json")
    file2_arg_stats = os.path.join("out", f"index_stats_date_nanos_{test_name}.json")

    resolved_file1_json = find_file(file1_arg_json)
    resolved_file2_json = find_file(file2_arg_json)
    resolved_file1_stats = find_file(file1_arg_stats)
    resolved_file2_stats = find_file(file2_arg_stats)

    if not resolved_file1_json:
        print(f"Error: Could not find file '{file1_arg_json}'.")
        sys.exit(1)
    if not resolved_file2_json:
        print(f"Error: Could not find file '{file2_arg_json}'.")
        sys.exit(1)
    if not resolved_file1_stats:
        print(f"Error: Could not find file '{file1_arg_stats}'.")
        sys.exit(1)
    if not resolved_file2_stats:
        print(f"Error: Could not find file '{file2_arg_stats}'.")
        sys.exit(1)

    with open(resolved_file1_json, 'r') as f:
        file1_json = json.load(f)
    with open(resolved_file2_json, 'r') as f:
        file2_json = json.load(f)

    counts1 = read_index_stats(resolved_file1_stats)
    counts2 = read_index_stats(resolved_file2_stats)

    file1_data = extract_timestamp_data(file1_json)
    file2_data = extract_timestamp_data(file2_json)

    comparison = compare_data(file1_data, file2_data, counts1, counts2)
    if not comparison:
        print("No data to compare.")
        return
    print_markdown_table(comparison, "date", "date_nanos")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python compare_timestamp_storage.py <test-name>")
        sys.exit(1)

    test_name = sys.argv[1]
    main(test_name)
