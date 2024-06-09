import os
import json
import tempfile
from unittest.mock import patch, MagicMock

import git
import pytest

from main import (
    COMMIT_MESSAGES_LOG_FILE,
    RepositoryUpdater,
    CommitHistory,
    save_commit_messages_to_log,
    filter_diff,
    run_git_command,
    validate_repo_path,
    # parse_output_string,
    _split_text_at_boundaries,
    _split_diff_intelligently,
    _split_text_aggressively,
    _generate_single_commit_message_json,
    _generate_commit_message_parts,
    combine_messages,
    generate_commit_description,
    Commit,
    GitAnalyzer,
)
from clients import create_client, OpenAIClient, GroqClient
from config import load_configuration

# Load test configuration
TEST_CONFIG = load_configuration()


@pytest.fixture
def mock_git_repo(monkeypatch):
    """Fixture to mock Git repository interactions using GitPython."""
    mock_repo = MagicMock(spec=git.Repo)
    mock_git = MagicMock(spec=git.Git)

    def mock_execute(*args, **kwargs):
        command = args[0]
        if command == ['rev-parse', '--is-inside-work-tree']:
            return ""  # Simulate being inside a work tree
        elif command == ['--version']:
            return "git version 2.30.1"
        elif command[0] == "rev-parse":
            return ""  # Simulate success
        elif command[:2] == ["remote", "get-url"]:
            return "git@github.com:example/repo.git\n"
        elif command[:2] == ['rev-list', '--max-parents=0', 'HEAD']:
            return "initial_commit_hash\n"
        elif command == ['diff', 'commit_hash~1', 'commit_hash']:
            return "mocked diff output"
        else:
            return ""

    mock_git.execute.side_effect = mock_execute
    mock_repo.git = mock_git

    monkeypatch.setattr("git.Repo", lambda *args, **kwargs: mock_repo)
    return mock_repo

@pytest.fixture
def mock_llm_client(monkeypatch):
    """Fixture to mock the LLM client."""
    mock_response = json.dumps({
        "Short analysis": "Mocked analysis",
        "New Commit Title": "Test Title",
        "New Detailed Commit Message": "This is a test message.",
        "Code Changes": {"file.py": "Changes"}
    })

    def mock_generate_text(self, prompt, **kwargs):
        return mock_response

    monkeypatch.setattr(OpenAIClient, "generate_text", mock_generate_text)
    monkeypatch.setattr(GroqClient, "generate_text", mock_generate_text)

