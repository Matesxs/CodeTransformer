from genericpath import exists
import os
import sys
import argparse
import shutil
import time
from tqdm import tqdm
from config_loader import Config

MAX_CHAR_LENGTH = Config.n_positions
MIN_CHAR_LENGTH = MAX_CHAR_LENGTH / 2

parser = argparse.ArgumentParser()
parser.add_argument("--input", "-i", help="Path to input repos folder", required=False, default="repos", type=str)
parser.add_argument("--output", "-o", help="Path to output folder", required=False, default="github_data", type=str)
parser.add_argument("--name", "-n", help="Name of output file", required=True, type=str)
parser.add_argument("--delete", "-d", help="Delete input folder and files in progress (BE CAREFUL AND USE ON YOUR OWN RISK) (use only on ssd or it will hurt performance)", action="store_true")

args = parser.parse_args()
assert os.path.exists(args.input) and os.path.isdir(args.input), "Invalid input path"

if not os.path.exists(args.output): os.mkdir(args.output)
OUTPUT_PATH = os.path.join(args.output, args.name)

python_files = []
for dirpath, dirnames, filenames in tqdm(os.walk(args.input)):
  for f in filenames:
    full_path = os.path.join(dirpath, f)
    python_files.append(full_path)

if os.path.exists(OUTPUT_PATH): os.remove(OUTPUT_PATH)

with open(OUTPUT_PATH, "a", encoding="utf-8") as f:
  for file_path in tqdm(python_files):
    try:
      file = open(file_path, "r")
      data = file.read()
      file.close()

      data_length = len(data)
      if 200 < data_length:
        fd = data.replace("\n", Config.new_line_tag)

        if data_length <= MAX_CHAR_LENGTH:
          f.write(f"{fd}\n")
        else:
          # If section is too large then split it
          sd = fd.split(f"{Config.new_line_tag}{Config.new_line_tag}")
          substring = ""

          # Iterate over split parts
          for split in sd:
            # Create new substring from old substring and current split part
            substring += split + f"{Config.new_line_tag}{Config.new_line_tag}"
            len_of_substring = len(substring)

            # If length of current new substring is enough process it
            if MIN_CHAR_LENGTH <= len_of_substring:
              # If length is in top boundaries
              if len_of_substring <= MAX_CHAR_LENGTH:
                f.write(f"{substring}\n")

              # If not check newer part
              elif MIN_CHAR_LENGTH <= len(split) <= MAX_CHAR_LENGTH:
                f.write(f"{split}{Config.new_line_tag}{Config.new_line_tag}\n")

              # If not then delete substring and start again
              substring = ""

      if args.delete:
        os.remove(file_path)
    except KeyboardInterrupt:
      print("user interrupt")
      sys.exit(1)
    except:
      pass

if args.delete:
  if os.path.exists(args.input) and os.path.isdir(args.input):
    finished = False
    while not finished:
      try:
        shutil.rmtree(args.input)
        finished = True
      except:
        time.sleep(0.1)
        pass