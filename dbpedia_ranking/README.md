## DBPedia Passage Ranking Track

This track assesses the search performance of the dataset available at [mteb/dbpedia](https://huggingface.co/datasets/mteb/dbpedia).
To compare search performance, the following strategies are employed:
* `default`: This is a straightforward strategy that involves indexing the text fields using a standard analyzer and querying using a `match_all` query. No custom analysis is used.
* `english-analyzed`: In this strategy, we perform the same test as with `default` but with a basic custom english analyzer applied.


### Example Document

Documents adhere to the [JSON Lines format](https://jsonlines.org/).
When a single document is pretty printed, it takes the following example format:

<details>
  <summary><i>Example document</i></summary>

```json
{
  "_id": "<dbpedia:Animalia_(book)>",
  "title": "Animalia (book)",
  "text": "Animalia is an illustrated children's book by Graeme Base. It was originally published in 1986, followed by a tenth anniversary edition in 1996, and a 25th anniversary edition in 2012. Over three million copies have been sold.   A special numbered and signed anniversary edition was also published in 1996, with an embossed gold jacket."
}
```
</details>

### Example Query

Queries are structured within a JSON array, where each individual object signifies a unique 'query' and its corresponding expansion achieved through ELSER v2, which is stored pre-computed in the 'text_expansion_elser' field.:

<details>
  <summary><i>Example query object</i></summary>

TODO 

</details>

### Parameters
This track accepts the following parameters with Rally 0.8.0+ using `--track-params`:

* `bulk_size` (default: 5000)
* `bulk_indexing_clients` (default: 8)
* `ingest_percentage` (default: 100)
* `number_of_shards` (default: 1)
* `number_of_replicas` (default: 0)
* `search_clients` (default: 1)

### License
Terms and Conditions for using the mteb datasets can be found at https://github.com/embeddings-benchmark/mteb 
