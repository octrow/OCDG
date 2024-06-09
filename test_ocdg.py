import os
import json
import tempfile
from unittest.mock import patch, MagicMock

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
def mocker():
    from unittest import mock
    return mock.MagicMock()

@pytest.fixture
def mock_git_command(monkeypatch):
    def mock_run_git_command(command, repo_path="."):
        #  Define expected outputs for different Git commands
        if command == ["--version"]:
            return "git version 2.30.1"  # Example version
        elif command[0] == "rev-parse":
            return  "" # Simulate success
        elif command[:2] == ["remote", "get-url"]:
            return "git@github.com:example/repo.git\n" # Example output
        else:
            return  "" # Default return value

    # Patch the function within the test scope
    monkeypatch.setattr("main.run_git_command", mock_run_git_command)

@pytest.fixture
def mock_llm_client(monkeypatch):
    mock_response = json.dumps({
        "Short analysis": "Mocked analysis",
        "New Commit Title": "Test Title",
        "New Detailed Commit Message": "This is a test message.",
        "Code Changes": {"file.py": "Changes"}
    })
    def mock_generate_text(self, prompt, **kwargs):
        return mock_response

    # Adapt this to mock the specific client you're using
    monkeypatch.setattr(OpenAIClient, "generate_text", mock_generate_text)

@pytest.fixture(scope="session") # Change scope to "session"
def test_repo(tmp_path_factory):
    """Creates a temporary Git repository for testing."""
    repo_path = tmp_path_factory.mktemp("test_repo")
    os.makedirs(repo_path, exist_ok=True)
    run_git_command(["init"], str(repo_path))

    # Create a test file and commit it
    with open(os.path.join(repo_path, "test.txt"), "w") as f:
        f.write("Initial content\n")
    run_git_command(["add", "."], str(repo_path))
    run_git_command(
        ["commit", "-m", "Initial commit"], str(repo_path)
    )

    # Make some changes and commit again
    with open(os.path.join(repo_path, "test.txt"), "a") as f:
        f.write("More content\n")
    run_git_command(["add", "."], str(repo_path))
    run_git_command(
        ["commit", "-m", "Second commit"], str(repo_path)
    )
    yield repo_path
    # Cleanup (pytest handles this automatically after the yield)

def test_run_git_command(test_repo):
    """Test running a basic Git command."""
    output = run_git_command(["--version"], repo_path=str(test_repo))
    assert "git version" in output

def test_validate_repo_path_valid(test_repo, mock_git_command):
    """Test validating a correct repository path."""
    validate_repo_path(str(test_repo))

def test_validate_repo_path_invalid():
    """Test validating an incorrect repository path."""
    with pytest.raises(ValueError):
        validate_repo_path("non_existing_path")

def test_filter_diff_section(test_repo):
    """Test filtering unwanted sections from a diff."""
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
    """
    filtered_diff = filter_diff(diff)
    assert "venv" not in filtered_diff
    assert "new code" in filtered_diff


def test_filter_diff_lines(test_repo):
    """Test filtering unwanted lines from a diff."""
    diff = """
    diff --git a/some/path/file.py b/some/path/file.py
    index 1234567..abcdefg 100644
    --- a/some/path/file.py
    +++ b/some/path/file.py
    @@ -1,3 +1,3 @@
     # This is a comment
    -print("old code")
    +print("new code")
     # This is a .jpg image
     Binary files a/image.jpg and b/image.jpg differ
    """
    filtered_diff = filter_diff(diff)
    assert "Binary files a/image.jpg and b/image.jpg differ" not in filtered_diff
    assert "new code" in filtered_diff

# def test_parse_output_string():
#     output_string = """
#     **Short analysis**: This commit introduces a new feature.
#
#     **New Commit Title**: Feat: Implement new functionality
#
#     **New Detailed Commit Message**:
#     This commit implements a new feature that allows users to do something cool.
#
#     **Code Changes**:
#     ```
#     {"file1.py": "Added new function", "file2.py": "Modified existing function"}
#     ```
#     """
#     expected_data = {
#         "short_analysis": "This commit introduces a new feature.",
#         "commit_title": "Feat: Implement new functionality",
#         "detailed_commit_message": "This commit implements a new feature that allows users to do something cool.",
#         "code_changes": {"file1.py": "Added new function", "file2.py": "Modified existing function"},
#     }
#     assert parse_output_string(output_string) == expected_data

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
    chunks = list(_split_text_at_boundaries(text, max_chunk_size=50))  # Convert to list
    assert all(len(chunk) <= 50 for chunk in chunks)

