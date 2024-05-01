import os
import tempfile

from utils import run_git_command, log_message


def update_repository(repo_path, commit_history):
    """Updates commit messages in the repository using git filter-branch."""
    # Create a temporary directory for the filter script
    with tempfile.TemporaryDirectory() as temp_dir:
        filter_script_path = os.path.join(temp_dir, "filter_script.py")

        # Generate and save the filter script
        generate_filter_script(commit_history, filter_script_path)

        # Backup refs before running filter-branch
        run_git_command(["for-each-ref", "--format='%(refname)'", "refs/heads/", "refs/remotes/", "refs/tags/", ">",
                         ".git/refs_backup"], repo_path)

        try:
            # Run git filter-branch with the filter script
            filter_branch_cmd = ["filter-branch", "-f", "--msg-filter", f"python {filter_script_path}",
                                 "--tag-name-filter", "cat", "--", "HEAD"]
            run_git_command(filter_branch_cmd, repo_path)
        except Exception as e:
            log_message(f"Error updating repository: {e}", level="error")
            # Restore refs from backup
            run_git_command(["update-ref", "--stdin", "<", ".git/refs_backup"], repo_path)
            raise

        # Remove backup file
        os.remove(os.path.join(repo_path, ".git/refs_backup"))
        log_message("Repository update completed.", level="info")

def generate_filter_script(commit_history, script_path):
    """Generates the filter script to replace commit messages."""
    with open(script_path, "w") as f:
        f.write("""
import sys

def filter_message(message):
    # Mapping of old commit hashes to new messages
    message_map = {
""")
        for commit in commit_history.commits:
            f.write(f"        '{commit.hash}': '{commit.new_message}',\n")
        f.write("""
    }

    commit_hash = sys.stdin.readline().strip()
    return message_map.get(commit_hash, message)

if __name__ == "__main__":
    print(filter_message(sys.stdin.readline().strip()))
""")

