# Production Deployment

## Pre-deployment Checklist

### Environment

- [ ] Python 3.11+ installed
- [ ] Poetry installed (`curl -sSL https://install.python-poetry.org | python3 -`)
- [ ] Git installed
- [ ] Docker installed (for containerized deployment)
- [ ] API keys obtained for chosen LLM provider

### Configuration

- [ ] Copy `.env.example` to `.env`
- [ ] Set API keys in `.env`:
  - `NVIDIA_API_KEY` (for OpenAI client)
  - `GROQ_API_KEY` (for Groq client)
  - `REPLICATE_API_TOKEN` (for Replicate client)
  - Ollama: no key required
- [ ] Verify `.env` not committed to version control

### Testing

- [ ] Run syntax validation: `python -m py_compile main.py config.py clients/*.py`
- [ ] Test import: `python -c "import main; from clients import create_client"`
- [ ] Test LLM connection: `python main.py --help`
- [ ] Run on test repository first

### Docker Deployment

```bash
# Build image
docker build -t ocdg:0.2.0-beta .

# Test run
docker run --rm --env-file .env ocdg:0.2.0-beta --help

# Production run with volumes
docker run --rm \
  -v /path/to/repos:/app/repos \
  -v /path/to/logs:/app \
  --env-file .env \
  ocdg:0.2.0-beta /app/repos/target-repo -l groq
```

### Docker Compose Deployment

```bash
# Start Ollama (if using local LLM)
docker-compose --profile local-llm up -d ollama

# Wait for Ollama to start (5-10s)
sleep 10

# Pull Ollama model
docker exec ollama ollama pull llama3

# Run OCDG
docker-compose run --rm ocdg /app/repos/target-repo -l ollama
```

## Production Recommendations

### Resource Limits

Docker memory limits:
- OCDG: 2GB minimum, 4GB recommended
- Ollama: 8GB minimum for llama3-70b, 4GB for llama3-7b

CPU: 2+ cores recommended for async processing

### Volume Mounts

Required:
- `/app/repos` - Repository storage
- `/app/commit_diff` - Temporary clone directory

Optional:
- `/app/commit_messages.log` - Old/new message log
- `/app/generated_messages.log` - LLM response log

### Network Configuration

Cloud LLMs (OpenAI, Groq, Replicate):
- Outbound HTTPS (443) required
- No inbound ports needed

Ollama (local):
- Port 11434 for OCDG → Ollama communication
- Use Docker bridge network for container-to-container

### Security

- [ ] Store API keys in secrets manager (not .env in production)
- [ ] Use read-only volume mounts where possible
- [ ] Run containers as non-root user
- [ ] Network segmentation for Ollama
- [ ] Review commit message generation for sensitive data exposure

### Backup Strategy

Before each run:
- Git refs automatically backed up by OCDG
- Manual backup: `git bundle create backup.bundle --all`

Restore:
- OCDG restore: `python main.py /repo -r`
- Manual restore: `git clone backup.bundle restored-repo`

### Monitoring

Log to external system:
- `commit_messages.log` - Audit trail
- `generated_messages.log` - LLM response validation
- Docker logs: `docker logs ocdg`

Metrics to track:
- API retry count (indicates rate limiting)
- Processing time per commit
- Memory usage for large repositories

### Scaling

Concurrent processing:
- Default: 4 concurrent requests (`MAX_CONCURRENT_REQUESTS`)
- Increase for higher throughput
- Respect API rate limits

Batch processing:
- Process repositories sequentially
- Use separate containers for parallel repo processing

### Error Handling

Retry exhausted:
- Check API key validity
- Verify network connectivity
- Review rate limits

Out of memory:
- Reduce `MAX_CONCURRENT_REQUESTS`
- Increase Docker memory limit
- Process smaller repositories

Rebase failures:
- Use restore: `python main.py /repo -r`
- Check repository state: `git status`
- Manual intervention may be required

## Post-deployment Validation

- [ ] Verify backup created: Check `.git/refs_backup` existence
- [ ] Review generated messages: Check `generated_messages.log`
- [ ] Compare old vs new: Check `commit_messages.log`
- [ ] Test restore: Run with `-r` flag on test repo
- [ ] Verify remote push (if using `-f`): Check remote repository

## Rollback

Automatic:
```bash
python main.py /repo -r
```

Manual:
```bash
cd /repo
git reflog
git reset --hard <commit-before-ocdg>
```

## Support

Issues: https://github.com/octrow/OCDG/issues
Contributing: See CONTRIBUTING.md
License: MIT
