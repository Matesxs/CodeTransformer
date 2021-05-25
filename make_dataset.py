import os
import sys
from tqdm import tqdm
from config import n_positions

MAX_CHAR_LENGTH = n_positions
MIN_CHAR_LENGTH = MAX_CHAR_LENGTH / 2

assert len(sys.argv) == 2, "Enter output dataset name as fist argument (.txt)"
OUTPUT_PATH = sys.argv[1]

NEWLINE_CHAR = "<newl>"

if not os.path.exists("github_data"): os.mkdir("github_data")
OUTPUT_PATH = os.path.join("github_data", OUTPUT_PATH)

python_files = []
for dirpath, dirnames, filenames in tqdm(os.walk("repos")):
  for f in filenames:
    full_path = os.path.join(dirpath, f)

    if full_path.endswith("topics.txt"):
      pass
    else:
      python_files.append(full_path)

if os.path.exists(OUTPUT_PATH): os.remove(OUTPUT_PATH)

with open(OUTPUT_PATH, "a", encoding="utf-8") as f:
  for file_path in tqdm(python_files):
    try:
      data = open(file_path, "r").read()

      data_length = len(data)
      if 200 < data_length:
        fd = data.replace("\n", NEWLINE_CHAR)

        if data_length <= MAX_CHAR_LENGTH:
          f.write(f"{fd}\n")
        else:
          sd = fd.split(f"{NEWLINE_CHAR}{NEWLINE_CHAR}")
          substring = ""
          for split in sd:
            substring += split + f"{NEWLINE_CHAR}{NEWLINE_CHAR}"
            len_of_substring = len(substring)
            if MIN_CHAR_LENGTH <= len_of_substring:
              if len_of_substring <= MAX_CHAR_LENGTH:
                f.write(f"{substring}\n")
                substring = ""
              else:
                break
    except:
      pass