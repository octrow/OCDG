import os

from clients import create_client
from config import load_configuration
import argparse

from data_access import Database
from git_repo import GitAnalyzer
# from clients import create_client
# from data_access import CommitDatabase
# from git_utils import GitAnalyzer
from message_generation import MessageGenerator

# Import other necessary modules

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("repo_url", help="URL of the GitHub repository")
    parser.add_argument("client", choices=["openai", "groq", "replicate"], help="AI client to use")
    # Add more arguments as needed...
    args = parser.parse_args()
    config = load_configuration()
    os.makedirs(config['COMMIT_DIFF_DIRECTORY'], exist_ok=True)

    # Create client instance
    client = create_client(args.client)
    repo = args.repo_url
    commits = repo.get_commits()

    db = Database()
    analyzer = GitAnalyzer(args.repo_url)
    generator = MessageGenerator(client)

    # Get commits from the Git repository
    commits = analyzer.get_commits()  # Implement logic to retrieve commits based on arguments

    # Process each commit
    for commit in commits:
        # Generate diff
        diff = analyzer.get_diff(commit)

        # Generate new commit message
        new_message = generator.generate_commit_message(diff, commit.message)

        # Update commit message in Git and database
        analyzer.update_commit_message(commit, new_message)
        commit.message = new_message  # Update commit object
        db.update_commit(commit)






    # ... rest of the application logic ...


if __name__ == "__main__":
    main()