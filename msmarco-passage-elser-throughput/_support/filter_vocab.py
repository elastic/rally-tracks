import re

pattern = re.compile(r"^[a-zA-Z]{2,}$")


lines = None
with open("huggingface.co_bert-base-uncased_raw_main_vocab.txt") as raw_vocab:
    lines = raw_vocab.readlines()


l2 = ['"'+s.strip()+'"' for s in lines if pattern.match(s)]

with open("bert_vocab_whole_words.json", "w") as outfile:
    outfile.write("[")
    outfile.write(",".join(l2))
    outfile.write("]")


