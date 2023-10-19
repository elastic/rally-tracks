## Wikipedia Search track

This track benchmarks

The dataset is derived from a dump of wikipedia availaible here:
https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles-multistream.xml.bz2.

Each page is formatted into a JSON document with the following fields:

title: Page title
namespace: Optional namespace for the page. [Namespaces](https://en.wikipedia.org/wiki/Wikipedia:Namespace) allow for the organization and separation of content pages from administration pages.
content: Page content.
redirect: If the page is a redirect, the target of the redirection. In this case content is empty.

Fields that do not have values have been left out.

### Generating the documents dataset

To regenerate the dataset from scratch, first download and unzip an archive
of Wikipedia dumps from [this link](https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles-multistream.xml.bz2) (~21GB).

Then run this command:

```bash
python _tools/parse_documents.py <path_to_xml_file> | pbzip2 -9 -k -m2000 > pages.json.bz2
```

### Generating clickstream probability ditribution

To generate the probability distribution of the most frequent queries in a specific month from the Wikimedia clickstream, please execute the following command

```bash
python3 _tools/parse_clicks.py --year 2023 --month 6 --lang en > queries.csv
```

### Example Document

```json
{
  "title": "Anarchism",
  "content": "{{short description|Political philosophy and movement}}\n{{other uses}}\n{{redirect2|Anarchist|Anarchists|other uses|Anarchist (disambiguation)}}\n{{distinguish|Anarchy}}\n{{good article}}\n{{pp-semi-indef}}\n{{use British English|date=August 2021}}\n{{use dmy dates|date=August 2021}}\n{{Use shortened footnotes|date=May 2023}}\n{{anarchism sidebar}}\n{{basic forms of government}}\n\n'''Anarchism''' is a [[political philosophy]] and [[Political movement|movement]] that is skeptical of all justifications for [[authority]] and seeks to abolish the [[institutions]] it claims maintain unnecessary [[coercion]] and [[Social hierarchy|hierarchy]], typically including [[government]]s,<ref name=\":0\">{{Cite book |title=The Desk Encyclopedia of World History |publisher=[[Oxford University Press]] |year=2006 |isbn=978-0-7394-7809-7 |editor-last=Wright |editor-first=Edmund |location=New York |pages=20\u201321}}</ref> [[State (polity)|nation states]],{{sfn|Suissa|2019b|ps=: \"...as many anarchists have stressed, it is not government as such that they find objectionable, but the hierarchical forms of government associated with the nation state.\"}} [[law]] and [[law enforcement]],<ref name=\":0\" /> and [[capitalism]]. Anarchism advocates for the replacement of the state with [[Stateless society|stateless societies]] or other forms of [[Free association (communism and anarchism)|free associations]]. As a historically [[left-wing]] movement, this reading of anarchism is placed on the [[Far-left politics|farthest left]] of the [[political spectrum]], usually described as the [[libertarian]] wing of the [[socialist movement]] ([ ..."
}
```

### Parameters

This track accepts the following parameters with Rally 0.8.0+ using `--track-params`:
- Index settings:
  - `number_of_replicas` (default: `0`)
  - `number_of_shards` (default: `1`)
  - `index_mapping_type` (default: `minimal`)
- Initial indexing:
  - `initial_indexing_bulk_clients` (default: `5`)
  - `initial_indexing_bulk_size` (default: `500`)
  - `initial_indexing_ingest_percentage` (default: `100`)
  - `initial_indexing_bulk_warmup_time_period` (default: `40` )
- Standalone search:
  - `standalone_search_clients` (default: `20`)
  - `standalone_search_time_period` (default: `300`)
  - `standalone_search_warmup_time_period` (default: `10`)
- Application search:
  - `application_search_clients` (default: `20`)
  - `application_search_time_period` (default: `300`)
  - `application_search_warmup_time_period` (default: `10`)
- Concurrent searcgh & indexing:
  - `parallel_indexing_bulk_clients` (default: `1`)
  - `parallel_indexing_bulk_size` (default: `500`)
  - `parallel_indexing_bulk_warmup_time_period` (default: `10`)
  - `parallel_indexing_bulk_target_throughput` (default: `1`)
  - `parallel_indexing_search_clients` (default: `20`)
  - `parallel_indexing_search_time_period`: (default: `300`)
  - `parallel_indexing_search_warmup_time_period` (default: `10`)
  - `parallel_indexing_target_throughput`: (default: `100`)

### License

We use the same license for the data as the original data: [CC-SA-3.0](http://creativecommons.org/licenses/by-sa/3.0/).
More details can be found on [this page](https://en.wikipedia.org/wiki/Wikipedia:Copyrights).
