import os
import shutil

from utils import run_git_command, validate_repo_path, log_message


def create_backup(repo_path, backup_dir):
    """Creates a bare clone of the repository as a backup."""
    validate_repo_path(repo_path)
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