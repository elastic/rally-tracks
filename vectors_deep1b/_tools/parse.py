import sys
import struct
import json
from tqdm import tqdm

def to_json(f):
	for i in tqdm(range(num_vectors)) :
		f.read(4)  # in .fvecs format for each vector the first 4 bytes represent dim
		vector = struct.unpack('f' * dims, f.read(dims * 4))

		record = {}
		record['vector'] = vector
		print(json.dumps(record, ensure_ascii=False))


dims = 96
num_vectors = 9990000 

with open(sys.argv[1], 'rb') as f:
	to_json(f)	