def test_split_diff_intelligently():
    """Test splitting a diff intelligently."""
    # Create a long diff string with code blocks
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
    assert len(chunks) > 1 # Should now be split

def test_split_diff_intelligently_aggressive():
    """Test aggressive splitting when no logical boundaries are found."""
    diff = "a" * 8000  # A diff larger than max_chunk_size
    chunks = _split_diff_intelligently(diff, max_chunk_size=1000)
    assert len(chunks) > 1

def test_split_text_aggressively():
    text = "This is a long text that needs to be split into smaller chunks."
    chunks = list(_split_text_aggressively(text, max_chunk_size=10))  # Convert to list to evaluate
    assert len(chunks) == 7  # Should be split into 7 chunks

def test_generate_single_commit_message_json():
    """Test generating a single commit message part (mocked LLM)."""

    # Mocking the LLM client
    class MockClient:
        def generate_text(self, prompt, **kwargs):
            return """
            {
                "Short analysis": "Mocked analysis",
                "New Commit Title": "Test Title",
                "New Detailed Commit Message": "This is a test message.",
                "Code Changes": {"file.py": "Changes"}
            }
            """

    mock_client = MockClient()
    diff_chunk = "- print('old')\n+ print('new')"
    commit_message = "Old message"
    model = "mock_model"
    chunk_index = 0
    total_chunks = 1

    result = _generate_single_commit_message_json(diff_chunk, commit_message, mock_client, model, chunk_index,
                                                  total_chunks)
    assert result["New Commit Title"] == "Test Title"
    assert result["New Detailed Commit Message"] == "This is a test message."

def test_generate_commit_message_parts():
    """Test generating parts of a commit message (mocked LLM)."""
    class MockClient:
        def generate_text(self, prompt, **kwargs):
            return """
            {
                "Short analysis": "Mocked analysis",
                "New Commit Title": "Test Title",
                "New Detailed Commit Message": "This is a test message.",
                "Code Changes": {"file.py": "Changes"}
            }
            """

    mock_client = MockClient()
    diff = "- print('old')\n+ print('new')"  # Small diff
    old_description = "Old message"
    model = "mock_model"

    # Set chunk_size larger than the diff to ensure a single chunk
    commit_messages = _generate_commit_message_parts(diff, old_description, mock_client, model, chunk_size=100)

    assert len(commit_messages) == 1 # Verify only one message is generated
    assert commit_messages[0]['New Commit Title'] == "Test Title"

def test_combine_messages():
    class MockClient:
        def generate_text(self, prompt, **kwargs):
            combined_message = {
                "Short analysis": "Combined Analysis",
                "New Commit Title": "Combined Title",
                "New Detailed Commit Message": "This is a combined message.",
                "Code Changes": {"file1.py": "Changes", "file2.py": "More Changes"},
            }
            return json.dumps(combined_message)  # Return as a JSON string

    mock_client = MockClient()
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
    combined = combine_messages(multi_commit, mock_client, model)
    assert combined["New Commit Title"] == "Combined Title"
    assert combined["New Detailed Commit Message"] == "This is a combined message."


def test_generate_commit_description_long_diff(mocker):
    """Test generating a commit description for a long diff (mocked LLM)."""
    # ... (create a mock client similar to other tests)
    mock_client = MagicMock()

    diff = "- print('old')" + "+ print('new')\n" * 4000  # Creating a diff longer than 7900 characters
    old_description = "Old message"
    model = "mock_model"

    # Set up mock responses for chunk generation and combination.
    mock_client.generate_text.side_effect = [
                                                json.dumps({
                                                    "Short analysis": f"Mocked analysis for chunk {i}",
                                                    "New Commit Title": f"Test Title {i}",
                                                    "New Detailed Commit Message": f"This is a test message for chunk {i}.",
                                                    "Code Changes": {"file.py": "Changes"}
                                                }) for i in range(2)  # Assuming the diff will be split into two chunks
                                            ] + [
                                                json.dumps({
                                                    "Short analysis": "Combined analysis",
                                                    "New Commit Title": "Combined Title",
                                                    "New Detailed Commit Message": "This is a combined message.",
                                                    "Code Changes": {"file.py": "Changes"}
                                                })
                                            ]

    new_description = generate_commit_description(diff, old_description, mock_client, model)
    assert "Combined Title" in new_description
    assert "This is a combined message." in new_description

def test_generate_commit_description(mock_llm_client):
    """Test generating a commit description (mocked LLM)."""
    diff = "- print('old')\n+ print('new')"
    old_description = "Old message"
    model = "mock_model"
    # Mock LLM response:
    mock_llm_client.generate_text.return_value = json.dumps({
        "Short analysis": "Mocked analysis",
        "New Commit Title": "Test Title",
        "New Detailed Commit Message": "This is a test message.",
        "Code Changes": {"file.py": "Changes"}
    })

    new_description = generate_commit_description(diff, old_description, mock_llm_client, model)
    assert new_description == "Test Title\n\nThis is a test message."

