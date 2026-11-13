# AgentBreaker Installation Guide

**Product:** AgentBreaker  
**Brand:** AshlynxCyber Security Systems  
**Audience:** Security Engineers, Penetration Testers, ML Researchers  
**Supported Platforms:** Windows 11 / 10, macOS (Apple Silicon / Intel), Linux (Ubuntu 22.04+)

---

## 1. Prerequisites

Before installing AgentBreaker, ensure your system has the following core tools:

1. **Python 3.12+**: AgentBreaker utilizes modern Python features (typed syntax, standard library improvements).
2. **`uv` Package Manager (Recommended)**: Ultra-fast, reliable Python package and environment manager.
   ```bash
   # Windows (PowerShell)
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

   # macOS / Linux (curl)
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
3. **Bun (Optional, for Visual Dashboard)**: Fast JavaScript package manager and runtime.
   ```bash
   # Windows (PowerShell)
   powershell -c "irm bun.sh/install.ps1 | iex"

   # macOS / Linux
   curl -fsSL https://bun.sh/install | bash
   ```
4. **Node.js 20 LTS (Optional, required for Next.js build runtime if using GUI)**:
   - Ensure Node.js 20.x is available on your system `PATH`.

---

## 2. Installation Workflow

### Step 1: Clone the Repository
```bash
git clone https://github.com/HalaNaaz/AgentBreaker.git
cd AgentBreaker
```

### Step 2: Set Up Backend Python Environment
Using `uv`, synchronize the virtual environment with the frozen lockfile:
```bash
# Production runtime only
uv sync --frozen

# Or with development and testing tools (recommended for researchers)
uv sync --frozen --extra dev
```

### Step 3: Verify CLI Installation
Run the system diagnostic check:
```bash
uv run agentbreaker system info
```
Expected output displays:
- AgentBreaker version (`0.1.0.dev1`)
- Python runtime (`3.12.x`)
- OS vault status (e.g., `Windows DPAPI Available: True` or `Keyring Available: True`)
- Active storage path (defaults to `~/.agentbreaker`)

### Step 4: Set Up Frontend Tactical Dashboard (Optional)
If you wish to use the graphical workstation:
```bash
cd frontend
bun install --frozen-lockfile
bun run type-check
```

---

## 3. Environment Configuration

Copy the example environment templates:
```bash
# Root backend configuration
cp .env.example .env

# Frontend configuration (if using GUI)
cp frontend/.env.example frontend/.env.local
```

### Key Environment Variables
| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `AGENTBREAKER_HOME` | `~/.agentbreaker` | Root directory for storing targets, results, and reports. |
| `AGENTBREAKER_HOST` | `127.0.0.1` | Loopback IP address for the local daemon. |
| `AGENTBREAKER_PORT` | `8000` | Port for the local FastAPI daemon. |
| `AGENTBREAKER_API_KEY` | *(empty)* | Optional local pre-shared token for daemon authorization. |
| `NEXT_PUBLIC_API_URL` | `http://127.0.0.1:8000` | Frontend backend API URL. |
| `NEXT_PUBLIC_WS_URL` | `ws://127.0.0.1:8000` | Frontend backend WebSocket telemetry URL. |

---

## 4. Upgrading & Maintenance

To pull the latest updates and update your locked environment:
```bash
git pull origin main
uv sync --frozen --extra dev
cd frontend && bun install --frozen-lockfile
```

