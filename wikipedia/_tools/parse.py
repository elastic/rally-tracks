import sys
import json
from xml.etree import cElementTree as ET

PAGE_TAG = 'page'
SITEINFO_TAG = 'siteinfo'
XML_NAMESPACES = { '': 'http://www.mediawiki.org/xml/export-0.10/' }


def doc_generator(f):
    namespaces = dict()
    for _, element in ET.iterparse(f):
        _, tag = element.tag.split('}')
        if tag == PAGE_TAG:
            yield parse_page(element, namespaces)
        if tag == SITEINFO_TAG:
            namespaces = parse_namespaces(element)

def to_json(f):
    for doc in doc_generator(f):
        print(json.dumps(doc))

def parse_namespaces(element) -> dict:
    namespaces = dict()
    for namespace_element in element.findall('namespaces/namespace', XML_NAMESPACES):
        namespaces[namespace_element.get('key')] = namespace_element.text
    return namespaces

def parse_page(element, namespaces):
    page_data = {
        'title': element.find('title', XML_NAMESPACES).text,
    }

    redirect = element.find('redirect', XML_NAMESPACES)
    if redirect is not None:
        page_data['redirect'] = redirect.get('title')
    else:
        page_data['content'] = element.find('revision/text', XML_NAMESPACES).text

    namespace = namespaces[element.find('ns', XML_NAMESPACES).text]
    if namespace is not None:
        page_data['namespace'] = namespace

    return page_data

for file_name in sys.argv[1:]:
    to_json(file_name)
