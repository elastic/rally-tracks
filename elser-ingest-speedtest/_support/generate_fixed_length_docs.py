import json
import random

DOCUMENT_FIXED_LENGTH = 16
DOCUMENT_COUNT = 10000

with open("bert_vocab_whole_words.json") as word_file:
    word_list = json.load(word_file)

with open("../document_set.json", "w") as doc_file:
    for i in range(DOCUMENT_COUNT):
        doc_words = random.choices(word_list, k=DOCUMENT_FIXED_LENGTH)
        doc = {"body": " ".join(doc_words)}

        doc_file.writelines([json.dumps(doc), "\n"])
