# AgentBreaker Strategic Development Roadmap

**Product:** AgentBreaker  
**Brand:** AshlynxCyber Security Systems  
**Audience:** Community Contributors, Enterprise Users, Researchers  
**Status:** Post-Publication Baseline (Phases 1–9 Complete)

---

## 1. Completed Milestones

- [x] **Phase 1: Architecture, Threat Model & Safe Payloads Baseline**
- [x] **Phase 2: Target Connector Abstraction (vLLM, Ollama, Cloud APIs, Custom HTTP)**
- [x] **Phase 3: Attack Execution Engine & Orchestrator**
- [x] **Phase 4: Adversarial Mutation & Obfuscation Engine**
- [x] **Phase 5: Multi-Tier Evaluation Oracle & Verdict Aggregator**
- [x] **Phase 6: Typer CLI Application & Terminal Workflow**
- [x] **Phase 7: Reporting Engine (OWASP Top 10, MITRE ATLAS, JSON/MD/HTML)**
- [x] **Phase 8: FastAPI Local Daemon & Next.js 15 Tactical Workstation Integration**
- [x] **Phase 9: Open-Source Governance, OS-Backed Credential Storage & GitHub Actions CI**

---

## 2. Near-Term Roadmap (v0.2 – v0.3)

### Multi-Turn Dialogue Assessments
- Stateful multi-turn conversation trees allowing iterative prompt injection and progressive context manipulation.
- Automated tree-of-attacks evaluation (TAP).

### Extended Agent Tool Simulations
- Deep mock environment simulation for Model Context Protocol (MCP) servers.
- Automated tool poisoning evaluation for agentic memory stores and retrieval pipelines.

### Enhanced Autonomous Adaptive Mutation
- Evolutionary genetic algorithm mutators optimizing for bypass probability while preserving semantic intent.
- Model-guided iterative evasion scoring.

---

## 3. Long-Term Vision (v1.0)

- **Continuous CI/CD AI Safety Gate:** Dedicated GitHub Action and GitLab CI integration for automated pipeline blocking on AI safety regressions.
- **Enterprise Distributed Worker Nodes:** Scale evaluations across distributed worker fleets for large-scale enterprise model benchmarking.
- **Dynamic Guardrail Validation:** Active auditing of third-party guardrails (NeMo Guardrails, Llama Guard, Guardrails AI).

