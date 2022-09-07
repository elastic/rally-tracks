import argparse
import json
import re
import xml.sax
from pathlib import Path

from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer

model = "sentence-transformers/multi-qa-mpnet-base-cos-v1"
embedding_model = SentenceTransformer(model)

thedatawriter = None


class PostsHandler(xml.sax.ContentHandler):
    def startElement(self, name, attrs):
        if name == "row":
            postType = int(attrs["PostTypeId"])
            # only keep questions, dropping the answer posts
            if postType == 1:
                record = {}
                # In some questions e.g. 10030718 the ownerID is missing and we have OwnerDisplayName instead
                ownerDisplayName = ""
                ownerId = ""
                user = ""
                if "OwnerUserId" in attrs:
                    ownerId = attrs["OwnerUserId"]
                    record["user"] = ownerId
                elif "OwnerDisplayName" in attrs:
                    ownerDisplayName = attrs["OwnerDisplayName"]
                    record["user"] = ownerDisplayName
                tags = []
                if "Tags" in attrs:
                    tags = re.split("[<>]+", attrs["Tags"])
                    record["tags"] = [x for x in tags if len(x) > 0]

                record["type"] = "question"
                record["questionId"] = attrs["Id"]

                if "CreationDate" in attrs:
                    record["creationDate"] = attrs["CreationDate"]
                if "Title" in attrs:
                    record["title"] = attrs["Title"].replace("\n", " ").replace("\r", " ")
                    record["titleVector"] = embedding_model.encode(record["title"], normalize_embeddings=True).tolist()
                if "AcceptedAnswerId" in attrs:
                    record["acceptedAnswerId"] = attrs["AcceptedAnswerId"]
                if "Body" in attrs:
                    soup = BeautifulSoup(attrs["Body"], "html.parser")
                    body = soup.get_text().replace("\n", " ").replace("\r", "")
                    body = re.sub("\s+", " ", body)
                    record["body"] = body

                myjsonfile.write(json.dumps(record, separators=(",", ":")))
                myjsonfile.write("\n")


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(
        description="Script to process stack overflow posts. Filters out non-question type posts and computes vector embedding for Title fields",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    arg_parser.add_argument("file", help="Path to XML posts file")

    args = arg_parser.parse_args()

    posts_filename = args.file
    p = Path(posts_filename)
    output = p.with_suffix(".json")
    parser = xml.sax.make_parser()
    print("Preprocessing stack overflow posts")

    with open(output, "w") as myjsonfile:
        parser.setContentHandler(PostsHandler())
        parser.parse(open(posts_filename, "r"))
