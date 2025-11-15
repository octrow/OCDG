# Quick Start

### Local Python (Ollama)

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3

git clone https://github.com/octrow/OCDG.git
cd OCDG
python3 -m venv .venv
source .venv/bin/activate
pip install poetry
poetry install

python main.py /path/to/your/repo
```

### Docker (Cloud LLM)

```bash
git clone https://github.com/octrow/OCDG.git
cd OCDG
cp .env.example .env
echo "GROQ_API_KEY=your_key_here" >> .env

docker build -t ocdg .
docker run --rm -v /path/to/your/repo:/app/repos --env-file .env ocdg /app/repos -l groq
```

### Docker Compose (Ollama)

```bash
git clone https://github.com/octrow/OCDG.git
cd OCDG
docker-compose --profile local-llm up -d ollama
sleep 10
docker exec ollama ollama pull llama3

docker-compose run --rm ocdg /app/repos/your-repo -l ollama
```

## Test

```bash
mkdir test-repo && cd test-repo
git init
echo "# Test" > README.md
git add . && git commit -m "initial"
echo "More content" >> README.md
git add . && git commit -m "update"

cd ..
python main.py test-repo
```

Output: Repository analysis → Commit processing → Preview → Confirmation (`yes`) → Success

## Commands

```bash
python main.py /repo/path
python main.py https://github.com/user/repo -l groq -m llama3-70b-8192
python main.py /repo/path -l openai -m meta/llama3-70b-instruct
python main.py /repo/path -f
python main.py /repo/path -r
```

## Troubleshooting

**NVIDIA_API_KEY required**
```bash
echo "NVIDIA_API_KEY=your_key" >> .env
```

**Connection refused (Ollama)**
```bash
curl http://localhost:11434
ollama serve
```

**Module not found**
```bash
poetry install --no-cache
```

**Out of memory**
```bash
# config.py
MAX_CONCURRENT_REQUESTS = 2
```

## Process

1. Backup refs
2. Extract diffs
3. Generate messages
4. Preview
5. Confirm
6. Rewrite history
7. Push (if `-f`)

## Safety

- Auto-backup refs
- Confirmation required
- Restore with `-r`
- No auto-push

## Next

- CONTRIBUTING.md - Development
- DEPLOY.md - Production
- CHANGELOG.md - History
- README.md - Full docs
