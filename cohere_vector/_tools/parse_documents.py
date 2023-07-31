import json
import sys
from datasets import load_dataset
import numpy as np

DATASET_NAME: str = f"Cohere/miracl-en-corpus-22-12"
OUTPUT_FILENAME: str = "documents.json"
DEFAULT_MAX_DOCS = -1

def output_documents(docs_file):
  max_documents = int(sys.argv[1]) if sys.argv[1] else DEFAULT_MAX_DOCS
  partial_index = max_documents != DEFAULT_MAX_DOCS

  if partial_index:
     print("Parsing {} documents".format(max_documents))
  else:
     print("Parsing entire {} dataset".format(DATASET_NAME))
  docs = load_dataset(DATASET_NAME, split="train", streaming=True)
  doc_count = 0
  for doc in docs:
      v = np.array(doc['emb'])
      v_unit = v / np.linalg.norm(v)
      docs_file.write(json.dumps({
         "docid": doc['docid'],
         "title": doc['title'],
         "text": doc['text'],
         "emb": v_unit.tolist(),
      }, ensure_ascii=True))
      docs_file.write("\n")
      doc_count += 1
      if partial_index and doc_count >= max_documents:
         return

if __name__ == "__main__":
  print("Outputing documents to {}".format(OUTPUT_FILENAME))
  with open(OUTPUT_FILENAME, "w") as documents_file:
    output_documents(documents_file)
