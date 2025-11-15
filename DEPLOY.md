# Production

## Pre-deployment

**Environment**
- [ ] Python 3.11+, Poetry, Git, Docker
- [ ] API keys for LLM provider

**Configuration**
- [ ] `cp .env.example .env`
- [ ] Set keys: `NVIDIA_API_KEY`, `GROQ_API_KEY`, `REPLICATE_API_TOKEN` (Ollama: none)
- [ ] Verify `.env` not in version control

**Testing**
- [ ] `python -m py_compile main.py config.py clients/*.py`
- [ ] `python -c "import main; from clients import create_client"`
- [ ] `python main.py --help`
- [ ] Test on small repo first

## Docker

```bash
docker build -t ocdg:0.2.0-beta .
docker run --rm --env-file .env ocdg:0.2.0-beta --help

docker run --rm \
  -v /path/to/repos:/app/repos \
  -v /path/to/logs:/app \
  --env-file .env \
  ocdg:0.2.0-beta /app/repos/target-repo -l groq
```

## Compose

```bash
docker-compose --profile local-llm up -d ollama
sleep 10
docker exec ollama ollama pull llama3
docker-compose run --rm ocdg /app/repos/target-repo -l ollama
```

## Resources

**Memory**
- OCDG: 2GB min, 4GB recommended
- Ollama: 8GB (llama3-70b), 4GB (llama3-7b)
- CPU: 2+ cores

**Volumes**
- `/app/repos` - Repositories
- `/app/commit_diff` - Temp clones
- `/app/commit_messages.log` - Old/new log
- `/app/generated_messages.log` - LLM responses

**Network**
- Cloud: HTTPS 443 outbound
- Ollama: Port 11434, bridge network

**Security**
- [ ] Secrets manager for keys
- [ ] Read-only mounts
- [ ] Non-root containers
- [ ] Network segmentation
- [ ] Review messages for sensitive data

## Backup

**Auto**: OCDG backs up refs before run
**Manual**: `git bundle create backup.bundle --all`
**Restore**: `python main.py /repo -r` or `git clone backup.bundle restored-repo`

## Monitoring

**Logs**
- `commit_messages.log` - Audit
- `generated_messages.log` - LLM validation
- `docker logs ocdg`

**Metrics**
- API retry count (rate limits)
- Processing time/commit
- Memory usage

## Scaling

**Concurrent**: Default 4 (`MAX_CONCURRENT_REQUESTS`), increase for throughput, respect rate limits
**Batch**: Sequential repos or parallel containers

## Errors

**Retry exhausted**: Check API key, network, rate limits
**OOM**: Reduce `MAX_CONCURRENT_REQUESTS`, increase memory
**Rebase fail**: `python main.py /repo -r`, check `git status`, manual fix

## Validation

- [ ] `.git/refs_backup` exists
- [ ] Review `generated_messages.log`
- [ ] Check `commit_messages.log`
- [ ] Test restore with `-r`
- [ ] Verify remote if `-f` used

## Rollback

**Auto**: `python main.py /repo -r`
**Manual**: `cd /repo && git reflog && git reset --hard <commit>`

## Support

Issues: https://github.com/octrow/OCDG/issues
Contributing: CONTRIBUTING.md
License: MIT
