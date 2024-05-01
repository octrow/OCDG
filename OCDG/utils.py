import logging
import subprocess
import os
from loguru import logger

def run_git_command(command, repo_path="."):
    """Executes a Git command and returns the output."""
    try:
        logger.debug(f"Running git command: git {command}")
        result = subprocess.run(["git"] + command, cwd=repo_path, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Git command failed: {e.stderr}") from e

def validate_repo_path(repo_path):
    """Checks if the provided path is a valid Git repository."""
    if not os.path.isdir(repo_path):
        raise ValueError(f"Invalid repository path: {repo_path}")
    try:
        run_git_command(["rev-parse", "--is-inside-work-tree"], repo_path)
    except RuntimeError:
        raise ValueError(f"{repo_path} is not a valid Git repository.")

def log_message(message, level="info"):
    """Logs a message with the specified severity level."""
    log_function = getattr(logging, level)
    log_function(message)