def test_commit_class():
    """Test the Commit class."""
    commit = Commit(
        hash="test_hash",
        author="Test Author",
        date="2024-01-20",
        message="Test commit message",
        repo=None  # You can mock the repo object here if needed
    )
    assert commit.hash == "test_hash"
    assert commit.author == "Test Author"
    assert commit.date == "2024-01-20"
    assert commit.message == "Test commit message"

def test_commit_history():
    """Test the CommitHistory class."""
    history = CommitHistory()
    with patch.object(Commit, 'get_diff', return_value="mocked diff"):
        commit1 = Commit("hash1", "Author 1", "2024-01-20", "Message 1", repo=None)
        commit2 = Commit("hash2", "Author 2", "2024-01-21", "Message 2", repo=None)
    history.commits = [commit1, commit2]

    assert len(history.commits) == 2
    assert history.get_commit("hash1") == commit1
    assert history.get_commit("hash2") == commit2
    assert history.get_commit("non_existing_hash") is None

def test_save_commit_messages_to_log(test_repo):
    """Test saving commit messages to a log file."""
    commit_history = CommitHistory()
    commit_history.commits.append(
        Commit("hash1", "Author 1", "2024-01-20", "Old Message 1", repo=None)
    )
    commit_history.commits.append(
        Commit("hash2", "Author 2", "2024-01-21", "Old Message 2", repo=None),
    )
    commit_history.commits[0].new_message = "New Message 1"
    commit_history.commits[1].new_message = "New Message 2"
    save_commit_messages_to_log(commit_history)

    assert os.path.exists(COMMIT_MESSAGES_LOG_FILE)
    with open(COMMIT_MESSAGES_LOG_FILE, "r") as f:
        log_content = f.read()
        assert "Old Message 1" in log_content
        assert "New Message 1" in log_content
        assert "Old Message 2" in log_content
        assert "New Message 2" in log_content

def test_repository_updater(test_repo, mocker):
    """Test the RepositoryUpdater class (mocking Git commands)."""
    updater = RepositoryUpdater(repo_path=str(test_repo))

    # Test backup_refs
    mocker.patch('main.run_git_command')  # Patch here
    updater.backup_refs()

    # Test restore_refs
    mocker.patch('os.path.exists', return_value=True)
    mocker.patch('main.run_git_command')  # Patch here
    updater.restore_refs()

    # Test rewrite_commit_messages and generate_filter_script
    commit_history = CommitHistory()
    with patch.object(Commit, 'get_diff', return_value="mocked diff"):
        commit_history.commits.append(
            Commit(
                hash="test_hash",
                author="Test Author",
                date="2024-01-20",
                message="Old message",
                repo=None,
            )
        )
    commit_history.commits[0].new_message = "New message"

    with tempfile.TemporaryDirectory() as temp_dir:
        filter_script_path = os.path.join(temp_dir, "filter_script.py")
        updater.generate_filter_script(commit_history, filter_script_path)
        assert os.path.exists(filter_script_path)

        mocker.patch('main.run_git_command')  # Patch here
        updater.rewrite_commit_messages(commit_history)
        # Add assertions based on your mock_run_git calls here
        # For example, check if 'filter-branch' was called with the correct arguments

def test_git_analyzer(test_repo, mocker):
    """Test the GitAnalyzer class (partially mocked)."""
    analyzer = GitAnalyzer(repo_path=str(test_repo))

    # Mock run_git_command for get_commits
    mocker.patch("main.run_git_command", return_value="Test output")  # Patch here
    commits = analyzer.get_commits()
    assert len(commits) > 0

    mocker.patch("main.generate_commit_description", return_value="Mocked commit message")
    analyzer.update_commit_message(commits[0], "Updated message")

    # Mock subprocess.run for update_commit_message
    mocker.patch("main.subprocess.run")  # Patch here
    analyzer.update_commit_message(commits[0], "Updated message")
    # Add assertions based on your expectations of the subprocess calls

@pytest.mark.parametrize("client_type, expected_class", [
    ("openai", OpenAIClient),
    # ("groq", GroqClient),
    # ("replicate", ReplicateClient),  # Uncomment when you have Replicate tests
])
def test_create_client(client_type, expected_class, test_config=TEST_CONFIG):
    client = create_client(client_type, test_config)
    assert isinstance(client, expected_class)