@pytest.fixture
def temp_repo_path():
    """Fixture to create a temporary directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir

@pytest.fixture
def commit_history():
    """Fixture to create a sample CommitHistory object."""
    history = CommitHistory()
    history.commits = [
        Commit("hash1", "Author 1", "2024-01-20", "Message 1", repo=MagicMock()),
        Commit("hash2", "Author 2", "2024-01-21", "Message 2", repo=MagicMock()),
    ]
    return history

# ------------------------------------------------------------------------------
# Tests
# ------------------------------------------------------------------------------

def test_run_git_command(mock_git_repo):
    """Test running a basic Git command."""
    output = run_git_command(["--version"])
    assert "git version" in output

def test_validate_repo_path_valid(temp_repo_path, mock_git_repo):
    """Test validating a correct repository path."""
    # Create a mock .git directory to simulate a valid repo
    os.mkdir(os.path.join(temp_repo_path, ".git"))
    validate_repo_path(temp_repo_path)

def test_validate_repo_path_invalid():
    """Test validating an incorrect repository path."""
    with pytest.raises(ValueError):
        validate_repo_path("non_existing_path")

def test_filter_diff():
    """Test filtering unwanted sections and lines from a diff."""
    diff = """
    diff --git a/some/path/file.py b/some/path/file.py
    index 1234567..abcdefg 100644
    --- a/some/path/file.py
    +++ b/some/path/file.py
    @@ -1,2 +1,2 @@
    -print("old code")
    +print("new code")
    diff --git a/venv/some/other/file.py b/venv/some/other/file.py
    index 1234567..abcdefg 100644
    --- a/venv/some/other/file.py
    +++ b/venv/some/other/file.py
    @@ -1,2 +1,2 @@
    -print("old code in venv")
    +print("new code in venv")
    Binary files a/image.jpg and b/image.jpg differ
    """
    filtered_diff = filter_diff(diff)
    assert "venv" not in filtered_diff
    assert "new code" in filtered_diff
    assert "Binary files" not in filtered_diff


def test_split_text_at_boundaries():
    """Tests the _split_text_at_boundaries function."""
    text = """This is some text.
    ```python
    print("Hello, world!")
    ```
    More text here.
    ```
    This is another code block.
    ```
    And some final text."""
    chunks = _split_text_at_boundaries(text, max_chunk_size=50)
    assert len(chunks) == 4
    assert all(len(chunk) <= 50 for chunk in chunks)

def test_split_text_at_boundaries_no_splits():
    """Tests when text is smaller than chunk size."""
    text = "Small text"
    chunks = list(_split_text_at_boundaries(text, max_chunk_size=50))
    assert all(len(chunk) <= 50 for chunk in chunks)

def test_split_diff_intelligently():
    """Test splitting a diff intelligently."""
    diff = """
    ```diff
    --- a/file1.py
    +++ b/file1.py
    @@ -1,2 +1,2 @@
    -print("old code")
    +print("new code")
    ```
    """
    chunks = _split_diff_intelligently(diff, max_chunk_size=50)
    assert len(chunks) > 1

def test_split_diff_intelligently_aggressive():
    """Test aggressive splitting when no logical boundaries are found."""
    diff = "a" * 8000
    chunks = _split_diff_intelligently(diff, max_chunk_size=1000)
    assert len(chunks) > 1

def test_split_text_aggressively():
    """Test splitting text aggressively into chunks with overlap."""
    text = "This is a long text that needs to be split into smaller chunks."
    chunks = list(_split_text_aggressively(text, max_chunk_size=10))
    assert len(chunks) == 8

def test_generate_single_commit_message_json(mock_llm_client):
    """Test generating a single commit message part (mocked LLM)."""
    diff_chunk = "- print('old')\n+ print('new')"
    commit_message = "Old message"
    model = "mock_model"
    chunk_index = 0
    total_chunks = 1

    result = _generate_single_commit_message_json(
        diff_chunk, commit_message, mock_llm_client, model, chunk_index, total_chunks
    )
    assert result["New Commit Title"] == "Test Title"
    assert result["New Detailed Commit Message"] == "This is a test message."

def test_generate_commit_message_parts(mock_llm_client):
    """Test generating parts of a commit message (mocked LLM)."""
    diff = "- print('old')\n+ print('new')"
    old_description = "Old message"
    model = "mock_model"

    commit_messages = _generate_commit_message_parts(
        diff, old_description, mock_llm_client, model, chunk_size=100
    )
    assert len(commit_messages) == 1
    assert commit_messages[0]['New Commit Title'] == "Test Title"

def test_combine_messages(mock_llm_client):
    """Test combining multiple commit messages into a single message."""
    multi_commit = [
        {
            "Short analysis": "Analysis 1",
            "New Commit Title": "Title 1",
            "New Detailed Commit Message": "Message 1",
            "Code Changes": {"file1.py": "Changes"},
        },
        {
            "Short analysis": "Analysis 2",
            "New Commit Title": "Title 2",
            "New Detailed Commit Message": "Message 2",
            "Code Changes": {"file2.py": "More Changes"},
        },
    ]
    model = "mock_model"
    combined = combine_messages(multi_commit, mock_llm_client, model)
    assert combined["New Commit Title"] == "Test Title"
    assert combined["New Detailed Commit Message"] == "This is a test message."

def test_generate_commit_description_long_diff(mock_llm_client):
    """Test generating a commit description for a long diff (mocked LLM)."""
    diff = "- print('old')" + "+ print('new')\n" * 4000
    old_description = "Old message"
    model = "mock_model"

    new_description = generate_commit_description(
        diff, old_description, mock_llm_client, model
    )
    assert "Test Title" in new_description
    assert "This is a test message." in new_description

def test_commit_class():
    """Test the Commit class."""
    commit = Commit(
        hash="test_hash",
        author="Test Author",
        date="2024-01-20",
        message="Test commit message",
        repo=MagicMock()
    )
    assert commit.hash == "test_hash"
    assert commit.author == "Test Author"
    assert commit.date == "2024-01-20"
    assert commit.message == "Test commit message"

def test_commit_history(commit_history):
    """Test the CommitHistory class."""
    assert len(commit_history.commits) == 2
    assert commit_history.get_commit("hash1") == commit_history.commits[0]
    assert commit_history.get_commit("non_existing_hash") is None
    assert commit_history.get_oldest_commit() == commit_history.commits[0]

def test_save_commit_messages_to_log(commit_history):
    """Test saving commit messages to a log file."""
    commit_history.commits[0].new_message = "New Message 1"
    commit_history.commits[1].new_message = "New Message 2"
    save_commit_messages_to_log(commit_history)

    assert os.path.exists(COMMIT_MESSAGES_LOG_FILE)
    with open(COMMIT_MESSAGES_LOG_FILE, "r") as f:
        log_content = f.read()
        assert "Message 1" in log_content
        assert "New Message 1" in log_content
        assert "Message 2" in log_content
        assert "New Message 2" in log_content

def test_repository_updater_backup_restore(temp_repo_path, mock_git_repo):
    """Test backup and restore functionality of RepositoryUpdater."""
    updater = RepositoryUpdater(temp_repo_path)
    updater.backup_refs()
    assert hasattr(updater, 'refs_backup_file')
    assert os.path.exists(updater.refs_backup_file)
    updater.restore_refs()
    assert not os.path.exists(updater.refs_backup_file)

def test_repository_updater_rewrite(temp_repo_path, commit_history, mock_git_repo):
    """Test rewriting commit messages with RepositoryUpdater."""
    updater = RepositoryUpdater(temp_repo_path)
    commit_history.commits[0].new_message = "New Message 1"
    updater.rewrite_commit_messages(commit_history)
    # Assertions might need adjustments based on your mocking strategy

def test_git_analyzer(temp_repo_path, mock_git_repo):
    """Test the GitAnalyzer class."""
    analyzer = GitAnalyzer(temp_repo_path)

    repo_url = analyzer.get_repo_url()
    assert repo_url == "git@github.com:example/repo.git"

    commits = analyzer.get_commits()
    assert len(commits) > 0

    with pytest.raises(RuntimeError):
        # This should raise an error as 'wrong_hash' is invalid
        analyzer.get_commit_message("wrong_hash")

    # Mocking the commit object
    mock_commit = MagicMock(spec=git.Commit)
    mock_commit.hash = commits[0].hash
    mock_commit.author = "Test Author <test@example.com>"

    # Test updating commit message
    analyzer.update_commit_message(mock_commit, "Updated message")
    # Add assertions based on your mocking strategy to check if the message was updated

@pytest.mark.parametrize("client_type, expected_class", [
    ("openai", OpenAIClient),
    # ("groq", GroqClient),
    # ("replicate", ReplicateClient),  # Uncomment when you have Replicate tests
])
def test_create_client(client_type, expected_class, test_config=TEST_CONFIG):
    """Test creating different LLM clients."""
    client = create_client(client_type, test_config)
    assert isinstance(client, expected_class)
