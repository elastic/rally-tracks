# semantic-multilingual

Compares three retrieval approaches on multilingual Wikipedia data:

| Model | `model` param | Field type |
|-------|---------------|------------|
| ELSER (sparse, English-optimised) | `elser` | `semantic_text` → `.elser-2-elasticsearch` |
| Jina V5 (dense, multilingual) | `jina` | `semantic_text` → `.jina-embeddings-v5-text-small` |
| BM25 (standard tokenizer) | `bm25` | `text` with `standard` analyzer |

Datasets:

| Language | `language` param | Docs |
|----------|------------------|------|
| English Wikipedia (random sample) | `en` | 100,000 |
| Spanish Wikipedia (random sample) | `es` | 100,000 |
| Dhivehi Wikipedia (complete) | `dv` | ~89 |

## Data preparation

Data files live in `data/` (git-ignored). To regenerate from the model-change-eval project:

```bash
cd ~/Intellij/model-change-eval
for lang in en es dv; do
  gunzip -c data/wikipedia_${lang}.jsonl.gz | pbzip2 -c \
    > ~/Intellij/rally-tracks/semantic-multilingual/data/wikipedia_${lang}.json.bz2
done
```

## Local runs

```bash
cd ~/Intellij/rally-tracks

# BM25, English, local cluster
esrally race \
  --track-path=semantic-multilingual \
  --target-hosts=localhost:9200 \
  --client-options="use_ssl:true,verify_certs:false,basic_auth_user:'elastic',basic_auth_password:'changeme'" \
  --pipeline=benchmark-only \
  --on-error=abort \
  --kill-running-processes \
  --track-params='{"model":"bm25","language":"en"}'

# ELSER, English
esrally race \
  --track-path=semantic-multilingual \
  --target-hosts=localhost:9200 \
  --client-options="use_ssl:true,verify_certs:false,basic_auth_user:'elastic',basic_auth_password:'changeme'" \
  --pipeline=benchmark-only \
  --on-error=abort \
  --kill-running-processes \
  --track-params='{"model":"elser","language":"en"}'

# Jina V5, Spanish
esrally race \
  --track-path=semantic-multilingual \
  --target-hosts=localhost:9200 \
  --client-options="use_ssl:true,verify_certs:false,basic_auth_user:'elastic',basic_auth_password:'changeme'" \
  --pipeline=benchmark-only \
  --on-error=abort \
  --kill-running-processes \
  --track-params='{"model":"jina","language":"es"}'

# Quick smoke test (--test-mode uses 1k docs)
esrally race \
  --track-path=semantic-multilingual \
  --target-hosts=localhost:9200 \
  --client-options="use_ssl:true,verify_certs:false,basic_auth_user:'elastic',basic_auth_password:'changeme'" \
  --pipeline=benchmark-only \
  --on-error=abort \
  --test-mode \
  --track-params='{"model":"bm25","language":"en"}'
```

## Track params

| Param | Default | Options |
|-------|---------|---------|
| `model` | `bm25` | `elser`, `jina`, `bm25` |
| `language` | `en` | `en`, `es`, `dv` |
| `bulk_size` | `100` | integer |
| `bulk_indexing_clients` | `1` | integer |
| `search_clients` | `1` | integer |
| `search_iterations` | `500` | integer |
| `search_warmup_iterations` | `50` | integer |
| `number_of_shards` | `1` | integer |
| `number_of_replicas` | `0` | integer |

## esbench

Upload the data directory to GCP first:

```bash
gsutil -m cp data/*.json.bz2 gs://rally-tracks/semantic-multilingual/
```

Then add `data_url` to your esbench params JSON:

```json
{
  "track.name": "semantic-multilingual",
  "track.revision": "your-branch",
  "track.params": {
    "model": "jina",
    "language": "en",
    "data_url": "https://storage.googleapis.com/rally-tracks/semantic-multilingual"
  }
}
```
