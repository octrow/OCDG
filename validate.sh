#!/bin/bash
# OCDG Installation Validation Script

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=== OCDG Installation Validation ==="
echo ""

# Check Python version
echo -n "Checking Python version... "
PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 11 ]; then
    echo -e "${GREEN}✓ Python $PYTHON_VERSION${NC}"
else
    echo -e "${RED}✗ Python 3.11+ required (found $PYTHON_VERSION)${NC}"
    exit 1
fi

# Check Poetry
echo -n "Checking Poetry... "
if command -v poetry &> /dev/null; then
    POETRY_VERSION=$(poetry --version | grep -oP '\d+\.\d+\.\d+')
    echo -e "${GREEN}✓ Poetry $POETRY_VERSION${NC}"
else
    echo -e "${YELLOW}⚠ Poetry not found (optional)${NC}"
fi

# Check Git
echo -n "Checking Git... "
if command -v git &> /dev/null; then
    GIT_VERSION=$(git --version | grep -oP '\d+\.\d+\.\d+')
    echo -e "${GREEN}✓ Git $GIT_VERSION${NC}"
else
    echo -e "${RED}✗ Git required${NC}"
    exit 1
fi

# Check Docker
echo -n "Checking Docker... "
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | grep -oP '\d+\.\d+\.\d+' | head -1)
    echo -e "${GREEN}✓ Docker $DOCKER_VERSION${NC}"
else
    echo -e "${YELLOW}⚠ Docker not found (optional)${NC}"
fi

# Check Python modules
echo ""
echo "Checking Python modules..."

check_module() {
    echo -n "  $1... "
    if python3 -c "import $1" 2>/dev/null; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo -e "${RED}✗${NC}"
        return 1
    fi
}

MODULES=(
    "openai"
    "groq"
    "ollama"
    "replicate"
    "loguru"
    "git"
    "dotenv"
    "jsonschema"
)

FAILED=0
for module in "${MODULES[@]}"; do
    check_module "$module" || FAILED=$((FAILED + 1))
done

if [ $FAILED -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}Missing $FAILED modules. Run: poetry install${NC}"
fi

# Check syntax
echo ""
echo "Checking Python syntax..."
python3 -m py_compile main.py 2>&1 && echo -e "${GREEN}✓ main.py${NC}" || echo -e "${RED}✗ main.py${NC}"
python3 -m py_compile config.py 2>&1 && echo -e "${GREEN}✓ config.py${NC}" || echo -e "${RED}✗ config.py${NC}"
python3 -m py_compile retry_utils.py 2>&1 && echo -e "${GREEN}✓ retry_utils.py${NC}" || echo -e "${RED}✗ retry_utils.py${NC}"

# Check imports
echo ""
echo -n "Checking imports... "
if python3 -c "import main; from clients import create_client; from retry_utils import retry_with_backoff" 2>/dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    exit 1
fi

# Check .env
echo ""
echo -n "Checking .env file... "
if [ -f .env ]; then
    echo -e "${GREEN}✓ Found${NC}"

    # Check for API keys
    if grep -q "GROQ_API_KEY=your_" .env 2>/dev/null; then
        echo -e "${YELLOW}  ⚠ GROQ_API_KEY not configured${NC}"
    fi
    if grep -q "NVIDIA_API_KEY=your_" .env 2>/dev/null; then
        echo -e "${YELLOW}  ⚠ NVIDIA_API_KEY not configured${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Not found (copy from .env.example)${NC}"
fi

# Check Ollama
echo ""
echo -n "Checking Ollama... "
if curl -s http://localhost:11434 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Running${NC}"

    # Check for llama3 model
    if ollama list 2>/dev/null | grep -q llama3; then
        echo -e "${GREEN}  ✓ llama3 model installed${NC}"
    else
        echo -e "${YELLOW}  ⚠ llama3 model not found (run: ollama pull llama3)${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Not running (optional for local LLM)${NC}"
fi

echo ""
echo "=== Validation Complete ==="
echo ""
echo "Ready to run:"
echo "  python main.py /path/to/repo"
echo ""
echo "For more information:"
echo "  - Quick start: QUICKSTART.md"
echo "  - Full docs: README.md"
echo "  - Deployment: DEPLOY.md"
