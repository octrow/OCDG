from utils import log_message

def update_commit_messages(commit_history, llm_interface):
    """Generates new commit messages for each commit in the history using the LLM."""
    for commit in commit_history.commits:
        try:
            new_message = llm_interface.generate_commit_message(commit.diff, commit.message)
            commit.new_message = new_message
            log_message(f"Generated new message for commit {commit.hash[:7]}", level="info")
        except Exception as e:
            log_message(f"Error generating message for commit {commit.hash[:7]}: {e}", level="error")