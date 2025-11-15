# Changelog

## [0.2.0-beta] - 2025-11-15

### Fixed
- Missing `await` on `combine_messages()` async call (main.py:477)
- Static method call on instance method `get_repo_url()` (main.py:660)
- Invalid loguru API call `logger.error(level=)` (main.py:532)
- Missing comma in `IGNORED_SECTION_PATTERNS` (config.py:26)
- Config validation not using `args.llm` parameter (main.py:644)
- Module-level config loading causing import-time issues (clients/*)
- Removed unused `logging` import (main.py)

### Added
- `retry_utils.py`: Exponential backoff decorator (3 retries, 1s→2s→4s)
- `async_generate_text()` method to OpenAI client
- `async_generate_text()` method to Groq client
- Full ReplicateClient implementation (sync + async)
- Retry logic to all 4 LLM clients (8 methods total)
- `Dockerfile` for containerization
- `.dockerignore` for build optimization
- `docker-compose.yml` with OCDG and Ollama services
- `.github/workflows/ci.yml` CI/CD pipeline
- `CONTRIBUTING.md` development guidelines
- `replicate` dependency to pyproject.toml
- All API keys to .env.example
- Docker usage documentation to README.md
- Retry logic documentation to README.md

### Changed
- Standardized all `logging.*` calls to `logger.*` (19 occurrences)
- Config validation now provider-specific (checks required keys per LLM)
- OpenAI client uses `os.getenv()` for NVIDIA_API_KEY
- Ollama client imports only required constants
- README.md rewritten: brutal brevity, zero marketing (178 lines)
- Status: Alpha → Beta
- All LLM client error handling now uses retry decorator

### Removed
- Try-except blocks from LLM clients (replaced by retry decorator)
- Print statements from LLM clients (use logger only)
- Module-level config loading from clients

## [0.1.0-alpha] - 2024-XX-XX

### Added
- Initial release
- Multi-provider LLM support (OpenAI, Groq, Ollama)
- Git commit history rewriting
- Async concurrent processing
- Intelligent diff chunking
- JSON schema validation
- Configurable ignore patterns

[0.2.0-beta]: https://github.com/octrow/OCDG/compare/v0.1.0...v0.2.0
[0.1.0-alpha]: https://github.com/octrow/OCDG/releases/tag/v0.1.0
