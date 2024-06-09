import argparse
import json
import os
import logging
import re
import subprocess
import tempfile
import traceback
from typing import Any, List, Dict

from loguru import logger
import git

from clients import create_client
from config import load_configuration

# Global variable to store log file path
COMMIT_MESSAGES_LOG_FILE = "commit_messages.log"

# Define file/folder paths and patterns to ignore ENTIRE SECTIONS
IGNORED_SECTION_PATTERNS = {
    r'venv.*',  # Ignore any path containing 'venv'
    r'.idea.*'  # Ignore any path containing '.idea'
    r'node_modules.*',  # Ignore any path containing 'node_modules'
    r'__pycache__.*',  # Ignore any path containing '__pycache__
}

# Define file extensions and patterns to ignore
IGNORED_LINE_PATTERNS = {
    r'.*\.(png|jpg|jpeg|gif|bmp|tiff|svg|ico|raw|psd|ai)$',
    r'.*\.(xlsx|xls|docx|pptx|pdf)$', r'.*\.(pack|idx|DS_Store|sys|ini|bat|plist)$',
    r'.*\.(exe|dll|so|bin)$', r'.*\.(zip|rar|7z|tar|gz|bz2)$',
    r'.*\.(mp3|wav|aac|flac)$', r'.*\.(mp4|avi|mov|wmv|flv)$',
    r'.*\.(db|sqlitedb|mdb)$', r'.*\.(ttf|otf|woff|woff2)$',
    r'.*\.(tmp|temp|swp|swo)$', r'.*\.(o|obj|pyc|class)$',
    r'.*\.(cer|pem|crt|key)$', r'.*\.(conf|cfg|config)$',
    r'.*\.(env)$', r'node_modules', r'.*\.(pyo)$',
    r'(package-lock\.json|poetry\.lock|yarn\.lock|Gemfile\.lock)',
    r'.*\.(err|stderr|stdout|log)$', r'.*\.(cache|cached)$'
}

def user_confirms_rewrite(commit_history):
    """Presents the proposed changes to the user and asks for confirmation."""
    print("\nThe following commit messages will be rewritten:")
    print("-" * 80)
    for commit in commit_history.commits:
        if commit.new_message:
            print(f"Commit: {commit.hash} (Author: {commit.author})")
            print(f"Old: {commit.message}")
            print(f"New: {commit.new_message}")
            print("-" * 80)

    while True:
        confirmation = input("Do you want to rewrite these commit messages? (yes/no): ").lower()
        if confirmation in ("yes", "y"):
            return True
        elif confirmation in ("no", "n"):
            return False
        else:
            print("Invalid input. Please enter 'yes' or 'no'.")

