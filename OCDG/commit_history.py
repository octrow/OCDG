import os
import re

from loguru import logger

from utils import run_git_command, log_message

class Commit:
    """Represents a single commit with its metadata and diff."""

    def __init__(self, hash, author, date, message, diff):
        self.hash = hash
        self.author = author
        self.date = date
        self.message = message
        self.diff = diff
        self.new_message = None  # To be populated later


class CommitHistory:
    """Manages a collection of Commit objects and provides methods to access them."""

    def __init__(self):
        self.commits = []

    def get_repo_url(self, repo_path):
        """Retrieves the remote repository URL."""
        remote_command = ["remote", "get-url", "origin"]
        try:
            return run_git_command(remote_command, repo_path).strip()
        except RuntimeError as e:
            log_message(f"Error retrieving repository URL: {e}", level="error")
            return None

    def load_from_repo(self, repo_path):
        """Extracts commit history from the repository."""
        if repo_path.startswith(("http", "git@")):
            # Clone remote repository
            repo_name = repo_path.split("/")[-1].replace(".git", "")
            local_dir = os.path.join("repos", repo_name)
            if not os.path.exists(local_dir):
                clone_command = ["clone", repo_path, local_dir]
                run_git_command(clone_command)
            repo_path = local_dir
        repo_url = self.get_repo_url(repo_path)
        log_command = ["log", "--pretty=format:%H,%an,%ad,%s", "--date=short", "--patch"]
        logger.info(f"log_command: {log_command}")
        log_output = run_git_command(log_command, repo_path)
        logger.info(f"log_output: {log_output[0:50]}...")
        if not log_output:
            logger.warning("Repository seems to be empty. No commits found. Log output: %s", log_output)
            return  # Or raise an exception

        # Parse the log output and create Commit objects
        current_commit = None
        for line in log_output.splitlines():
            if re.match(r'^[a-f0-9]{40},', line):  # Start of a new commit
                if current_commit:
                    self.commits.append(current_commit)
                parts = line.split(",")
                current_commit = Commit(parts[0], parts[1], parts[2], parts[3], "")
            elif current_commit:  # Ensure current_commit is not None
                current_commit.diff += line + "\n"
        if current_commit:
            self.commits.append(current_commit)
        # if not self.commits:
        #     logger.warning("No commits found in the repository. Exiting...")
        #     return  # Or raise an exception

    def get_commit(self, commit_hash):
        """Retrieves a specific commit by its hash."""
        for commit in self.commits:
            if commit.hash == commit_hash:
                return commit
        return None

    def get_oldest_commit(self):
        """Returns the oldest commit in the history."""
        return self.commits[-1]  # Assuming commits are ordered from newest to oldest
