import os
import re
import tempfile

from loguru import logger

from git_repo import Commit
from OCDG.utils import run_git_command, log_message


class CommitHistory:
    """Manages a collection of Commit objects."""

    def __init__(self):
        self.commits = []


    def get_commit(self, commit_hash):
        """Retrieves a specific commit by its hash."""
        for commit in self.commits:
            if commit.hash == commit_hash:
                return commit
        return None

    def get_oldest_commit(self):
        """Returns the oldest commit in the history."""
        return self.commits[-1]  # Assuming commits are ordered from newest to oldest

