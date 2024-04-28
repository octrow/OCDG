# git_repo.py
import os
import git

class GitAnalyzer:
    def __init__(self, repo_path="."):
        self.repo = git.Repo(repo_path)

    def get_commits(self):
        # Implement logic to retrieve commits based on specified range or hashes
        return os.popen("git log --pretty=format:'%h,%an,%ad,%s' --date=format:%Y-%m-%d").read().strip().split('\n')

    def get_diff(self, commit):
        return commit.diff(commit.parents[0]).decode()

        # return os.popen(f"git diff {hash}^!").read()

    def update_commit_message(self, commit, new_message):
        # Implement logic to update commit message using Git commands
        pass

