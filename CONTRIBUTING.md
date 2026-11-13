# Contributing to AgentBreaker

Thank you for your interest in contributing to **AgentBreaker**, an open-source AI Security Research & Evaluation Framework by AshlynxCyber.

## Security Notice

AgentBreaker is intended exclusively for authorized security research, red teaming, and model evaluation under controlled environments. Contributions introducing malicious exploits or violating our [Acceptable Use Policy](ACCEPTABLE_USE.md) will be rejected.

## Code of Conduct

All contributors and participants are expected to adhere to our [Code of Conduct](CODE_OF_CONDUCT.md).

## Development Setup

AgentBreaker requires:
- Python 3.12+ (managed with `uv`)
- Bun 1.1+ (for Next.js frontend development)

### Backend Setup

```bash
# Clone the repository
git clone https://github.com/HalaNaaz/AgentBreaker.git
cd AgentBreaker

# Install backend dependencies
uv sync

# Run tests
uv run pytest

# Check code formatting and linting
uv run ruff check .
uv run ruff format --check .
```

### Frontend Setup

```bash
cd frontend
bun install --frozen-lockfile
bun run type-check
bun run lint
bun run build
```

## Pull Request Guidelines

1. **Focus:** Ensure changes are focused, well-tested, and documented.
2. **Quality:** Ensure 100% test pass rate with strict coverage, zero lint/formatting issues, and zero dependency audit vulnerabilities (`bun audit`).
3. **Target Secrets:** Never commit real API keys, credentials, or production tokens.
4. **Commits:** Write clear, conventional commit messages (e.g., `feat:`, `fix:`, `docs:`, `test:`).
