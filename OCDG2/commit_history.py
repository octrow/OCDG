from utils import run_git_command

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

    def load_from_repo(self, repo_path):
        """Extracts commit history from the repository."""
        # Use git log to retrieve commit data
        log_command = ["log", "--pretty=format:%H|%an|%ad|%s", "--date=short", "--patch"]
        log_output = run_git_command(log_command, repo_path)

        # Parse the log output and create Commit objects
        current_commit = None
        for line in log_output.splitlines():
            if line.startswith("commit "):  # Start of a new commit
                if current_commit:
                    self.commits.append(current_commit)
                parts = line.split("|")
                current_commit = Commit(parts[0], parts[1], parts[2], parts[3], "")
            else:  # Part of the diff
                current_commit.diff += line + "\n"
        if current_commit:
            self.commits.append(current_commit)

    def get_commit(self, commit_hash):
        """Retrieves a specific commit by its hash."""
        for commit in self.commits:
            if commit.hash == commit_hash:
                return commit
        return None

    def get_oldest_commit(self):
        """Returns the oldest commit in the history."""
        return self.commits[-1]  # Assuming commits are ordered from newest to oldest
