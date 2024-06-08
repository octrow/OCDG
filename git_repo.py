# git_repo.py
import os
import re

import git
import logging
import subprocess
from OCDG.utils import run_git_command

logger = logging.getLogger(__name__)


class Commit:
    """Represents a single commit with its metadata and diff."""

    def __init__(self, hash: str, author: str, date: str, message: str, repo: git.Repo):
        self.hash = hash
        self.author = author
        self.date = date
        self.message = message
        self.repo = repo
        self.diff = ""
        self.status = False  # Add status attribute

    def __str__(self):
        """Returns a string representation of the Commit object."""
        return f"Commit(hash={self.hash}, author={self.author}, date={self.date}, message={self.message})"

    def diff(self, commit: git.Commit):
        return self.repo.git.diff(f'{self.hash}~1', f'{self.hash}')

    def delete(self):
        del self

class GitAnalyzer:
    def __init__(self, repo_path="."):
        self.repo = git.Repo(repo_path)

    def get_repo_url(self):
        """Retrieves the remote repository URL."""
        remote_command = ["remote", "get-url", "origin"]
        try:
            return run_git_command(remote_command, self.repo.working_dir).strip()
        except RuntimeError as e:
            logger.error(f"Error retrieving repository URL: {e}", level="error")
            return None

    def get_commit_message(self, commit_hash: str) -> str | None:
        """Retrieves the commit message for a specific commit hash."""
        try:
            commit = self.repo.commit(commit_hash)
            return commit.message.strip()
        except Exception as e:
            logging.error(f"Error getting commit message for {commit_hash}: {e}")
            return None

    def get_commits(self, limit=None, since=None):
        """
        Retrieves commits with optional limit and since parameters.
        Diffs are NOT fetched at this stage.
        """
        # Initialize an empty list to store Commit objects
        commits = []
        # Define the Git log command to get commit information with diff
        # - "log": The basic Git command for showing commit history
        # - "--pretty=format:%H,%an <%ae>,%ad,%s": Specifies the format of output:
        #     - %H: Commit hash (SHA-1)
        #     - %an: Author name
        #     - %ae: Author email
        #     - %ad: Author date (short format)
        #     - %s: Commit subject (first line of the commit message)
        # - "--date=short": Display dates in short format (YYYY-MM-DD)
        # - "--patch": Include the diff of each commit
        log_command = [
            "log",
            "--pretty=format:%H,%an <%ae>,%ad,%s",
            "--date=short",
        ]
        if limit:
            log_command.append(f"-n {limit}")
        if since:
            log_command.append(f"--since={since}")
        # Execute the Git command and capture the output
        log_output = run_git_command(log_command, self.repo.working_dir)
        print(f"Log output length: {len(log_output)}")  # Check output length
        print(f"First 50 characters: {log_output[:50]}")  # Check output content
        # If the log output is empty (no commits), log a warning and return the empty list
        if not log_output:
            logging.warning(
                "Repository seems to be empty. No commits found."
            )
            return commits

        for line in log_output.splitlines():
            parts = line.split(",", maxsplit=3)
            commits.append(Commit(parts[0], parts[1], parts[2], parts[3], self.repo))

        return commits
        # for line in os.popen("git log --pretty=format:'%H,%an <%ae>,%ad,%s' --date=format:%Y-%m-%d").read().strip().split('\n'):
        #     hash, author, date, message = line.split(',', maxsplit=3)
        #     commits.append(Commit(hash, author, date, message, self.repo))
        # return commits

    def get_commit_diff(self, commit_hash: str):
        """Fetches the diff for a specific commit."""
        return self.repo.git.diff(f"{commit_hash}~1", f"{commit_hash}")

    def get_diff(self, commit):
        return commit.diff(commit.parents[0]).decode()

    def update_commit_message(self, commit, new_message):
        """Updates the commit message using Git commands."""
        try:
            # Create a temporary file with the new commit message
            with open('temp_commit_msg.txt', 'w') as temp_file:
                temp_file.write(new_message)

            # Use subprocess to run Git commands
            subprocess.run(['git', 'rebase', '-i', f'{commit.hash}~1'], cwd=self.repo.working_dir, check=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)  # Suppress output
            subprocess.run(['sed', '-i', f's/^pick {commit.hash}.*/reword {commit.hash}/',
                            os.path.join(self.repo.git_dir, 'rebase-merge', 'git-rebase-todo')], check=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)  # Suppress output
            # Simulate saving the 'git-rebase-todo' file
            with open(os.path.join(self.repo.git_dir, 'rebase-merge', 'git-rebase-todo'), 'w') as f:
                f.truncate()  # "Empty" the file (Git seems to expect this)

            subprocess.run(['git', 'rebase', '--continue'], cwd=self.repo.working_dir, check=True,
                           input=open('temp_commit_msg.txt', 'rb').read())

            # Remove the temporary file
            os.remove('temp_commit_msg.txt')
            # # Refresh Git index before amending
            # self.repo.git.add('.')
            #
            # # Amend the commit using repo.git.commit()
            # result = self.repo.git.commit('--amend', '-m', new_message,
            #                      author=f"{commit.author}")  # Use commit.author directly
            # # Check if the result is not an empty string, indicating success
            # if result != "":
            #     logging.info(f"Updated commit message for commit {commit.hash} with result: {result}")
            #     # Refresh Git index after amending commit
            #     self.repo.git.add('.')  # Add all changes to the index
            # else:
            #     logging.error(
            #         f"Failed to update commit message for commit {commit.hash}. Git command returned an empty result.")
            #     raise RuntimeError("Git commit amend failed.")
        except Exception as e:
            logging.error(f"Error updating commit message for commit {commit.hash}: {e}")
            raise


