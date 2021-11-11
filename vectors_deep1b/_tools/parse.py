#!/usr/bin/env python3
import sys
import struct
import json

try:
	from tqdm import tqdm
	iterate = lambda i: tqdm(range(i))
except ModuleNotFoundError:
	print("Warning: [tqdm] package is not available and you won't be able to see progress.", file=sys.stderr)
	iterate = range

dims = 96
num_vectors = 9990000 


def to_json(f):
	for i in iterate(num_vectors):
		f.read(4)  # in .fvecs format for each vector the first 4 bytes represent dim
		vector = struct.unpack('f' * dims, f.read(dims * 4))

		record = {}
		record['vector'] = vector
		print(json.dumps(record, ensure_ascii=False))


if len(sys.argv) != 2:
	print(f"Error: No .fvecs file. Rerun using [{sys.argv[0]} /path/to/deep10M.fvecs].")
	sys.exit(1)

with open(sys.argv[1], 'rb') as f:
	to_json(f)
