## OCDG Documentation: Revitalizing Git Commit Messages

#### Introduction

The Old Commit Description Generator (OCDG) is a Python-based tool designed to improve the quality and consistency of commit messages within a Git repository. It utilizes Large Language Models (LLMs) to automatically generate new, descriptive commit messages based on the commit diffs and existing messages. OCDG ensures a safe and controlled update process with robust backup and rollback mechanisms.

#### Features

- Intelligent Message Generation: Leverages LLMs like Llama3, OpenAI, or Gemini to create informative and conventional commit messages.
- Diff Analysis: Analyzes commit diffs to understand the changes made and provide context for message generation.
- Repository Backup: Creates a backup of the entire repository before updating commit messages, ensuring data safety.
- Error Handling & Rollback: Implements robust error handling and rollback mechanisms to maintain repository integrity.
- Logging: Provides informative logging messages to track the progress and identify potential issues.
- Customization: Offers options to configure the LLM settings, commit message conventions, and backup locations.

### Disclaimer
**NOT READY FOR USE!!!**

**OCDG modifies the Git history of your repository.** 

While the tool includes safety measures like backup and rollback, it's essential to use it cautiously and understand the potential risks associated with Git history rewrites!

I'm hope OCDG helps you improve the quality and clarity of your commit messages, leading to better collaboration and understanding within your development team!

### Installation

1. Clone the Repository:
```shell
git clone https://github.com/octrow/commit_diff.git
```
2. Install Dependencies:
```shell
cd OCDG
poetry install
poetry shell
```
3. Configure LLM Settings:
- Edit the main.py file and provide the necessary credentials or API keys for your chosen LLM.
- You might need to install additional LLM-specific libraries using pip.

### Usage

1. Run the Script:
```shell
python main.py /path/to/your/repository [-b /path/to/backup/dir] [-l llm_choice]
```
```shell 
* Replace `/path/to/your/repository` with the actual path to your Git repository.
* Optionally, use the `-b` flag to specify a directory for repository backup.
* Use the `-l` flag to choose the LLM (e.g., `-l openai`, `-l llama3`).
```
2. Review and Verify:
- The script will create a backup of your repository (if specified), analyze the commit history, generate new commit messages, and update the repository.
- Review the logs and verify that the commit messages have been updated correctly.

### Customization
- LLM Settings: Refer to the llm_integration.py file to configure settings specific to your chosen LLM (e.g., temperature, response length).
- Commit Conventions: Modify the prompt template in llm_integration.py to align with your preferred commit message conventions.
- Backup Location: Specify the backup directory using the -b flag when running the script.


