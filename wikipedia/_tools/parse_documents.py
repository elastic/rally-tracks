import bz2
import json
import os
import sys
from xml.etree import cElementTree

PAGE_TAG = "page"
SITEINFO_TAG = "siteinfo"
XML_NAMESPACES = {"": "http://www.mediawiki.org/xml/export-0.11/"}


def doc_generator(f):
    namespaces = dict()
    count = 0

    for _, element in cElementTree.iterparse(f):
        _, tag = element.tag.split("}")
        if tag == PAGE_TAG:
            yield parse_page(element, namespaces)
            count += 1
            if count % 10000 == 0:  # Progress every 10000 documents
                print(f"Processed {count} documents...", file=sys.stderr)
            element.clear()
        if tag == SITEINFO_TAG:
            namespaces = parse_namespaces(element)

    print(f"Finished processing {count} documents...", file=sys.stderr)


def get_doc_meta(doc_data, op_type="index"):
    return {op_type: {"_index": "wikipedia", "_id": doc_data["title"]}}


def to_json(f):
    document_count = 0
    json_bytes = 0

    with bz2.BZ2File(f, "r") as fp:
        for doc_data in doc_generator(fp):
            meta_line = json.dumps(get_doc_meta(doc_data))
            doc_line = json.dumps(doc_data)

            print(meta_line)
            print(doc_line)

            # Count bytes (including newlines)
            json_bytes += len(meta_line.encode('utf-8')) + 1  # +1 for newline
            json_bytes += len(doc_line.encode('utf-8')) + 1  # +1 for newline

            document_count += 1

    return document_count, json_bytes


def parse_namespaces(element) -> dict:
    namespaces = dict()
    for namespace_element in element.findall("namespaces/namespace", XML_NAMESPACES):
        namespaces[namespace_element.get("key")] = namespace_element.text
    return namespaces


def parse_page(element, namespaces):
    page_data = {
        "title": element.find("title", XML_NAMESPACES).text,
    }

    redirect = element.find("redirect", XML_NAMESPACES)
    if redirect is not None:
        page_data["redirect"] = redirect.get("title")
    else:
        page_data["content"] = element.find("revision/text", XML_NAMESPACES).text

    namespace = namespaces[element.find("ns", XML_NAMESPACES).text]
    if namespace is not None:
        page_data["namespace"] = namespace

    return page_data


for file_name in sys.argv[1:]:
    compressed_size = os.path.getsize(file_name)
    document_count, json_size = to_json(file_name)

    print(f"Number of documents: {document_count} documents", file=sys.stderr)
    print(f"Compressed file size: {compressed_size} bytes", file=sys.stderr)
    print(f"Json file size: {json_size} bytes", file=sys.stderr)