class RepositoryUpdater:
    """Handles safe rewriting of commit messages."""

    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.refs_backup_file = os.path.join(self.repo_path, ".git", "refs_backup")

    def backup_refs(self):
        """Backs up refs using git for-each-ref to a file."""
        try:
            run_git_command(
                [
                    "for-each-ref",
                    "--format='%(refname)'",
                    "refs/heads/",
                    "refs/remotes/",
                    "refs/tags/",
                    ">",
                    self.refs_backup_file,
                ],
                self.repo_path,
            )
            logging.info("Backed up refs to '.git/refs_backup'")
        except Exception as e:
            logging.error(f"Error backing up refs: {e}")
            raise

    def restore_refs(self):
        """Restores refs from the backup file."""
        try:
            if not os.path.exists(self.refs_backup_file):
                logging.warning(
                    f"Refs backup file '{self.refs_backup_file}' not found. Skipping restore."
                )
                return
            run_git_command(
                ["update-ref", "--stdin", "<", self.refs_backup_file], self.repo_path
            )
            logging.info("Restored refs from backup.")
        except Exception as e:
            logging.error(f"Error restoring refs: {e}")
            raise
        finally:
            # Clean up the backup file after restore attempt
            if os.path.exists(self.refs_backup_file):
                os.remove(self.refs_backup_file)

    def rewrite_commit_messages(self, commit_history):
        """Rewrites commit messages using git filter-branch."""
        with tempfile.TemporaryDirectory() as temp_dir:
            filter_script_path = os.path.join(temp_dir, "filter_script.py")
            self.generate_filter_script(commit_history, filter_script_path)

            try:
                self.backup_refs()  # Backup before rewriting!

                filter_branch_cmd = [
                    "filter-branch",
                    "-f",
                    "--msg-filter",
                    f"python {filter_script_path}",
                    "--tag-name-filter",
                    "cat",
                    "--",
                    "HEAD",
                ]
                run_git_command(filter_branch_cmd, self.repo_path)
                logging.info("Commit messages rewritten successfully.")

            except Exception as e:
                logging.error(f"Error rewriting commit messages: {e}")
                self.restore_refs()  # Attempt restore on error
                raise
            finally:
                backup_file = os.path.join(self.repo_path, ".git/refs_backup")
                if os.path.exists(backup_file):
                    os.remove(backup_file)

    def generate_filter_script(self, commit_history, script_path):
        """Generates the Python script for git filter-branch."""
        with open(script_path, "w") as f:
            f.write(
                """
import sys

def filter_message(message):
    message_map = {
"""
            )
            for commit in commit_history.commits:
                if commit.new_message:
                    # Properly escape single quotes in new_message
                    escaped_message = commit.new_message.replace("'", r"\'")
                    f.write(f"        '{commit.hash}': '{escaped_message}',\n")
            f.write(
                """
    }
    commit_hash = sys.stdin.readline().strip()
    return message_map.get(commit_hash, message)

if __name__ == "__main__":
    print(filter_message(sys.stdin.readline().strip()))
"""
            )


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


def save_commit_messages_to_log(commit_history: CommitHistory):
    """Saves old and new commit messages to the log file."""
    try:
        with open(COMMIT_MESSAGES_LOG_FILE, "a") as log_file:
            for commit in commit_history.commits:
                if commit.new_message:
                    log_file.write(f"Commit: {commit.hash}\n")
                    log_file.write(f"Old Message: {commit.message}\n")
                    log_file.write(f"New Message: {commit.new_message}\n\n")
        logging.info(f"Old and new commit messages saved to '{COMMIT_MESSAGES_LOG_FILE}'")
    except Exception as e:
        logging.error(f"Failed to save commit messages to log file: {e}")

def filter_diff(diff: str) -> str:
    """Removes unwanted lines from the diff based on file extensions and patterns."""
    filtered_lines = []
    skip_section = False  # Flag to skip entire diff sections

    for line in diff.splitlines():
        # Section-Level Filtering
        if line.startswith('diff --git '):
            # Check if the section should be skipped
            if any(re.search(pattern, line) for pattern in IGNORED_SECTION_PATTERNS):
                skip_section = True
                logging.info(f"Skipping section: {line}")
                continue # Skip to the next line
            else:
                skip_section = False  # Reset the flag for the new section
                filtered_lines.append(line) # Add the 'diff --git' line if not skipped
        else:
            # Only add lines if not skipping the section
            if not skip_section and not any(re.search(pattern, line) for pattern in IGNORED_LINE_PATTERNS):
                filtered_lines.append(line)

    return "\n".join(filtered_lines)



def run_git_command(command, repo_path="."):
    """Executes a Git command and returns the output."""
    logger.debug(f"Running git command: git {command}")
    result = subprocess.run(["git"] + command, cwd=repo_path, capture_output=True, text=True, check=True, encoding="cp437", timeout=10)
    try:
        # result = subprocess.run(["git"] + command, cwd=repo_path, capture_output=True, text=True, check=True, timeout=10)
        result.check_returncode()
        output = result.stdout
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Git command failed: {e.stderr}") from e
    except UnicodeDecodeError:
        # If decoding as UTF-8 fails, try decoding as ISO-8859-1 (Latin-1) instead
        output = result.stdout.decode('ISO-8859-1')
    return output


