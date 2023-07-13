import argparse
import csv
import gzip
import logging
import os
import pickle
import sys
from collections import Counter

import requests

# Set up the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Define a handler to output log messages to the console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Define a formatter for the log messages
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)

# Add the console handler to the logger
logger.addHandler(console_handler)


class ClickStreamDist:
    def __init__(self, year, month, lang):
        self.filename = f"clickstream-{lang}wiki-{year}-{month:02d}.tsv.gz"
        self.url = f"https://dumps.wikimedia.org/other/clickstream/{year:d}-{month:02d}/{self.filename}"
        self.clickstream_output_file = os.path.expanduser(f"~/.rally/benchmarks/data/wikipedia/{self.filename}")

    def download(self):
        if os.path.exists(self.clickstream_output_file):
            logger.info("File already exists. Skipping download.")
            return

        logger.info("Downloading the clickstream file...")
        response = requests.get(self.url)

        if response.status_code == 200:
            # Create the file if it is missing
            os.makedirs(os.path.dirname(self.clickstream_output_file), exist_ok=True)

            # Write the content to the file
            with open(self.clickstream_output_file, "wb") as file:
                file.write(response.content)
            logger.info("File downloaded successfully.")
        else:
            logger.info("Failed to download the file.")

    def analyze(self):
        logger.info("Analyzing...")

        word_freq = self.calculate_word_frequency()
        word_prob = self.calculate_word_probability(word_freq)

        self.dump_probability_distribution(word_prob)

        logger.info("Analysis completed.")

    def calculate_word_frequency(self):
        logger.info("Calculating word frequency...")

        word_freq = Counter()
        with gzip.open(self.clickstream_output_file, "rt", encoding="utf-8") as file:
            # Documentation for clickstream format: https://meta.wikimedia.org/wiki/Research:Wikipedia_clickstream
            for row in csv.reader(file, delimiter="\t"):
                prev, curr, count = row[0], row[1].replace("_", " ").strip().replace('"', ""), int(row[3])
                if prev != "other-search" and curr != "Main Page":
                    word_freq[curr] += count

        sorted_word_freq = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)

        return sorted_word_freq[:10000]

    def calculate_word_probability(self, word_freq):
        logger.info("Calculating word probability...")

        total_words = sum(count for _, count in word_freq)

        return [(word, count / total_words) for word, count in word_freq]

    def dump_probability_distribution(self, prob_dist):
        logger.info("Dumping probability distribution...")

        writer = csv.writer(sys.stdout)
        writer.writerow(["query", "probability"])
        writer.writerows(prob_dist)


parser = argparse.ArgumentParser()
parser.add_argument("--year", type=int, default=2023, help="Year")
parser.add_argument("--month", type=int, default=6, help="Month")
parser.add_argument("--lang", type=str, default="en", help="Language")
args = parser.parse_args()

click_stream = ClickStreamDist(year=args.year, month=args.month, lang=args.lang)
click_stream.download()
click_stream.analyze()
