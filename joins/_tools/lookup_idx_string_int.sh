#!/bin/zsh

# generate the corpus of the lookup index
# with the following fields:
# key_<cardinality>: a keyword field with cardinality <cardinality>
# lookup_keyword_1..n: n keyword fields
# lookup_int_1..n: n keyword fields
#
# the value of the lookup_* fiels is just an incremental number, starting from zero, different for each record.
# All the lookup_* fields for the same record will have the same value
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
  echo "This script accepts zero or three arguments: cardinality, number of fields and number of repetitions"
  echo "eg."
  echo
  echo "./lookup_idx_constant_key.sh 100 20 3"
  echo
  echo "will produce 300 documents, 100 keys (repeated three times), each document with 20 keyword fields"
fi

counter=0

for ((id = 0; id<cardinality; id++)); do
  for ((repetition = 0; repetition<repetitions; repetition++)); do
    echo -n '{'
    echo -n '"key_'$cardinality'": "'$id'"'
    for ((i = 0; i<fields; i++)); do
      echo -n ', "lookup_keyword_'$i'": "'$counter'"'
      echo -n ', "lookup_int_'$i'": '$counter
    done
    counter=$((counter+1))
    echo '}'
  done
done;
