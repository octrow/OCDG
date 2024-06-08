import argparse
import os
import logging
import shutil
import traceback
from typing import List, Any, Dict, Tuple

import git

from clients import create_client
from config import load_configuration

from data_access import Database
from git_repo import GitAnalyzer
from OCDG.utils import run_git_command, log_message, find_closing_brace_index, parse_output_string, generate_commit_multi, generate_commit_description

logger = logging.getLogger(__name__)
# Import other necessary modules

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Revitalize old commit messages using LLMs.")
    parser.add_argument("repo_path", help="Path to the Git repository (local path or URL).")
    parser.add_argument("-b", "--backup_dir",
                        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "backup"),
                        help="Directory for repository backup.")
    parser.add_argument("-l", "--llm", choices=["openai", "groq", "replicate"], default="openai", help="Choice of LLM.")
    parser.add_argument("-m", "--model", default="meta/llama3-70b-instruct", help="Choice of LLM model.")
    parser.add_argument("-f", "-force", default=True, help="Force update github.")
    # Add more arguments as needed...
    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
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
    # backup_dir = os.path.join(args.backup_dir, os.path.basename(repo_url))
    # if os.path.exists(backup_dir):
    #     user_input = input(
    #         f"Backup directory '{backup_dir}' already exists. Do you want to overwrite it? (yes/no): "
    #     ).lower()
    #     if user_input != 'yes':
    #         print("Exiting...")
    #         return
    #
    #     try:
    #         shutil.rmtree(backup_dir)
    #         print(f"Removed existing backup directory: {backup_dir}")
    #     except Exception as e:
    #         print(f"Error removing existing backup directory: {e}")
    #         return
    #
    # if args.backup_dir:
    #     logging.info("Creating repository backup...")
    #     try:
    #         run_git_command(["clone", "--mirror", repo_url, backup_dir])
    #         logging.info(f"Repository backed up to '{backup_dir}'")
    #     except Exception as e:
    #         logging.error(f"Error creating backup: {e}")
    #         return
    # else:
    #     logging.warning("Skipping repository backup. Proceed with caution!")

    # 2. Load Commit History
    logging.info("Loading commit history...")
    try:
        analyzer = GitAnalyzer(repo_path)
        commits = analyzer.get_commits()
        # Get the repo object from the analyzer
        repo = analyzer.repo
    except Exception as e:
        logging.error(f"Failed to load commit history: {e}")
        return

    logging.info(f"Loaded {len(commits)} commits from repository.")

    # 3. Initialize LLM Interface
    client = create_client(args.llm, config)

    # 4. Process each commit
    initial_commit_hash = run_git_command(['rev-list', '--max-parents=0', 'HEAD'], repo_path).strip()
    for i, commit in enumerate(commits):
        logging.info(f"Processing commit {i + 1}/{len(commits)}: {commit.hash}")
        try:
            if commit.hash == initial_commit_hash:
                logging.info(f"Skipping diff for initial commit: {commit.hash}")
                diff = ""  # Or handle the initial commit differently
                return
            else:
                diff = repo.git.diff(f'{commit.hash}~1', f'{commit.hash}')
            new_message = generate_commit_description(diff, commit.message, client, args.model)
            if new_message is None:
                logging.warning(f"Skipping commit {commit.hash} - No new message generated")
                continue

            # 5. Update Commit Message
            try:
                # Save old and new messages to the log file
                with open("commit_messages.log", "a") as log_file:
                    log_file.write(f"Commit: {commit.hash}\n")
                    log_file.write(f"Old Message: {commit.message}\n")
                    log_file.write(f"New Message: {new_message}\n\n")

                # Update commit message in Git
                analyzer.update_commit_message(commit, new_message)  # Call the function

                # Check if the commit message was updated successfully
                if analyzer.get_commit_message(commit.hash) == new_message:
                    logging.info(f"Updated commit message for commit {commit.hash}")
                else:
                    logging.error(f"Failed to update commit message for {commit.hash} with new message: {new_message}")
            except Exception as e:
                logging.error(f"Error updating commit message for commit {commit.hash}: {e}")
                return

        except Exception as e:
            logging.error(f"Error processing commit {commit.hash}: {traceback.format_exc()} {e}")
            return

    # Push changes to the remote repository
    if args.force_push:
        logging.info("Force pushing changes to remote repository...")
        try:
            repo.git.push('--force-with-lease', 'origin', repo.active_branch.name)
            logging.info("Successfully pushed changes to remote.")
        except Exception as e:
            logging.error(f"Error force pushing changes: {e}")

    logging.info("OCDG process completed!")


if __name__ == "__main__":
    main()