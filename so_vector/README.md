## StackOverflow vector track

This track benchmarks advanced searches on dense vector fields. Unlike the
`dense_vector` track, each document contains other fields besides vectors to
support testing features like ANN with filtering and hybrid search.

The dataset is derived from this dump of StackOverflow posts: <TODO add link here>

It only contains question documents -- all documents representing answers have
been removed. Each question title was encoded into a vector using the sentence
transformer model
[multi-qa-mpnet-base-cos-v1](https://huggingface.co/sentence-transformers/multi-qa-mpnet-base-cos-v1).

Each question and answer have formatted into a JSON document with the following fields:

	questionId:	      a unique ID
	acceptedAnswerId: the unique ID of the answer accepted for question
	title:	          a free-text field with the question title
  title_vector:     the question title encoded as a vector
	creationDate:	    the date the question was asked
	user:	            the user's unique ID
	tags:	            an array of tags describing the topics
  body:             field containing the text of the question or answer

Fields that do not have values have been left out. The body text was extracted
formatted to fit into JSON documents.

Run this command to generate the JSON dataset: <TODO add a script and fill in this section>

### Example Document

```json
{
	"user": "45",
	"tags": ["c#", "linq", ".net-3.5"],
	"questionId": "59",
	"creationDate": "2008-08-01T13:14:33.797",
	"title": "How do I get a distinct, ordered list of names from a DataTable using LINQ?",
  "title_vector": [-0.03565507382154465, 0.029150789603590965, -0.009953430853784084, ...],
	"acceptedAnswerId": "43110",
	"body": "Let's say I have a DataTable with a Name column. I want to have a collection of the unique names ordered alphabetically. The following query ignores the order by clause. var names = (from DataRow dr in dataTable.Rows orderby (string)dr[\"Name\"] select (string)dr[\"Name\"]).Distinct(); Why does the orderby not get enforced? "
}
### Parameters

This track accepts the following parameters with Rally 0.8.0+ using `--track-params`:

* `bulk_size` (default: 500)
* `bulk_indexing_clients` (default: 1)
* `ingest_percentage` (default: 100)
