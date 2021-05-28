import os
import sys
import time
from tqdm import tqdm
from git import rmtree

BLACKLIST_FOLDERS = [".git", ".venv", "__pycache__"]

def path_ends_with(path, ending):
  return path.endswith(ending) or path.endswith(rf"{ending}\\") or path.endswith(f"{ending}/")

def clean_folder_recursive(path:str="repos", tqdm_active:bool=True):
  if not os.path.exists(path) or not os.path.isdir(path): return

  iterator = tqdm(os.walk(path)) if tqdm_active else os.walk(path)
  unsuccess_deletes = []

  try:
    for dirpath, dirnames, filenames in iterator:
      if not path in dirpath:
        print(f"Something went wrong\nInvalid path {dirpath}")
        time.sleep(60)
        break

      # Delete any blacklisted folder rightaway
      if any([path_ends_with(dirpath, end) for end in BLACKLIST_FOLDERS]):
        try:
          rmtree(dirpath)
        except:
          unsuccess_deletes.append(dirpath)
        continue

      for f in filenames:
        full_path = os.path.join(dirpath, f)

        if not full_path.endswith("topics.txt") and not full_path.endswith(".py"):
          if not path in full_path:
            print(f"Something went wrong\nInvalid path {full_path}")
            time.sleep(60)
            break

          try:
            os.remove(full_path)
          except PermissionError:
            os.chmod(full_path, 0o777)
            os.remove(full_path)

    for uns_path in unsuccess_deletes:
      success = False
      while not success:
        try:
          rmtree(dirpath)
          success = True
        except:
          time.sleep(0.1)
          pass
  except KeyboardInterrupt:
    pass

if __name__ == '__main__':
  if len(sys.argv) == 2:
    assert os.path.exists(sys.argv[1]) and os.path.isdir(sys.argv[1]), "Invalid path to repos folder"
    clean_folder_recursive(sys.argv[1])
  else:
    print("Using default path to repos")
    clean_folder_recursive()