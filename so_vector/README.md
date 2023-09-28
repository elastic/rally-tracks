## StackOverflow vector track

This track benchmarks advanced searches on dense vector fields. Unlike the
`dense_vector` track, each document contains other fields besides vectors to
support testing features like ANN with filtering and hybrid search.

The dataset is derived from a dump of StackOverflow posts downloaded on April, 21st 2022 from
https://archive.org/download/stackexchange/stackoverflow.com-Posts.7z.

It only contains question documents -- all documents representing answers have
been removed. Each question title was encoded into a vector using the sentence
transformer model
[multi-qa-mpnet-base-cos-v1](https://huggingface.co/sentence-transformers/multi-qa-mpnet-base-cos-v1).
This dataset contains the first 2 million questions.

Each post is formatted into a JSON document with the following fields:

  questionId:	      a unique ID
  acceptedAnswerId: the unique ID of the answer accepted for question
  title:	          a free-text field with the question title
  titleVector:      the question title encoded as a vector
  creationDate:	    the date the question was asked
  user:	            the user's unique ID
  tags:	            an array of tags describing the topics
  body:             field containing the text of the question or answer

Fields that do not have values have been left out. The body text was extracted
and formatted to fit into JSON documents.

### Generating the dataset

To regenerate the dataset from scratch, first download and unzip an archive
of StackExchange dumps from [this link](https://archive.org/download/stackexchange/stackoverflow.com-Posts.7z) (~17GB).

Then run this command:
```bash
python _tools/parse_embed.py <path_to_xml_file>
```

Before running the command you'll need to install the packages specified in `_tools/requirements.txt`.

> Please note that due to the large size of the XML dataset (~100GB unzipped), this can take a very long time to run (~ 10 days on a 2021 M1 Max Macbook Pro).
We recommend monitoring the script and stopping it once the output file has reached a satisfying size.

### Example Document

```json
{
	"user": "45",
	"tags": ["c#", "linq", ".net-3.5"],
	"questionId": "59",
	"creationDate": "2008-08-01T13:14:33.797",
	"title": "How do I get a distinct, ordered list of names from a DataTable using LINQ?",
  "titleVector": [-0.03565507382154465, 0.029150789603590965, -0.009953430853784084, ...],
	"acceptedAnswerId": "43110",
  "type": "question",
	"body": "Let's say I have a DataTable with a Name column. I want to have a collection of the unique names ordered alphabetically. The following query ignores the order by clause. var names = (from DataRow dr in dataTable.Rows orderby (string)dr[\"Name\"] select (string)dr[\"Name\"]).Distinct(); Why does the orderby not get enforced? "
}
```

### Parameters

This track accepts the following parameters with Rally 0.8.0+ using `--track-params`:

* `bulk_size` (default: 500)
* `bulk_indexing_clients` (default: 1)
* `ingest_percentage` (default: 100)
* `max_num_segments` (default: 1)

### License
We use the same license for the data as the original data: [CC-SA-4.0](http://creativecommons.org/licenses/by-sa/4.0/).
More details can be found on [this page](https://archive.org/details/stackexchange).
