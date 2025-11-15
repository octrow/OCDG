# OCDG

Rewrites Git commit history with LLM-generated messages. Supports Llama3, OpenAI, Groq, Replicate, Ollama.

## Workflow

1. Clone repository
2. Extract diffs
3. Generate messages via LLM
4. Rewrite history
5. Force-push (optional)

## Requirements

- Python 3.11+
- Poetry
- Git repository
- API keys for chosen LLM provider

## Installation

```bash
git clone https://github.com/octrow/OCDG.git
cd OCDG
python3 -m venv .venv
source .venv/bin/activate
poetry install
poetry shell
```

## Configuration

```bash
cp .env.example .env
```

Set API keys in `.env`:
- `NVIDIA_API_KEY` - OpenAI client
- `GROQ_API_KEY` - Groq client
- `REPLICATE_API_TOKEN` - Replicate client
- Ollama - no key (local)

Ollama install: https://ollama.com/

## Usage

```bash
python main.py <repo_path> [-b <backup_dir>] [-l <llm_choice>] [-m <model>] [-f] [-r]
```

### Arguments

- `repo_path` - Local path or remote URL
- `-b` - Backup directory
- `-l` - LLM provider (`ollama`|`openai`|`groq`|`replicate`), default: `ollama`
- `-m` - Model name
- `-f` - Force push
- `-r` - Restore backup

### Examples

```bash
python main.py /path/to/repo
python main.py https://github.com/user/repo -l groq -m llama3-70b-8192
python main.py /path/to/repo -l openai -m meta/llama3-70b-instruct -f
python main.py /path/to/repo -r
```

## Docker

```bash
docker build -t ocdg .
docker run --rm -v $(pwd)/repos:/app/repos --env-file .env ocdg /app/repos/your-repo
```

### Compose

```bash
cp .env.example .env
docker-compose run --rm ocdg /app/repos/your-repo -l groq

docker-compose --profile local-llm up -d ollama
docker-compose run --rm ocdg /app/repos/your-repo -l ollama
```

## Features

- Async concurrent processing
- Automatic Git backup/restore
- Exponential backoff retry logic (3 retries, 1s→2s→4s)
- Intelligent diff chunking for large commits
- JSON schema validation for LLM responses
- Multi-provider LLM support
- Configurable ignore patterns for binaries/dependencies
- Docker and Docker Compose support

## Architecture

- `main.py` - Orchestration, diff analysis, rewriting
- `clients/` - LLM implementations (base, ollama, openai, groq, replicate)
- `config.py` - Environment config, ignore patterns
- `retry_utils.py` - Exponential backoff decorator
- `test_ocdg.py` - Tests

Classes: `GitAnalyzer`, `Commit`, `CommitHistory`, `RepositoryUpdater`

## Configuration

Edit `config.py` `IGNORED_SECTION_PATTERNS` and `IGNORED_LINE_PATTERNS` to exclude paths from diffs.

Default excludes: `venv/`, `.idea/`, `node_modules/`, `__pycache__/`, binaries, lock files, logs

## Safety

- Refs backup before modifications
- User confirmation required
- Auto-restore on errors
- Force-push needs `-f`

## Retry

Max 3 retries, exponential backoff: 1s → 2s → 4s (max 60s)

## Limitations

- Beta
- Non-TTY rebase may fail
- Large repos memory-intensive
- No incremental processing

## Contributing

See CONTRIBUTING.md

## License

MIT

## Author

octrow <octrow@yandex.ru>
