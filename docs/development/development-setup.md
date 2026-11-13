# AgentBreaker Developer Environment Setup

**Product:** AgentBreaker  
**Brand:** AshlynxCyber Security Systems  
**Audience:** Core Maintainers, Contributors, Open-Source Developers

---

## 1. Prerequisites

1. **Python 3.12+**
2. **`uv` (v0.6+)**: Fast Python project manager.
3. **Bun (v1.1+)**: JavaScript runtime and package manager.
4. **Node.js 20 LTS**: Required for Next.js build runtime.
5. **Git**: Version control.

---

## 2. Setting Up the Workspace

```bash
# Clone the repository
git clone https://github.com/HalaNaaz/AgentBreaker.git
cd AgentBreaker

# Synchronize virtual environment with dev extras
uv sync --frozen --extra dev

# Install frontend dependencies
cd frontend
bun install --frozen-lockfile
cd ..
```

---

## 3. Code Style & Pre-Commit Quality Checks

AgentBreaker enforces strict code style using `ruff`:

```bash
# Check linting rules
uv run ruff check .

# Check code formatting without modifying files
uv run ruff format --check .

# Automatically format Python code
uv run ruff format .
```

### Ruff Configuration Highlights
- Line length: 100 characters.
- Target Python version: `py311` / `py312`.
- Rules selected: Pyflakes (`F`), pycodestyle (`E`, `W`), isort (`I`), pep8-naming (`N`), flake8-bugbear (`B`), flake8-bandit security checks (`S`).

---

## 4. Frontend Code Quality

```bash
cd frontend

# Verify TypeScript types without emitting artifacts
bun run type-check

# Run ESLint on all Next.js pages and components
bun run lint

# Audit package dependencies
bun audit
```

---

## 5. Development Servers

To run both services concurrently during feature development:

```bash
# Terminal 1: Launch FastAPI Backend in reload mode
uv run uvicorn agentbreaker.api.app:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2: Launch Next.js Development Server
cd frontend
bun run dev
```

The workstation UI is available at `http://localhost:3000`.

