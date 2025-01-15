#!/bin/zsh

# generate the corpus of the main index
# with the following fields:
# id: sequential
# @timestamp: sequential, starting Jan 1st 2000
# key_1_000: a keyword field with cardinality 1.000
# key_100_000: a keyword field with cardinality 100.000
# key_200_000: a keyword field with cardinality 200.000
# key_500_000: a keyword field with cardinality 500.000
# key_1_000_000: a keyword field with cardinality 1.000.000
# key_5_000_000: a keyword field with cardinality 5.000.000
# key_100_000_000: a keyword field with cardinality 100.000.000
# field_1..100: 100 text fields
#
#
# By default the script produces 1000 documents with 100 additional keyword fields, but this default is overridden passing two command line arguments,
# eg.
#
# ./joins_main_idx.sh 100000 3
#
# produces 100.000 documents with 3 additional fields each



if [ "$#" -eq 0 ]; then
    ndocs=1000
    fields=100
elif [ "$#" -eq 2 ]; then
    ndocs=$1
    fields=$2
else
  echo "This script accepts zero or two arguments: number of docs, number of additional fields"
  echo "eg."
  echo
  echo "./joins_main_idx.sh 100 20"
  echo
  echo "will produce 100 documents, each document with 20 additional keyword fields"
  echo
  echo "With no arguments:"
  echo
  echo "./joins_main_idx.sh"
  echo
  echo "will produce 1000 documents, each document with 100 additional keyword fields"
fi

for ((id = 0; id<ndocs; id++)); do
  echo -n '{'
  echo -n '"id": '$id''
  echo -n ', "@timestamp": '$((id+946728000))
  echo -n ', "key_1000": "'$((id%1000))'"'
  echo -n ', "key_100000": "'$((id%100000))'"'
  echo -n ', "key_200000": "'$((id%200000))'"'
  echo -n ', "key_500000": "'$((id%500000))'"'
  echo -n ', "key_1000000": "'$((id%1000000))'"'
  echo -n ', "key_5000000": "'$((id%5000000))'"'
  echo -n ', "key_100000000": "'$((id%100000000))'"'
  for ((i = 0; i<fields; i++)); do
    echo -n ', "field_'$i'": "value '$i'_'$id'"'
  done
  echo '}'
done;
