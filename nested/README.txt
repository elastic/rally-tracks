This dataset is derived from a dump of StackOverflow posts downloaded on June 10th 2016 from
https://ia800500.us.archive.org/22/items/stackexchange/stackoverflow.com-Posts.7z
The license is CC-SA-3.0 http://creativecommons.org/licenses/by-sa/3.0/

Each question and related answers have been assembled into a single JSON doc containing:
	qid:	a unique ID for a question 
	title:	a free-text field with the question title
	creationDate:	The date the questions was asked 
	user:	The user's screen name and unique ID combined into a single string
	tag:	An array of tags describing the technologies.
	answers:	An array of objects, one per answer, with the following fields:
		date:	Date of answer
		user:	Answerer's screen name and unique ID combined into a single string
		

Data preparation process:
* Question and answer entries in the original posts.XML were converted to slimmed-down rows 
  in a CSV and enriched with user names from users.xml
* CSV was sorted by first two columns (questionID and answerID)
* The CSV was converted to the JSON file presented here, combining questions and answers into 
  a single JSON doc
These scripts are available in the raw_data_prep_scripts.zip file.

