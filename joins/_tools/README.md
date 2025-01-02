## About JOINS datasets


### Contents 

This directory contains two scripts

- joins_main_idx.sh - generates the main index, ie. the one that is intended to be used in the FROM clause of the query.
- lookup_idx.sh - generates lookup (join) indexes, ie. those that are intended to be used in the JOIN command.


### Generating the main index

`joins_main_idx.sh` generates JSON documents with the following fields:

- `id`: numeric (incremental)
- `@timestamp`: numeric, with value id + 946728000 
- `key_1000`: string, with value id%1000, intended to be a foreign key to a lookup index
- `key_100000`: string, with value id%100000, intended to be a foreign key to a lookup index
- `key_200000`: string, with value id%200000, intended to be a foreign key to a lookup index
- `key_500000`: string, with value id%500000, intended to be a foreign key to a lookup index
- `key_1000000`: string, with value id%1000000, intended to be a foreign key to a lookup index
- `key_5000000`: string, with value id%5000000, intended to be a foreign key to a lookup index
- `key_100000000`: string, with value id%100000000, intended to be a foreign key to a lookup index
- 100 additional text fields (`field_0` to `field_99`)

By default it produces 1000 documents (one per row), but the number can be changed passing a command line argument.

#### Example usage

Generate a file with 50.000 documents and bzip it: 

```shell
./joins_main_idx.sh 50000 | bzip2 -c > join_base_idx.json.bz2
```


### Generating the lookup indexes

`lookup_idx.sh` produces a lookup index. 

It accepts three parameters as input:

- cardinality (default 1000): the number of keys to be generated 
- fields (default 10): the number of additional fields per document
- repetitions (default 1): the number of repetitions per key

The result will be a file with the following fields:

- `key_<cardinaltity>`: a text containing the lookup key (practically, it's just a sequential number). 
Since the default cardinality is 1000, the name of this field will be `key_1000` by default. 
Passing a different cardinality as input will also result in a different field name.
- `M` additional fields (`M` is defined by the `fields` input param), called `lookup_keyword_0`, `lookup_keyword_1`...`lookup_keyword_M-1`, 
containing the following string:  `val <id> rep <repetition>`; the id is the same as the value of the key, the repetition is the value of the repetition (exmaple below) 

#### Example usage


Generate a lookup dataset with 20.000 keys, repeated 3 times each (ie. 60.000 documents in total), with 5 additional text fields.
Then shuffle the rows and bzip the result.

```shell
./lookup_idx.sh 20000 5 3 | shuf | bzip2 - c > my_lookup_idx.json.bz2
```

The generated file will be like:

```json
...
{"key_20000": "15", "field_0": "val 15 rep 0",  ... "field_4": "val 15 rep 0"}
...
```




## The default dataset

The dataset for this benchmark was generated with the following:

```shell
./lookup_idx.sh 1000 10 1 | shuf | bzip2 -c > lookup_idx_1000_f10.json.bz2
./lookup_idx.sh 100000 10 1 | shuf | bzip2 -c > lookup_idx_100000_f10.json.bz2
./lookup_idx.sh 200000 10 1 | shuf | bzip2 -c > lookup_idx_200000_f10.json.bz2
./lookup_idx.sh 500000 10 1 | shuf | bzip2 -c > lookup_idx_500000_f10.json.bz2
./lookup_idx.sh 1000000 10 1 | shuf | bzip2 -c > lookup_idx_1000000_f10.json.bz2
./lookup_idx.sh 5000000 10 1 | shuf | bzip2 -c > lookup_idx_5000000_f10.json.bz2
./joins_main_idx.sh 10000000 | bzip2 -c > join_base_idx-10M.json.bz2
```