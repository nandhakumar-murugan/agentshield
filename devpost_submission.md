# ?? Devpost Submission Copy-Paste Guide

**Project Title:** AgentShield: Autonomous Security Guardian for Enterprise AI Agent Fleets  
**Tagline:** An autonomous Zero-Trust & Model Armor security layer protecting enterprise AI agent fleets from prompt injections, tool abuse, and data leaks.  
**Category / Track:** The Fortified Enterprise Fleet  

---

### ?? Inspiration
As enterprises transition from individual chatbots to interconnected fleets of autonomous AI agents (handling finance, HR, and cloud operations), a massive security gap has emerged. Traditional endpoint and network security cannot inspect the internal reasoning loops, capability tokens, or indirect prompt injections targeting AI agents. We built AgentShield to serve as the definitive Zero-Trust security and governance mesh for multi-agent fleets.

---

### ??? What It Does
AgentShield is an autonomous security layer that sits in front of all enterprise AI agents, providing:
1. **Zero-Trust Identity & Ephemeral Capability Tokens:** Issues cryptographically signed (HMAC-SHA256) capability tokens with strict time-to-live (TTL) and role-scoped tool access.
2. **Model Armor & Prompt Injection Defense:** Uses dual-layer scanning (zero-latency regex heuristics + Gemini semantic analysis) to catch indirect prompt injections, jailbreaks, and hidden command overrides in data feeds.
3. **In-Flight Data Loss Prevention (DLP):** Redacts sensitive PII (SSNs, API keys, credentials) before parameters reach backend tools.
4. **Autonomous Mitigation & Quarantining:** Automatically isolates compromised agents, blocks unauthorized privilege escalations, and preserves forensic state.
5. **AuditChain & Gemini Incident Narrator:** Maintains a cryptographically linked (SHA-256) immutable audit ledger and uses Gemini 2.5/3.5 to produce executive SOC 2 and ISO 27001 compliance incident narratives.

---

### ?? How We Built It
- **AI & Agent Frameworks:** Google Gemini 2.5 Flash / Gemini 3.5 via the Google GenAI SDK for semantic intent analysis and incident narrative generation.
- **Backend & API:** Python 3.11, FastAPI, Pydantic v2 for deterministic data contracts.
- **Security Engineering:** HMAC-SHA256 capability tokens, Zero-Trust Policy Decision Point (PDP), and Model Armor pattern matchers.
- **Cloud Infrastructure:** Containerized with Docker and deployed on **Google Cloud Run** for high-availability serverless execution.
- **Frontend Dashboard:** Dark-mode real-time Security Operations Center (SOC) dashboard built with Tailwind CSS and responsive Web APIs.

---

### ?? Challenges We Overcame
1. **Zero-Latency vs. Deep Inspection:** Balancing instantaneous heuristic checks for known injection patterns with asynchronous deep LLM evaluations.
2. **Deterministic Token Scoping:** Designing a lightweight capability token format that prevents replay attacks without introducing complex external database overhead.
3. **Immutable Audit Linking:** Implementing a blockchain-inspired hash chain (`prev_hash` $\rightarrow$ `event_hash`) ensuring that any tampering with audit logs is immediately detected.

---

### ?? Accomplishments That We're Proud Of
- Implemented a 100% functional, 4-agent enterprise security mesh with simulated Finance, HR, and IT Ops agents.
- Developed an automated attack test suite demonstrating instantaneous detection of indirect prompt injections and privilege escalations.
- Deployed seamlessly to Google Cloud Run with comprehensive OpenTelemetry-ready audit event logging.

---

### ?? What We Learned
- Multi-agent enterprise deployments require dynamic identity brokering rather than static API keys.
- Inline DLP is essential because business agents often encounter unstructured PII during standard tool executions.

---

### ?? What's Next for AgentShield
- Integration with Google Cloud Secret Manager for automated dynamic secret rotation.
- Enterprise SSO / OIDC federation for human-in-the-loop escalation workflows.
- Native OpenTelemetry exporter for Google Cloud Trace and Cloud Logging.
