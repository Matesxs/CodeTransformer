import github.GithubException
from github import Github
from tqdm import tqdm
import time
from datetime import datetime
import os
import multiprocessing
import subprocess
from clean_repos import clean_folder_recursive
import argparse
from config_loader import Config

parser = argparse.ArgumentParser()
parser.add_argument("--search", "-s", help="Search phrase (blank for all)", required=False, default=None, type=str)
parser.add_argument("--language", "-l", help="Language to search for", required=False, default="python", type=str)
parser.add_argument("--offset", "-O", help="Time offset in days", required=False, default=0, type=int)
parser.add_argument("--workers", "-w", help="Number of downloader workers", required=False, default=1, type=int)
parser.add_argument("--queue", "-q", help="Max repository queue length", required=False, default=50, type=int)
parser.add_argument("--max_repo_size", "-M", help="Maximum size of repository to clone in MB", required=False, default=500, type=int)
parser.add_argument("--clear", "-c", help="Clean downloaded repository rightaway", action="store_true")
parser.add_argument("--blacklist", "-b", help="Blacklisted names separated by ;", required=False, default="hack;test", type=str)
parser.add_argument("--debug", "-d", help="Show more info about cloned repositories", action="store_true")

args = parser.parse_args()

NUM_OF_WORKERS = args.workers
MAX_QUEUE_SIZE = args.queue

DAYS_BACK_OFFSET = args.offset
QUERY_BASE = f"{args.search} language:{args.language}" if args.search else f"language:{args.language}"
MAX_REPO_SIZE_MB = args.max_repo_size

BLACKLIST_PHRASES = args.blacklist.split(";")

git = Github(Config.github_token)

end_time = time.time() - DAYS_BACK_OFFSET * 86400
start_time = end_time - 86400

if not os.path.exists("repos"): os.mkdir("repos")

class WorkerProcess(multiprocessing.Process):
  def __init__(self, queue, repos_in_progress, repos_in_progress_access_lock, blacklist_repos, blacklist_repos_lock) -> None:
    super(WorkerProcess, self).__init__()
    self.daemon = True

    self.queue = queue
    self.repos_in_progress = repos_in_progress
    self.repos_in_progress_access_lock = repos_in_progress_access_lock
    self.blacklist_repos = blacklist_repos
    self.blacklist_repos_lock = blacklist_repos_lock

  def run(self) -> None:
    while True:
      pld = None
      clone_process = None

      try:
        pld = self.queue.get()

        if isinstance(pld, list):
          clone_process = subprocess.Popen(['git', 'clone', str(pld[1]), str(pld[0])], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
          clone_process.wait(Config.clone_timeout_seconds)

          clone_process = None

          # Clean data rightaway
          if args.clear:
            clean_folder_recursive(str(pld[0]), False)
        else:
          print("Invalid payload arrived")
      except KeyboardInterrupt:
        break
      except subprocess.TimeoutExpired:
        # Clone failed / too long
        self.blacklist_repos_lock.acquire()
        self.blacklist_repos.append(str(pld[0]))
        self.blacklist_repos_lock.release()
      finally:
        if pld:
          self.repos_in_progress_access_lock.acquire()
          self.repos_in_progress.remove(str(pld[0]))
          self.repos_in_progress_access_lock.release()

        if clone_process:
          clone_process.kill()

if __name__ == '__main__':
  # List of blacklisted repos
  blacklist_repos = []

  # Create task queue for workers
  manager = multiprocessing.Manager()
  repos_in_progress_access_lock = manager.Lock()
  repos_in_progress = manager.list()
  blacklist_repos = manager.list()
  blacklist_repos_lock = manager.Lock()
  work_queue = manager.Queue(maxsize=MAX_QUEUE_SIZE)

  # Create downloader processes
  workers = [WorkerProcess(work_queue, repos_in_progress, repos_in_progress_access_lock, blacklist_repos, blacklist_repos_lock) for _ in range(NUM_OF_WORKERS)]
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

      number_of_repositories = repositories.totalCount
      print(f"\nFound {number_of_repositories} repos")
      print(f"Workers allive: {len([worker for worker in workers if worker.is_alive])}")
      if not args.debug:
        print(f"Current time: {start_time_str} - {end_time_str} ({DAYS_BACK_OFFSET + i} DBO)")

      try:
        for repository in tqdm(repositories, total=number_of_repositories, unit="rep"):
          # Slow down request calls
          time.sleep(Config.github_req_delay)

          repo_name = repository.name
          owner_login = repository.owner.login.replace('.', '').replace('/', '')
          repo_path = f"repos/{owner_login}/{repo_name}"

          if args.debug:
            print(f"\nCurrent time: {start_time_str} - {end_time_str} ({DAYS_BACK_OFFSET + i} DBO)")
            print(f"Repository: {owner_login}/{repo_name}")

          # Check if this repo isnt already downloaded or in queue for download
          repos_in_progress_access_lock.acquire()
          repo_in_progress = repo_path in repos_in_progress
          repos_in_progress_access_lock.release()

          if os.path.exists(repo_path) or repo_in_progress:
            if args.debug:
              print("Repository already downloaded")
            continue

          # Check if this repo is not on blacklost (to save some github api calls)
          blacklist_repos_lock.acquire()
          repo_in_blacklist = repo_path in blacklist_repos
          blacklist_repos_lock.release()
          if repo_in_blacklist:
            if args.debug:
              print("Repository already on blacklist")
            continue

          # Check if repo name dont contain any blacklist phrase
          blplut = [(p in repo_name) for p in BLACKLIST_PHRASES]
          if any(blplut):
            #print("Repository on blacklist")
            blacklist_repos_lock.acquire()
            blacklist_repos.append(repo_path)
            blacklist_repos_lock.release()
            continue

          # Get size of repo
          repo_size = repository.size / 1000
          if args.debug:
            print(f"Repository size: {repo_size}MB")

          # Ignore too large repos (some still could pass because they can have some other github repos as dependency)
          if repo_size > MAX_REPO_SIZE_MB:
            if args.debug:
              print(f"Repository too large")

            blacklist_repos_lock.acquire()
            blacklist_repos.append(repo_path)
            blacklist_repos_lock.release()
            continue

          # Append repo to work queue
          repos_in_progress_access_lock.acquire()
          repos_in_progress.append(repo_path)
          repos_in_progress_access_lock.release()

          work_queue.put([repo_path, repository.clone_url])
      except github.RateLimitExceededException:
        print("\nGithub pull limit exceeded\nWaiting")
        for _ in tqdm(range(Config.error_delay_seconds), unit="s"): time.sleep(1)

      i += 1
    except KeyboardInterrupt:
      print("User interrupt")
      break
    except github.RateLimitExceededException:
      print("\nGithub pull limit exceeded\nWaiting")
      for _ in tqdm(range(Config.error_delay_seconds), unit="s"): time.sleep(1)
    except Exception as e:
      print(f"\nSomething went wrong\n{e}\nWaiting")
      for _ in tqdm(range(Config.error_delay_seconds), unit="s"): time.sleep(1)

  for worker in workers:
    if worker.is_alive():
      worker.kill()
      worker.join()

  if args.clear:
    print("\nCleaning repositories")
    clean_folder_recursive("repos", True)