import json
import random

DOC_LENGTHS = [128, 256, 384, 512]
DOCUMENT_COUNT = 10000

with open("bert_vocab_whole_words.json") as word_file:
    word_list = json.load(word_file)

for doc_length in DOC_LENGTHS:
    with open(f"../{doc_length}_document_set.json", "w") as doc_file:
        for i in range(DOCUMENT_COUNT):
            doc_words = random.choices(word_list, k=doc_length)
            doc = {"body": " ".join(doc_words)}
            doc_file.writelines([json.dumps(doc), "\n"])
