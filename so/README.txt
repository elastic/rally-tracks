This dataset is derived from a dump of StackOverflow posts downloaded on June 10th 2016 from
https://ia800500.us.archive.org/22/items/stackexchange/stackoverflow.com-Posts.7z
The license is CC-SA-3.0 http://creativecommons.org/licenses/by-sa/3.0/

Each question and answer have formatted into a JSON document with the following fields:

	questionId:	      a unique ID for a question
	answerId:         a unique ID for an answer
	acceptedAnswerId: the unique ID of the answer accepted for question
	title:            a free-text field with the question title
	creationDate:     The date the questions was asked 
	user:             The user's unique ID
	tags:             An array of tags describing the technologies.
	body:             Field contsaining the text of the question or answer.
	type:             Type of post. Either 'question' or 'answer'

Fields that do not have values have been left out. The body has had text extracted and been 
formatted to fit into JSON documents. The _all field has been disabled in the mappings.

Data preparation process:
* Question and answer entries in the original posts.XML were converted to slimmed-down JSON documents.
* No enrichment was performed.
These scripts are available in the raw_data_prep_script.zip file.
