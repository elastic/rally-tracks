import json
import re
from os import environ
from random import choice

import cohere
from datasets import load_dataset

DATASET_NAME: str = "Cohere/msmarco-v2-embed-english-v3"
DATASET_SPLIT: str = "train"
OUTPUT_FILENAME: str = "queries.json"
MAX_DOCS = 12_000
SENTENCE_RE = re.compile(r".*?[\.\!\?]+")
QUESTION_RE = re.compile(r"[^.^\!^:]*?[\?]+")

# Get your production Cohere API key from https://dashboard.cohere.com/api-keys
co = cohere.Client(environ["COHERE_API_KEY"])


def output_queries(queries_file):
    output = []
    queries = load_dataset(DATASET_NAME, split=DATASET_SPLIT, streaming=True)

    # Start off with a randomized sample from a random shard
    queries.shuffle(buffer_size=10_000)
    for query in queries:
        sentences = SENTENCE_RE.findall(query["text"])
        if sentences:
            sentence = choice(sentences)
        else:
            continue

        try:
            # If we say average of 200 input tokens and 200 output tokens, the
            # reality is actually more like 30 input tokens and 80 output, but
            # we're saying 400 is the *maximum*, then:
            # (12,000 * 200 input tokens) + (12_000 * 200 output tokens) ~= $8.00
            # at most to generate our queries.
            response = co.generate(model="command", prompt=f"generate a question from: {sentence}", max_tokens=400)

            if "nonsense" in response.generations[0].text.lower():
                continue

            # Try to extract a single sentence query ending in "?"
            # otherwise use the full response
            questions = QUESTION_RE.findall(response.generations[0].text)
            question = choice(questions) if questions else response.generations[0].text
            print(question)
        except Exception as e:
            print(e)
            continue

        response = co.embed(texts=[question], model="embed-english-v3.0", input_type="search_query")
        output.append(response.embeddings)

        if len(output) == MAX_DOCS:
            break

        if len(output) % 2_000 == 0:
            # Take another randomized sample from a random shard every 2,000 queries
            queries.shuffle(buffer_size=10_000)

    queries_file.write("\n".join(json.dumps(embed) for embed in output))


if __name__ == "__main__":
    with open(OUTPUT_FILENAME, "w") as queries_file:
        output_queries(queries_file)
