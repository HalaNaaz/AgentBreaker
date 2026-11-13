# AgentBreaker Development Roadmap

AgentBreaker is built incrementally across 8 structured milestones.

| Phase | Milestone | Focus Area | Status |
|:---|:---|:---|:---:|
| **Phase 1** | **Foundation & Packaging** | Repository structure, packaging, dependencies, Pydantic v2 schemas, Security by Design, initial test suite | **Completed** |
| **Phase 2** | **Target Connectors** | Async `BaseConnector`, vLLM/OpenAI-compatible adapter, Ollama connector, Cloud API adapters | **Completed** |
| **Phase 3** | **Attack Engine** | Curated YAML payload repository across 4 suites, async attack runner with rate limiting | **Completed** |
| **Phase 4** | **Payload Mutation Engine** | Base64, Rot13, Leetspeak, markdown delimiter and encoding mutators | **Next** |
| **Phase 5** | **Evaluation Oracle** | Refusal detection, regex pattern matching, canary tracking, tool-call violation analysis | *Pending* |
| **Phase 6** | **CLI Interface** | Typer CLI commands (`scan`, `payloads`, `report`) with Rich progress indicators and tables | *Pending* |
| **Phase 7** | **Reporting Engine** | Jinja2 templates for Markdown, standalone HTML reports, and machine-readable JSON | *Pending* |
| **Phase 8** | **Testing & Deployment** | End-to-end integration tests, mock target servers, Dockerfile, and GitHub Actions CI | *Pending* |
