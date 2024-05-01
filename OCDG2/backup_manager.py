import os
import re
import shutil

from utils import run_git_command, validate_repo_path, log_message


def get_repo_name_from_path(repo_path):
    # Use regular expressions to match different types of repository paths
    if repo_path.endswith(".git"):
        # Match the name in URLs ending with .git
        match = re.search(r'/([^/]+)\.git$', repo_path)
    else:
        # Match the name in normal file paths
        match = re.search(r'([^/\\]+)$', repo_path)
    if match:
        log_message(f"Extracted repository name from path: {match.group(1)}", level="info")
        return match.group(1)
    else:
        abs_path = os.path.abspath(repo_path)
        log_message(f"Could not extract repository name from path: {abs_path}", level="error")
        repo_name = os.path.basename(os.path.normpath(abs_path))
        log_message(f"Using default repository name: {repo_name}", level="warning")
        return repo_name
        # raise ValueError(f"Could not extract repository name from path: {repo_path}")


def create_backup(repo_path, backup_base_dir):
    """Creates a bare clone of the repository as a backup and names the backup directory after the repository name."""
    log_message(f"Creating base backup folder at '{backup_base_dir}'", level="info")
    validate_repo_path(repo_path)

    # Extract the repository name from the repo_path
    repo_name = get_repo_name_from_path(repo_path)
    backup_dir = os.path.join(backup_base_dir, repo_name)

    # Create a unique backup directory path using the repository name

    if os.path.exists(backup_dir):
        log_message(f"Backup directory '{backup_dir}' already exists. Overwriting...", level="warning")
        shutil.rmtree(backup_dir)
    os.makedirs(backup_dir, exist_ok=True)

    run_git_command(["clone", "--mirror", repo_path, backup_dir])
    log_message(f"Repository backed up to '{backup_dir}'", level="info")


def verify_backup(backup_dir):
    """Checks if the backup directory is a valid Git repository."""
    if not os.path.isdir(backup_dir):
        raise ValueError(f"Backup directory '{backup_dir}' does not exist.")
    try:
        run_git_command(["rev-parse", "--is-bare-repository"], backup_dir)
        log_message(f"Backup at '{backup_dir}' verified.", level="info")
        return True
    except RuntimeError as e:
        log_message(f"Backup verification failed: {e}", level="error")
        return False


def get_backup_info(backup_dir):
    """Retrieves information about the backup."""
    if not verify_backup(backup_dir):
        return None
    # Get backup creation time (approximation)
    ctime = os.path.getctime(backup_dir)
    return {"path": backup_dir, "created_at": ctime}