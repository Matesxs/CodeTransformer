from git import rmtree
from tqdm import tqdm
import os
import sys

assert len(sys.argv) == 2 and os.path.exists(sys.argv[1]) and os.path.isdir(sys.argv[1]), "Invalid path to repos forlder"

if os.path.exists(sys.argv[1]):
  entries = [os.path.join(sys.argv[1], f) for f in os.listdir(sys.argv[1])]

  for entry in tqdm(entries):
    rmtree(entry)

  rmtree(sys.argv[1])
