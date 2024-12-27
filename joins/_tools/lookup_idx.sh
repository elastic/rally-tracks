#!/bin/zsh

# generate the corpus of the lookup index
# with the following fields:
# key_<cardinality>: a keyword field with cardinality <cardinality>
# lookup_keyword_1..n: n keyword fields
#
# By default the script produces 1000 documents with keys 1...000, 10 keyword fields per doc
#
# these defaults can be overridden passing the following command line arguments:
# - cardinality:
# - n of fields
# - n of repetitions
#
# The final number of documents will be cardinality X n of repetitions
#
# eg.
#
# ./lookup_idx.sh 1000 20 3
#
# produces 3000 documents, each key will be repeated three times, each document will have 20 keyword fields




if [ "$#" -eq 0 ]; then
    cardinality=1000
    fields=10
    repetitions=1
elif [ "$#" -eq 3 ]; then
    cardinality=$1
    fields=$2
    repetitions=$3
else
  echo "This script accepts three arguments: cardinality, number of fields and number of repetitions"
  echo "eg."
  echo
  echo "./lookup_idx.sh 100 20 3"
  echo
  echo "will produce 300 documents, 100 keys (repeated three times), each document with 20 keyword fields"
fi

for ((id = 0; id<cardinality; id++)); do
  for ((repetition = 0; repetition<repetitions; repetition++)); do
    echo -n '{'
    echo -n '"key_'$cardinality'": "'$id'"'
    for ((i = 0; i<fields; i++)); do
      echo -n ', "lookup_keyword_'$i'": "val '$id' rep '$repetition'"'
    done
    echo '}'
  done
done;
