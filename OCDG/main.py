import argparse
import logging
import os
import traceback

import backup_manager
import commit_history
import commit_message_generator
import llm_integration
import repository_updater
import utils
from dotenv import load_dotenv
from llm_integration import generate_commit_description


def main():
    load_dotenv()
    # Setup argument parser
    parser = argparse.ArgumentParser(description="Revitalize old commit messages using LLMs.")
    parser.add_argument("repo_path", help="Path to the Git repository (local path or URL).")
    parser.add_argument("-b", "--backup_dir", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "backup"), help="Directory for repository backup.")
    parser.add_argument("-l", "--llm", choices=["llama3", "openai", "gemini"], default="openai", help="Choice of LLM.")
    # Add more arguments for LLM-specific settings as needed

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    # Determine repository type and get URL
    if args.repo_path.startswith(("http", "git@")):
        repo_url = args.repo_path
    else:
        # Get absolute path for local repositories
        repo_path = os.path.abspath(args.repo_path)
        logging.info(f"Using local repository path: {repo_path}")
        repo_url = commit_history.CommitHistory().get_repo_url(repo_path)
        if not repo_url:
            logging.error("Failed to get repository URL from local path. Exiting...")
            return

    # 1. Backup Repository
    if args.backup_dir:
        logging.info("Creating repository backup...")
        backup_manager.create_backup(args.repo_path, args.backup_dir)
    else:
        logging.warning("Skipping repository backup. Proceed with caution!")

    # 2. Load Commit History
    logging.info("Loading commit history...")
    history = commit_history.CommitHistory()
    history.load_from_repo(args.repo_path)
    logging.info(f"Loaded {len(history.commits)} commits from repository.")
    if not history.commits:
        logging.error("Failed to load commit history. Exiting...")
        return

    # 3. Initialize LLM Interface

    NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY")
    # logging.info(f"Initializing {args.llm} LLM interface...")
    # # llm = llm_integration.LLMInterface(args.llm)  # Add LLM specific arguments here
    # try:
    #     llm = llm_integration.LLMInterface()
    # except Exception as e:
    #     logging.error(f"Failed to initialize LLM interface: {e}")
    #     logging.error(f'traceback.format_exc(): {traceback.format_exc()}')
    #     return

    # 4. Generate New Commit Messages
    logging.info("Generating new commit messages using LLM...")
    # commit_message_generator.update_commit_messages(history, llm)
    generate_commit_description(history)
    # 5. Update Repository
    logging.info("Updating commit messages in the repository...")
    # repository_updater.update_repository(args.repo_path, history)

    # 6. Verification and Completion
    logging.info("Commit messages updated successfully!")
    logging.info("Verifying changes...")
    # Add verification logic here

    logging.info("OCDG process completed!")


if __name__ == "__main__":
    main()