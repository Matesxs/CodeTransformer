from git import rmtree
from tqdm import tqdm
import os

if os.path.exists("repos"):
  entries = [os.path.join("repos", f) for f in os.listdir("repos")]

  for entry in tqdm(entries):
    rmtree(entry)

  rmtree("repos")
