This dataset contains the rides that have been performed in yellow taxis in
New York in December 2015. It can be downloaded
from http://www.nyc.gov/html/tlc/html/about/trip_record_data.shtml.

This has only de tested with the December 2015 dump, but this should work with
any dump of the yellow taxis, and should be easy to adapt to the green taxis.

Once downloaded, you can generate the mappings with:
  python3 parse.py mappings

And the json documents  can be generated with
  python3 parse.py json file_name.csv > documents.json

Finally the json docs can be compressed with
  bzip2 -k documents.json
