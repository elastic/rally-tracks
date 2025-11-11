#!/bin/zsh

# generate the corpus of the lookup index
# with the following fields:
# key_<cardinality>: a keyword field with cardinality <cardinality>
# lookup_keyword_1..n: n keyword fields
#
# By default the script produces 1000 documents with one key (key_1000) of value 1...1000 (keywords), n keyword fields and n int fields per doc
#
# these defaults can be overridden passing the following command line arguments:
# - number of keys
# - cardinality for key1
# - cardinality for key2
# - ...
# - n of fields
# - n of repetitions
#
# The final number of documents will be the highest cardinality * n of repetitions
#
# eg.
#
# ./lookup_idx.sh 2 1000 10 20 3
#
# produces 3000 documents, each key will be repeated three times, each document will have
# - 2 keys ("key_1000" and "key_10")
# - 20 keyword fields and 20 int fields
# The key_1000 values will be values from 0 to 999
# The key_10 values will be values from 0 to 9





inputs=()
for arg in "$@"
do
    inputs+=($arg)
done

if [ "$#" -eq 0 ]; then
    nkeys=1
    cardinality=(1000)
    max_cardinality=1000
    fields=10
    repetitions=1
elif [ "$#" -gt 3 ]; then
    nkeys=$1
    cardinality=()
    max_cardinality=0
    for ((i = 1; i<nkeys+1; i++)); do
      cardinality[$i]=${inputs[i+1]}
      if [ $max_cardinality -lt $cardinality[i] ]; then
        max_cardinality=$cardinality[i]
      fi
    done
    fields=${inputs[nkeys+2]}
    repetitions=${inputs[nkeys+3]}
else
  echo "This script accepts zero or at least four arguments: number of keys, cardinalities, number of fields and number of repetitions"
  echo "eg."
  echo
  echo "./lookup_idx.sh 1 100 20 3"
  echo
  echo "will produce 300 documents, 100 keys (repeated three times), each document with 20 keyword fields"
fi

counter=0

for ((repetition = 0; repetition<repetitions; repetition++)); do
  for ((id = 0; id < max_cardinality; id++)); do
    echo -n '{'
    for ((k=1; k < nkeys+1; k++)); do
      card=${cardinality[k]}
      value=$((id%card))
      if [ $k -gt 1 ]; then
        echo -n ", "
      fi
      echo -n '"key_'$card'": "'$value'"'

    done
    for ((i = 0; i<fields; i++)); do
      echo -n ', "lookup_keyword_'$i'": "'$counter'"'
      echo -n ', "lookup_int_'$i'": '$counter
    done
    counter=$((counter+1))
    echo '}'
  done
done;