def validate_repo_path(repo_path):
    """Checks if the provided path is a valid Git repository."""
    if not os.path.isdir(repo_path):
        raise ValueError(f"Invalid repository path: {repo_path}")
    try:
        run_git_command(["rev-parse", "--is-inside-work-tree"], repo_path)
    except RuntimeError:
        raise ValueError(f"{repo_path} is not a valid Git repository.")


# def parse_output_string(output_string: str) -> dict:
#     """Parses the output string generated by the AI model into a dictionary."""
#     data = {}
#     patterns = {
#         'short_analysis': r'\*\*Short analysis\*\*: (.+?)\n',
#         'commit_title': r'\*\*New Commit Title\*\*: (.+?)\n',
#         'detailed_commit_message': r'\*\*New Detailed Commit Message\*\*:\n(.+?)\n\n\*\*Code Changes\*\*:',
#         'code_changes': r'\*\*Code Changes\*\*:\n```\n(\{.+\})\n```'
#     }
#
#     for key, pattern in patterns.items():
#         match = re.search(pattern, output_string, re.DOTALL)
#         if match:
#             if key == 'code_changes':
#                 try:
#                     data[key] = json.loads(match.group(1))
#                 except json.JSONDecodeError as e:
#                     logger.error(f"Error decoding JSON: {e} - {match.group(1)}")
#                     return {}
#             else:
#                 data[key] = match.group(1).strip()
#     return data


def _split_text_at_boundaries(text, max_chunk_size=7900):
    """Splits text into chunks, attempting to break at code block boundaries."""
    logger.info(f"Splitting text into chunks, attempting to break at code block boundaries...")
    logger.debug(f"Full text being split: \n{text}\n") # Print the full diff for inspection
    try:
        # Define a regular expression to find code block boundaries
        code_block_boundary = re.compile(r'```(?:\w+)?\n')  # Matches "```" followed by optional language specifier

        chunks = []
        current_chunk = ""
        last_split_index = 0
        for match in code_block_boundary.finditer(text):
            end_index = match.start()
            chunk = text[last_split_index:end_index]

            # FIX: The logic here was flawed.
            # It should append 'current_chunk' even if adding 'chunk' exceeds the limit.
            # Then, it should start a new 'current_chunk' with the exceeding 'chunk'
            if len(current_chunk) + len(chunk) > max_chunk_size:
                chunks.append(current_chunk) # Append even if adding 'chunk' goes over
                current_chunk = chunk # Start a new chunk with the exceeding part
            else:
                current_chunk += chunk

            last_split_index = end_index

        # Add the remaining text after the last code block
        current_chunk += text[last_split_index:]
        if current_chunk:
            chunks.append(current_chunk)

        # Log chunk sizes
        logger.info(f"Split text into {len(chunks)} chunks.")
        for i, chunk in enumerate(chunks):
            logger.debug(f"Chunk {i+1} size: {len(chunk)} characters")

        return chunks
    except Exception as e:
        logger.error(f'Error in split text at boundaries: {e}')
        raise


def _split_diff_intelligently(diff, max_chunk_size=7900, min_chunk_size=1000):
    """Splits a large diff intelligently, first trying logical boundaries then fallback to aggressive."""
    try:
        logger.info(f"Splitting diff into chunks, trying to preserve logical boundaries...")

        # First, attempt to split at code block boundaries
        chunks = _split_text_at_boundaries(diff, max_chunk_size)

        # If no logical splits were found or chunks are too small, use a more aggressive splitting
        if len(chunks) <= 1 or any(len(chunk) < min_chunk_size for chunk in chunks):
            logger.info(f"No logical splits found or chunks too small. Using aggressive splitting...")
            chunks = list(_split_text_aggressively(diff, max_chunk_size))  # Convert to list

        logger.info(f"Split diff into {len(chunks)} final chunks.")
        return chunks
    except Exception as e:
        logger.error(f'Error in split diff intelligently: {e}')
        raise


