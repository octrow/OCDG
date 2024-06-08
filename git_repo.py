# git_repo.py
import os
import git

from .commit import Commit

class GitAnalyzer:
    def __init__(self, repo_path="."):
        self.repo = git.Repo(repo_path)

    def get_commits(self):
        commits = []
        for line in os.popen("git log --pretty=format:'%h,%an,%ad,%s' --date=format:%Y-%m-%d").read().strip().split('\n'):
            hash, author, date, message = line.split(',', maxsplit=3)
            commits.append(Commit(hash, author, date, message, self.repo))
        return commits

    def get_diff(self, commit):
        return commit.diff(commit.parents[0]).decode()

    def update_commit_message(self, commit, new_message):
        # Implement logic to update commit message using Git commands
        pass

