# git_repo.py
import os
import git
import logging

class Commit:
    """Represents a single commit with its metadata and diff."""

    def __init__(self, hash: str, author: str, date: str, message: str, repo: git.Repo):
        self.hash = hash
        self.author = author
        self.date = date
        self.message = message
        self.repo = repo
        self.status = False  # Add status attribute

    def __str__(self):
        """Returns a string representation of the Commit object."""
        return f"Commit(hash={self.hash}, author={self.author}, date={self.date}, message={self.message})"

    def diff(self, commit: git.Commit):
        return self.repo.git.diff(f'{self.hash}~1', f'{self.hash}')

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
        """Updates the commit message using Git commands."""
        try:
            # Amend the commit using repo.git.commit()
            self.repo.git.commit('--amend', '-m', new_message,
                                 author=f"{commit.author} <{commit.author}>")  # Use commit.author directly
            logging.info(f"Updated commit message for commit {commit.hash}")
        except Exception as e:
            logging.error(f"Error updating commit message for commit {commit.hash}: {e}")
            raise


