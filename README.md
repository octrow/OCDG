# OCDG: Old Commit Description Generator

## Revitalizing Git Commit History with AI 🤖

The **Old Commit Description Generator (OCDG)** is a Python tool designed to enhance the clarity and informativeness of your Git commit history. It leverages the power of Large Language Models (LLMs) to automatically generate improved commit messages based on code diffs and previous descriptions. 

**🤔  The Problem:**  Many repositories have a history of commit messages that are unclear, inconsistent, or simply unhelpful. This can make it difficult to understand the evolution of a codebase, especially for newcomers or when revisiting older parts of the project.

**✨ The Solution:**  OCDG analyzes your commit diffs and existing messages to generate new, descriptive commit messages that adhere to best practices (like Conventional Commits). 

### Disclaimer
**This project is currently a work in progress and under active development.** While I'm excited about its potential, it is not yet ready for production use. 

## Key Features

- **AI-Powered Message Generation:**  Uses advanced LLMs, including Llama2, OpenAI, and Groq, to produce human-quality commit messages.  The `ollama`, `openai`, and `groq` libraries provide the necessary integrations for interacting with these models. 
- **Safe and Controlled:** Before any modifications, a full backup of your Git repository is created using `git for-each-ref` to store ref information. This backup can be easily restored using `git update-ref` if needed. 
- **Prioritizes Clarity:** Generates concise, technical, and well-structured commit messages.  Emphasizes the "what" and the "why" of code changes, aiding in understanding the rationale behind past decisions.
- **Configurable and Extensible:**  
    - **LLM Provider Choice:**  Switch between different LLM providers (OpenAI(nvidia), Groq, Replicate, Ollama(local)) using the `-l` command-line argument. 
    - **Model Selection:** Specify the desired LLM model (e.g., `meta/llama3-70b-instruct`) with the `-m` flag.
    - **Backup Management:** Customize the backup directory using the `-b` option.
    - **Force Push Option:**  The `-f` flag enables force-pushing changes to the remote repository (with a confirmation prompt for safety).
- **Intelligent Diff Chunking:** Handles large diffs by intelligently splitting them into manageable chunks using the `_split_text_at_boundaries`, `_split_diff_intelligently`, and `_split_text_aggressively` functions. This ensures optimal prompt sizes for LLMs and preserves context across code blocks. 
- **Asynchronous Processing:** Employs asynchronous programming with `asyncio` to process commits concurrently, significantly speeding up the commit message generation process, especially for repositories with large histories.
- **JSON Schema Validation:**  Ensures the LLM responses adhere to a predefined JSON schema using the `jsonschema` library. This guarantees consistent and reliable output that can be easily parsed and used by other parts of the application.
- **Robust Error Handling:**  Implements comprehensive error handling using try-except blocks to catch and manage potential issues during API interactions, Git operations, and JSON parsing.
- **Detailed Logging:** Leverages the `loguru` library to provide informative logs throughout the process, aiding in debugging and monitoring.

## Future Plans

- **LLM-Based Commit Evaluation:** Implement a system where an LLM evaluates the quality and content of the generated commit messages. This would involve rating different message options and choosing the most relevant and descriptive one.
- **Interactive User Interface:** Develop a user-friendly interface to provide a more intuitive and visually appealing way to interact with OCDG.  This would allow users to review suggestions, make manual edits, and have greater control over the rewriting process.
- **Support for Complex Branching:** Enhance OCDG to handle more complex Git histories with multiple branches, merges, and rebases.
- **Langchain Integration:** Integrate the Langchain framework to standardize LLM interactions, simplify prompt management, and streamline JSON parsing.

### Installation

1. Clone the Repository:
```shell
git clone https://github.com/octrow/OCDG.git
cd OCDG
```
2. Set up a Virtual Environment:
```shell
python3 -m venv .venv 
source .venv/bin/activate
```
3. Install Dependencies:
```shell
poetry install
poetry shell
```
3. Configure Environment Variables:
- Create a .env file in the project's root directory from .env.example.
- Add your API keys for the chosen LLM provider (e.g., OpenAI, Groq). The default is `ollama` with `llama3 7b`.
- **For Ollama:** Ensure you have Ollama installed and running locally. See [https://ollama.com/](https://ollama.com/) for installation instructions.

### Usage

1. Run OCDG:
 ```bash
   python main.py /path_url/to/your/repository 
                 [-b /path/to/backup/dir] 
                 [-l <llm_choice>] 
                 [-m <llm_model>] 
                 [-f]
                 [-r]
```
- Replace `/path/to/your/repository` with the path to your Git repository.
- **Optional Arguments:**
  - `-b /path/to/backup/dir`: Specify a custom directory for backing up the repository.
  - `-l <llm_choice>`: Choose the LLM provider (e.g., `openai`, `ollama`). The default is `ollama`.
  - `-m <llm_model>`:  Specify the LLM model (e.g., `meta/llama3-70b-instruct`).  Defaults vary by provider (see `main.py`).
  - `-f`: Force push changes to the remote repository after rewriting (use with caution!).
  - `-r`: Restore the repository from a previously created backup.
  
2. **Review and Confirm:**
   - OCDG will analyze the commit history and generate new commit messages.
   - You'll be prompted to confirm the changes before they are applied.
   - Review the generated messages carefully.

## Customization

- **API Keys:**  If using providers other than Ollama, set your API keys in the `.env` file.
- **LLM Provider and Model:**  Use the `-l` and `-m` arguments to choose the desired LLM and model. Ollama is the default LLM provider. 
- **Backup Location:** Configure the backup directory with the `-b` argument.
- **Force Push:** Use the `-f` flag carefully to force push changes.
- **Ignored Files and Patterns:** Modify `IGNORED_SECTION_PATTERNS` and `IGNORED_LINE_PATTERNS` in `config.py` to exclude specific files or patterns from diff analysis. 

## Contributing

I welcome contributions and feedback from the community! If you're passionate about improving developer workflows and believe in the power of AI for code understanding, feel free to open issues, submit pull requests, or share your thoughts. 
