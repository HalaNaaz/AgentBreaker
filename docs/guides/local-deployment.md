# AgentBreaker — Local Deployment & Operations Guide

**Product:** AgentBreaker Research Platform  
**Target Environment:** Local Workstation (Windows 11, macOS, Linux)  
**Python Runtime:** Python 3.12+  
**Node.js / Bun Runtime:** Node.js 18+ or Bun 1.1+

---

## 1. Prerequisites

1. **Python Environment:**
   - Install Python 3.12 or later.
   - Install `uv` (recommended fast package manager) or `pip`.
2. **Frontend Environment:**
   - Install `bun` (recommended) or `node` / `npm`.
3. **Local Target LLM (Optional for Probing):**
   - Ollama running locally at `http://127.0.0.1:11434` (`ollama run llama3`), OR
   - Local OpenAI-compatible server (vLLM, LocalAI, LMStudio) on loopback.

---

## 2. Setting Up the Backend

### Step 1: Install Dependencies
From the repository root:
```powershell
uv sync --all-extras
```
Or via pip:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

### Step 2: Start the FastAPI Backend
Start the local server daemon using the integrated CLI command:
```powershell
uv run agentbreaker api --host 127.0.0.1 --port 8000 --reload
```
Alternatively, invoke uvicorn directly:
```powershell
uv run python -m agentbreaker.api.main --host 127.0.0.1 --port 8000
```

Verify backend health:
```powershell
curl http://127.0.0.1:8000/health
```

The interactive OpenAPI Swagger documentation is available at:
```
http://127.0.0.1:8000/docs
```

---

## 3. Setting Up the Next.js Frontend

### Step 1: Install Frontend Dependencies
```powershell
cd frontend
bun install
```

### Step 2: Environment Configuration
Create or verify `.env.local` in `frontend/`:
```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
NEXT_PUBLIC_WS_URL=ws://127.0.0.1:8000
```

### Step 3: Start the Development Server
```powershell
bun run dev
```
The Next.js workstation will be accessible at:
```
http://127.0.0.1:3000
```

### Step 4: Building for Production
To generate an optimized static production build:
```powershell
bun run build
bun run start
```

---

## 4. End-to-End Operational Workflow

1. **Open Frontend Workstation:** Navigate to `http://127.0.0.1:3000`.
2. **Verify Engine Connection:** Look at the top navbar status indicator (`API: 127.0.0.1:8000 (CONNECTED)`).
3. **Provision Target Endpoint:**
   - Go to **Targets** (`/targets`).
   - Click **Add Target**.
   - Input `ollama-local` with endpoint `http://127.0.0.1:11434/api/generate` and model `llama3:latest`.
   - Click **Test Live Connection** to verify loopback reachability.
4. **Browse Vectors:**
   - Go to **Payloads** (`/payloads`) to review available test vectors.
5. **Explore Mutation Lab:**
   - Go to **Mutation Lab** (`/mutation-lab`).
   - Select a vector, choose Base64 and Rot13 strategies, and preview mutated prompts.
6. **Launch Assessment:**
   - Go to **Assessments** (`/assessments`).
   - Click **Launch New Assessment**.
   - Select your target and click **Create Assessment**.
   - Click **Start** to trigger background execution and watch the live WebSocket event log stream in real time.
7. **Inspect Findings:**
   - Go to **Findings** (`/findings`) to review generated vulnerability/defense determinations.
8. **Export Reports:**
   - Go to **Reports** (`/reports`) to compile and download Markdown, JSON, or interactive HTML reports.
9. **Review Analytics:**
   - Go to **Analytics** (`/analytics`) to inspect macro metrics or compare two historical assessment runs.

