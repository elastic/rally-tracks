import argparse
import datasets
import json

if __name__ == "__main__": 
    arg_parser = argparse.ArgumentParser(
        description="Script to process vectors.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    arg_parser.add_argument("path", help="Path to dataset folder")
    args = arg_parser.parse_args()
    dataset_path = args.path

    ds = datasets.load_from_disk(dataset_path)
    print(ds)
    print("Preprocessing documents")

    ndoc = 0
    with open('documents.json', 'w') as file_out:
        for row in ds:
            doc = {}
            doc["id"] = row["_id"]
            doc["title"] = row["title"]
            doc["text"] = row["text"]
            doc["vector"] = row["embedding"]
            file_out.write(json.dumps(doc, separators=(",", ":")))
            file_out.write("\n")
            ndoc += 1
print("Processed {} documents".format(ndoc))
            
