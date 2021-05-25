import github.GithubException
from github import Github
import time
from datetime import datetime
import os
from multiprocessing import Process, JoinableQueue
import subprocess
from clean_repos import clean_folder_recursive
import argparse
from config import GITHUB_APP_TOKEN

parser = argparse.ArgumentParser()
parser.add_argument("--search", "-s", help="Search phrase (blank for all)", required=False, default=None, type=str)
parser.add_argument("--language", "-l", help="Language to search for", required=False, default="python", type=str)
parser.add_argument("--offset", "-o", help="Time offset in days", required=False, default=0, type=int)
parser.add_argument("--workers", "-w", help="Number of downloader workers", required=False, default=1, type=int)
parser.add_argument("--queue", "-q", help="Max repository queue length", required=False, default=50, type=int)
parser.add_argument("--max_repo_size", "-M", help="Maximum size of repository to clone in MB", required=False, default=500, type=int)
parser.add_argument("--clear", "-c", help="Clean downloaded repository rightaway", action="store_true")
parser.add_argument("--blacklist", "-b", help="Blacklisted names separated by ;", required=False, default="hack;test", type=str)

args = parser.parse_args()

NUM_OF_WORKERS = args.workers
MAX_QUEUE_SIZE = args.queue

DAYS_BACK_OFFSET = args.offset
QUERY_BASE = f"{args.search} language:{args.language}" if args.search else f"language:{args.language}"
MAX_REPO_SIZE_MB = args.max_repo_size

BLACKLIST_PHRASES = args.blacklist.split(";")

git = Github(GITHUB_APP_TOKEN)

end_time = time.time() - DAYS_BACK_OFFSET * 86400
start_time = end_time - 86400

if not os.path.exists("repos"): os.mkdir("repos")

def download_repo(queue:JoinableQueue):
  while True:
    pld = None

    try:
      pld = queue.get()

      if isinstance(pld, list):
        subprocess.call(['git', 'clone', str(pld[1]), str(pld[0])], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

        # Clean data rightaway
        if args.clear:
          clean_folder_recursive(str(pld[0]), False)
      else:
        print("Invalid payload arrived")
    except KeyboardInterrupt:
      break
    finally:
      if pld: queue.task_done()

if __name__ == '__main__':
  # List of blacklisted repos
  blacklist_repos = []

  # Create task queue for workers
  work_queue = JoinableQueue(maxsize=MAX_QUEUE_SIZE)

  # Create downloader processes
  workers = [Process(target=download_repo, args=(work_queue,), daemon=True) for _ in range(NUM_OF_WORKERS)]
  for worker in workers:
    worker.start()

  i = 0
  while True:
    try:
      start_time_str = datetime.utcfromtimestamp(start_time).strftime("%Y-%m-%d")
      end_time_str = datetime.utcfromtimestamp(end_time).strftime("%Y-%m-%d")

      query = f"{QUERY_BASE} created:{start_time_str}..{end_time_str}"
      repositories = git.search_repositories(query)

      end_time -= 86400
      start_time -= 86400

      print(f"Found {repositories.totalCount} repos")

      tmp_repos = []

      try:
        for repository in repositories:
          # Slow down request calls
          time.sleep(0.1)

          repo_name = repository.name
          owner_login = repository.owner.login.replace('.', '').replace('/', '')
          repo_path = f"repos/{owner_login}/{repo_name}"

          print(f"\nCurrent time: {start_time_str} - {end_time_str} ({DAYS_BACK_OFFSET + i} DBO)")
          print(f"Repository: {owner_login}/{repo_name}")

          if os.path.exists(repo_path) or repo_path in tmp_repos:
            print("Repository already downloaded")
            continue

          if repo_path in blacklist_repos:
            print("Repository already on blacklist")
            continue

          blplut = [(p in repo_name) for p in BLACKLIST_PHRASES]
          if any(blplut):
            print("Repository on blacklist")
            blacklist_repos.append(repo_path)
            continue

          repo_size = repository.size / 1000
          print(f"Repository size: {repo_size}MB")

          if repo_size > MAX_REPO_SIZE_MB:
            print(f"Repository too large")
            blacklist_repos.append(repo_path)
            continue

          tmp_repos.append(repo_path)
          work_queue.put([repo_path, repository.clone_url])
      except github.RateLimitExceededException:
        print("\nGithub pull limit exceeded")
        time.sleep(120)

      print(f"\nWaiting for batch of {len(tmp_repos)} repositories to finish cloning")
      work_queue.join()

      i += 1
    except KeyboardInterrupt:
      print("User interrupt")
      break
    except github.RateLimitExceededException:
      print("\nGithub pull limit exceeded")
      time.sleep(120)
    except Exception as e:
      print(f"\nSomething went wrong\n{e}")
      time.sleep(120)

  for worker in workers:
    if worker.is_alive():
      worker.kill()

  if args.clear:
    print("\nCleaning repositories")
    clean_folder_recursive("repos", True)