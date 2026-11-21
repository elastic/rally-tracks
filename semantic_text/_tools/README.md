Instead of indexing the "text" field in the dataset as "semantic_text" field which generates embeddings at indexing time, this rally track pre-generates embeddings and indexes them as "dense_vector" field
Reason for doing this is to make indexing faster, re-use embeddings across runs, thus saving cost.

