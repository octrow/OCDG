# Contributing to OCDG

## Development Setup

```bash
git clone https://github.com/octrow/OCDG.git
cd OCDG
python3 -m venv .venv
source .venv/bin/activate
poetry install --with dev
pre-commit install
```

## Code Style

**Brutal brevity required:**
- Direct, technical language only
- No marketing phrases
- Information-first structure
- Active voice imperatives
- Every word must be essential

## Adding LLM Providers

Create client in `clients/`:

```python
from clients.base_client import Client
from retry_utils import retry_with_backoff

class NewProviderClient(Client):
    def __init__(self, api_key):
        super().__init__(api_key)
        # Initialize client

    @retry_with_backoff(max_retries=3, exceptions=(Exception,))
    def generate_text(self, prompt, **kwargs):
        # Implementation
        pass

    @retry_with_backoff(max_retries=3, exceptions=(Exception,))
    async def async_generate_text(self, system_prompt, prompt, **kwargs):
        # Async implementation
        pass
```

Update:
1. `clients/__init__.py` - Add to factory
2. `config.py` - Add API key validation
3. `.env.example` - Add key placeholder
4. `main.py` - Add to CLI choices

## Quality Checks

**Run all checks**
```bash
poetry run pytest -v --cov=.
poetry run ruff check .
poetry run mypy main.py config.py retry_utils.py
```

**Auto-format**
```bash
poetry run black .
poetry run ruff check --fix .
```

**Pre-commit (auto-runs on commit)**
```bash
pre-commit run --all-files
```

## Commit Messages

Format:
```
Category: Brief description

- Specific change 1
- Specific change 2

Impact:
- What changed for users
```

Categories: Fix, Feature, Refactor, Docs, CI, Test

## Pull Requests

1. Fork repository
2. Create feature branch: `git checkout -b feature/name`
3. Implement changes
4. Run quality checks: `pytest -v --cov=. && ruff check . && mypy main.py config.py retry_utils.py`
5. Commit with clear message (pre-commit runs automatically)
6. Push: `git push origin feature/name`
7. Create PR with description

## CI Pipeline

GitHub Actions runs:
- Python 3.11/3.12 tests with coverage
- Ruff linting
- Mypy type checking
- Syntax validation
- Import checks
- Docker build

All must pass.

## Issue Reporting

Include:
- Python version
- LLM provider used
- Full error traceback
- Minimal reproduction steps
- Expected vs actual behavior

## License

MIT - See LICENSE file