def _split_text_aggressively(text, max_chunk_size=7900, overlap=200):
    """Yields chunks of text with overlap."""
    logger.info(f"Splitting text aggressively into chunks of at most {max_chunk_size}"
                f" characters with {overlap} overlap...")
    try:
        start_index = 0
        while start_index < len(text):
            end_index = min(start_index + max_chunk_size, len(text))
            newline_index = text.rfind('\n', start_index, end_index)
            if newline_index != -1:
                end_index = newline_index + 1
            yield text[start_index:end_index]
            start_index = end_index
    except Exception as e:
        logger.error(f'Error in split text aggressively: {e}')
        raise

def _generate_single_commit_message_json(
    diff_chunk: str,
    commit_message: str,
    client: Any,
    model: str,
    chunk_index: int,
    total_chunks: int,
) -> Dict[str, str]:
    """
    Generates a single commit message in JSON format, handling potential JSON decoding errors.
    """
    system_prompt = (
        f""""
        You are a helpful AI assistant that generates commit messages based on code changes and previous descriptions. Follow the commit guidelines of the GitHub repository.
        Previous commit message: {commit_message}
        Code changes: {'(partial)' if chunk_index != total_chunks - 1 else ''} 
        ```
        {diff_chunk}
        ```
        Generate a new commit message based on these changes. Output only in JSON Format, without any additional text or code blocks.
        {{
        "Short analysis": "str",
        "New Commit Title": "str",
        "New Detailed Commit Message": "str",
        "Code Changes": {{"filename": "str", "filename2": "str"}}
        }}
        """
    )
    chat_completion = client.generate_text(system_prompt, model=model)
    try:
        # Extract JSON using a regular expression
        json_match = re.search(r'\{.*\}', chat_completion, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        else:
            logger.error(f"No valid JSON found in response: {chat_completion}")
            return {}
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON: {e} - {chat_completion}")
        return {}

def _generate_commit_message_parts(diff: str, commit_message: str, client: Any, model: str, chunk_size=7900) -> List[Dict[str, str]]:
    """Splits a diff into chunks and generates a commit message for each chunk."""
    logger.info("Split diff into chunks")
    try:
        diff_chunks = [diff[i:i + chunk_size] for i in range(0, len(diff), chunk_size)]
        # diff_chunks = _split_diff_intelligently(diff, chunk_size)
        commit_messages = []
        # Create an iterator from the generator
        for i, diff_chunk in enumerate(diff_chunks):
            commit_messages.append(
                _generate_single_commit_message_json(
                    diff_chunk, commit_message, client, model, i, len(diff_chunks)
                )
            )
        logger.success(f"Generated {len(commit_messages)} commit messages.")
        return commit_messages
    except Exception as e:
        logger.error(f'Error in generate commit multi: {e}')
        raise


def combine_messages(multi_commit: List[Dict[str, str]], client: Any, model: str) -> dict:
    """Combines multiple commit messages into a single commit message."""
    prompt = f"""Combine the following messages into a single commit message in JSON format:
    ```json
    {json.dumps(multi_commit)}
    ```
    Output only in JSON Format, without any additional text or code blocks.
    {{
    "Short analysis": "str",
    "New Commit Title": "str",
    "New Detailed Commit Message": "str",
    "Code Changes": {{"filename": "str", "filename2": "str"}}
    }}
    """
    combined_message = client.generate_text(
        prompt,
        model=model
    )
    try:
        # Extract JSON using a regular expression
        json_match = re.search(r'\{.*\}', combined_message, re.DOTALL)
        if json_match:
            logger.success(f"Combined messages: {json_match.group(0)}")
            return json.loads(json_match.group(0))
        else:
            logger.error(f"No valid JSON found in response: {combined_message}")
            return {}
        # return json.loads(combined_message)
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON: {e} - {combined_message}")
        return {}


# Simplified generate_commit_description
def generate_commit_description(diff: str, old_description: str, client: Any, model: str) -> str | None:
    """Generates a commit description for a potentially large diff."""
    try:
        if len(diff) >= 7900:
            logger.info("Diff is too long. Start splitting it into chunks.")
            multi_commit = _generate_commit_message_parts(diff, old_description, client, model)
            if not multi_commit:
                logger.warning("Failed to generate multi-commit message. Skipping...")
                return None
            generated_message = combine_messages(multi_commit, client, model)
        else:
            generated_message = _generate_single_commit_message_json(
                diff, old_description, client, model, 0, 1
            )
        # FIX: Moved the .strip() to the end of the joined string
        new_description = "\n".join(
            [
                generated_message.get("New Commit Title", ""),
                "",  # Add an empty line between title and body
                generated_message.get("New Detailed Commit Message", ""),
            ]
        ).strip()

        # Check if new_description is not empty
        if new_description:
            logger.success(f"Generated commit message: {new_description}")
            return new_description
        else:
            logger.warning("Generated commit message is empty. Skipping commit.")
            return None
    except Exception as e:
        logger.error(f"Error generating commit description: {e}")
        return None


class Commit:
    """Represents a single commit with its metadata and diff."""

    def __init__(self, hash: str, author: str, date: str, message: str, repo: git.Repo):
        self.hash = hash
        self.author = author
        self.date = date
        self.message = message
        self.repo = repo
        self.diff = ""
        self.new_message = None  # Add new_message attribute
        # self.status = False  # Add status attribute

    def __str__(self):
        """Returns a string representation of the Commit object."""
        return f"Commit(hash={self.hash}, author={self.author}, date={self.date}, message={self.message})"

    def get_diff(self):
        """Fetches the diff for this commit."""
        return self.repo.git.diff(f"{self.hash}~1", f"{self.hash}")


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
            commit = Commit(parts[0], parts[1], parts[2], parts[3], self.repo)
            commits.append(commit)  # Add commit without fetching diff

        return commits

    def get_commit_diff(self, commit_hash: str, commit: Commit):
        """Fetches the diff for a specific commit."""
        return self.repo.git.diff(f"{commit_hash}~1", f"{commit.hash}")
    #
    # def get_diff(self, commit):
    #     return commit.diff(commit.parents[0]).decode()

    def update_commit_message(self, commit, new_message):
        """Updates the commit message using Git commands."""
        try:
            # Create a temporary file with the new commit message
            with open('temp_commit_msg.txt', 'w') as temp_file:
                temp_file.write(new_message)

            # Use subprocess to run Git commands
            subprocess.run(['git', 'rebase', '-i', f'{commit.hash}~1'], cwd=self.repo.working_dir, check=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)  # Suppress output
            subprocess.run(['sed', '-i', f's/^pick {commit.hash}.*/reword {commit.hash}/',
                            os.path.join(self.repo.git_dir, 'rebase-merge', 'git-rebase-todo')], check=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)  # Suppress output
            # Simulate saving the 'git-rebase-todo' file
            with open(os.path.join(self.repo.git_dir, 'rebase-merge', 'git-rebase-todo'), 'w') as f:
                f.truncate()  # "Empty" the file (Git seems to expect this)

            subprocess.run(['git', 'rebase', '--continue'], cwd=self.repo.working_dir, check=True,
                           input=open('temp_commit_msg.txt', 'rb').read(), timeout=10)
            # Remove the temporary file
            os.remove('temp_commit_msg.txt')
        except Exception as e:
            logging.error(f"Error updating commit message for commit {commit.hash}: {e}")
            raise


# def update_repository(repo_path, commit_history):
#     """Updates commit messages in the repository using git filter-branch."""
#     # Create a temporary directory for the filter script
#     with tempfile.TemporaryDirectory() as temp_dir:
#         filter_script_path = os.path.join(temp_dir, "filter_script.py")
#
#         # Generate and save the filter script
#         generate_filter_script(commit_history, filter_script_path)
#
#         # Backup refs before running filter-branch
#         run_git_command(["for-each-ref", "--format='%(refname)'", "refs/heads/", "refs/remotes/", "refs/tags/", ">",
#                          ".git/refs_backup"], repo_path)
#
#         try:
#             # Run git filter-branch with the filter script
#             filter_branch_cmd = ["filter-branch", "-f", "--msg-filter", f"python {filter_script_path}",
#                                  "--tag-name-filter", "cat", "--", "HEAD"]
#             run_git_command(filter_branch_cmd, repo_path)
#         except Exception as e:
#             logger.error(f"Error updating repository: {e}", level="error")
#             # Restore refs from backup
#             run_git_command(["update-ref", "--stdin", "<", ".git/refs_backup"], repo_path)
#             raise
#
#         # Remove backup file
#         os.remove(os.path.join(repo_path, ".git/refs_backup"))
#         logger.info("Repository update completed.", level="info")
#

# def generate_filter_script(commit_history, script_path):
#     """Generates the filter script to replace commit messages."""
#     with open(script_path, "w") as f:
#         f.write("""
# import sys
#
# def filter_message(message):
#     # Mapping of old commit hashes to new messages
#     message_map = {
# """)
#         for commit in commit_history.commits:
#             f.write(f"        '{commit.hash}': '{commit.new_message}',\n")
#         f.write("""
#     }
#
#     commit_hash = sys.stdin.readline().strip()
#     return message_map.get(commit_hash, message)
#
# if __name__ == "__main__":
#     print(filter_message(sys.stdin.readline().strip()))
# """)

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Revitalize old commit messages using LLMs.")
    parser.add_argument("repo_path", help="Path to the Git repository (local path or URL).")
    parser.add_argument("-b", "--backup_dir",
                        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "backup"),
                        help="Directory for repository backup.")
    parser.add_argument("-l", "--llm", choices=["openai", "groq", "replicate"], default="openai", help="Choice of LLM.")
    parser.add_argument("-m", "--model", default="meta/llama3-70b-instruct", help="Choice of LLM model.")
    parser.add_argument("-f", "--force-push", action="store_true", help="Force push to remote after rewrite.")
    parser.add_argument(
        "-r",
        "--restore",
        action="store_true",
        help="Restore refs from backup before proceeding.",
    )
    # Add more arguments as needed...
    args = parser.parse_args()

    # Configure logging
    # logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    # Load configuration
    config = load_configuration()
    os.makedirs(config['COMMIT_DIFF_DIRECTORY'], exist_ok=True)

    # Determine repository type and get URL
    if args.repo_path.startswith(("http", "git@")):
        repo_url = args.repo_path
        repo_path = os.path.join(config['COMMIT_DIFF_DIRECTORY'], os.path.basename(repo_url).replace(".git", ""))
        # Clone if the directory doesn't exist
        if not os.path.exists(repo_path):
            logging.info(f"Cloning remote repository to {repo_path}")
            git.Repo.clone_from(repo_url, repo_path)
    else:
        # Get absolute path for local repositories
        repo_path = os.path.abspath(args.repo_path)
        logging.info(f"Using local repository path: {repo_path}")
        repo_url = GitAnalyzer.get_repo_url(repo_path)
        if not repo_url:
            logging.error("Failed to get repository URL from local path. Exiting...")
            return

    # 1. Backup Repository
    updater = RepositoryUpdater(repo_path)
    # Restore from backup if requested
    if args.restore:
        try:
            print("Attempting to restore refs from backup...")
            updater.restore_refs()
            print("Restore complete. Exiting.")
            return  # Exit after restore
        except Exception as e:
            logging.critical(f"Error during restore: {e}")
            return  # Exit on restore error
    # BACKUP REFS IMMEDIATELY AFTER LOADING REPOSITORY
    try:
        logging.info("Backing up refs before any operations...")
        updater.backup_refs()
    except Exception as e:
        logging.critical(f"Error during initial backup: {e}")
        return  # Exit on backup error

    # 2. Load Commit History
    logging.info("Loading commit history...")
    try:
        analyzer = GitAnalyzer(repo_path)
        commits = analyzer.get_commits() # Now get commits with diffs
        # Get the repo object from the analyzer
        repo = analyzer.repo

        commit_history = CommitHistory()
        commit_history.commits = commits  # Assign the commits to the history object
        counter = 0
        for commit in commits:
            logger.info(f"Commit {counter}: {commit.hash}")
            counter += 1
    except Exception as e:
        logging.error(f"Failed to load commit history: {e}")
        return

    logging.info(f"Loaded {len(commits)} commits from repository.")

    # 3. Initialize LLM Interface
    client = create_client(args.llm, config)
    logging.info(f"Initialized LLM client: {client}")

    # 4. Process each commit
    initial_commit_hash = run_git_command(['rev-list', '--max-parents=0', 'HEAD'], repo_path).strip()
    for i, commit in enumerate(commits):
        logging.info(f"Processing commit {i + 1}/{len(commits)}: {commit.hash}")
        try:
            if commit.hash == initial_commit_hash:
                logging.info(f"Skipping diff for initial commit: {commit.hash}")
                diff = ""  # Or handle the initial commit differently
            else:
                diff = analyzer.get_commit_diff(commit.hash, commit) # Fetch diff here
            filtered_diff = filter_diff(diff)
            new_message = generate_commit_description(
                filtered_diff, commit.message, client, args.model
            )

            if new_message is None:
                logging.warning(
                    f"Skipping commit {commit.hash} - No new message generated"
                )
                continue

            commit.new_message = new_message  # Store the new message

        except Exception as e:
            logging.error(
                f"Error processing commit {commit.hash}: {traceback.format_exc()} {e}"
            )
            return

    # 5. User Confirmation before Rewrite
    if user_confirms_rewrite(commit_history):
        # updater = RepositoryUpdater(repo_path)
        try:
            logging.info("Rewriting commit messages...")
            save_commit_messages_to_log(commit_history)
            updater.rewrite_commit_messages(commit_history)
        except Exception as e:
            logging.critical(
                f"An error occurred during the rewrite process. "
                f"'python {__file__} --restore'. Error: {e}"
            )
            return  # Stop execution after error

        # 6. Force push (if enabled and user is aware)
        if args.force_push:
            print(
                "\nWARNING: Force pushing will overwrite the remote repository's history!"
            )
            while True:
                force_confirm = input(
                    "Are you absolutely sure you want to force push? (yes/no): "
                ).lower()
                if force_confirm in ("yes", "y"):
                    logging.info(
                        "Force pushing changes to remote repository..."
                    )
                    try:
                        repo.git.push(
                            "--force-with-lease",
                            "origin",
                            repo.active_branch.name,
                        )
                        logging.info("Successfully force-pushed changes.")
                        break  # Exit confirmation loop
                    except Exception as e:
                        logging.error(f"Error force pushing changes: {e}")
                        return  # Stop execution after error
                elif force_confirm in ("no", "n"):
                    logging.info("Force push cancelled.")
                    break  # Exit confirmation loop
                else:
                    print("Invalid input. Please enter 'yes' or 'no'.")
    else:
        logging.info("Rewrite cancelled by user.")

    logging.info("OCDG process completed!")

if __name__ == "__main__":
    main()