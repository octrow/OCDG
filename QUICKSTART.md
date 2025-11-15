# Quick Start

## 5-Minute Setup

### Option 1: Local Python (Ollama)

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3

# Setup OCDG
git clone https://github.com/octrow/OCDG.git
cd OCDG
python3 -m venv .venv
source .venv/bin/activate
pip install poetry
poetry install

# Run
python main.py /path/to/your/repo
```

### Option 2: Docker (Cloud LLM)

```bash
# Clone and configure
git clone https://github.com/octrow/OCDG.git
cd OCDG
cp .env.example .env
echo "GROQ_API_KEY=your_key_here" >> .env

# Run
docker build -t ocdg .
docker run --rm -v /path/to/your/repo:/app/repos --env-file .env ocdg /app/repos -l groq
```

### Option 3: Docker Compose (Ollama)

```bash
# Clone and start
git clone https://github.com/octrow/OCDG.git
cd OCDG
docker-compose --profile local-llm up -d ollama
sleep 10
docker exec ollama ollama pull llama3

# Run
docker-compose run --rm ocdg /app/repos/your-repo -l ollama
```

## First Run Test

Test on a small repository first:

```bash
# Create test repo
mkdir test-repo && cd test-repo
git init
echo "# Test" > README.md
git add . && git commit -m "initial"
echo "More content" >> README.md
git add . && git commit -m "update"

# Run OCDG
cd ..
python main.py test-repo
```

Expected output:
1. Repository analysis
2. Commit processing (async)
3. Preview of new messages
4. Confirmation prompt: `yes`
5. Success message

## Common Commands

```bash
# Local repo, Ollama (default)
python main.py /repo/path

# Remote repo, Groq
python main.py https://github.com/user/repo -l groq -m llama3-70b-8192

# Custom model
python main.py /repo/path -l openai -m meta/llama3-70b-instruct

# Force push after rewrite
python main.py /repo/path -f

# Restore from backup
python main.py /repo/path -r
```

## Troubleshooting

### "NVIDIA_API_KEY required"
```bash
# Add to .env
echo "NVIDIA_API_KEY=your_key" >> .env
```

### "Connection refused" (Ollama)
```bash
# Check Ollama running
curl http://localhost:11434
# Start if needed
ollama serve
```

### "Module not found"
```bash
# Reinstall dependencies
poetry install --no-cache
```

### Out of memory
```bash
# Reduce concurrent requests in config.py
MAX_CONCURRENT_REQUESTS = 2
```

## What OCDG Does

1. **Backup**: Creates git refs backup
2. **Analyze**: Extracts commit diffs
3. **Generate**: LLM creates improved messages
4. **Preview**: Shows old vs new
5. **Confirm**: Asks for approval
6. **Rewrite**: Updates commit history
7. **Push** (if `-f`): Force-pushes to remote

## Safety

- Original refs backed up automatically
- User confirmation required before changes
- Restore with `-r` flag if needed
- No automatic push (requires `-f`)

## Next Steps

- Review CONTRIBUTING.md for development
- See DEPLOY.md for production deployment
- Check CHANGELOG.md for version history
- Read full README.md for details
