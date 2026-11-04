# IncidentLens — AI-First SRE Incident Copilot

A **runnable, locally hosted portfolio demo** built for an AI-First DevOps interview. Shows rules-as-code, real alert ingestion, evidence correlation, optional live LLM interpretation, and a human-approval boundary.

**This is a learning prototype, not a production deployment.** The built-in weather-related examples, services and metrics are fictional. Do not represent them as Tomorrow.io data or systems.

## Quick start (macOS, Linux, Windows with Python)

Requires **Python 3.9+**, with **no external Python packages**.

```bash
cd incidentlens-demo
python3 app.py
```

Open **http://127.0.0.1:8787**. Click one of three incidents, then **Run triage**. Works entirely offline.

### Add real AI analysis (optional)

Requires a valid OpenAI API key with API access and available billing. Without a key the app is **rules-only**, not an LLM agent. Never paste or commit your key into the project.

```bash
export OPENAI_API_KEY='YOUR_API_KEY'
export OPENAI_MODEL='gpt-4.1-mini'
python3 app.py
```

When enabled, each run calls the OpenAI Responses API over HTTPS using the evidence and matched rules. The model returns an evidence-grounded explanation and next investigation steps. Any API error falls back to deterministic rules and is visible in the audit trail.

**Privacy:** only synthetic incidents should be used with external AI unless you have explicit permission to send operational data. This demo does not use any credentials or data from Tomorrow.io.

## Live webhook integration

Send an actual Alertmanager-compatible JSON payload to the local endpoint:

```bash
curl -sS -X POST http://127.0.0.1:8787/api/webhook/alertmanager \
  -H 'Content-Type: application/json' \
  --data-binary @examples/alertmanager_webhook.json | python3 -m json.tool
```

The webhook creates a triage result even without metrics. It **does not invent metrics** that were not supplied. The most recent webhook result is available at `GET /api/latest`.

For a real Prometheus Alertmanager deployment, its webhook receiver can point to `http://<reachable-host>:8787/api/webhook/alertmanager`; this demo binds only to localhost for safety. Do not expose to the internet without authentication and proper hardening.

## Agentic workflow

1. **Ingest:** synthetic scenario or incoming Alertmanager alert.
2. **Gather evidence:** metric snapshot, Kubernetes events and alert metadata where supplied.
3. **Evaluate rules:** custom patterns and read-only commands from `rules.json`.
4. **Synthesize:** optional LLM analysis, constrained to provided evidence.
5. **Human-in-the-loop:** proposed remediation needs approval; acknowledgement is logged; **no action runs**.
6. **Audit:** record how the hypothesis was generated and whether an LLM was used.

## Key files

- `app.py`: Python HTTP server, UI and Alertmanager webhook integration.
- `engine.py`: evidence parsing, rules, and optional OpenAI integration.
- `rules.json`: editable hypothesis patterns and runbook checks.
- `examples/incidents.json`: three fictional weather-pipeline incidents.
- `examples/alertmanager_webhook.json`: webhook sample.
- `static/index.html`: standalone responsive dashboard.
- `tests/test_engine.py`: automated validation of evidence and safety.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

## Suggested 90-second interview demo

> "I wanted to go beyond consuming AI tools, so I built a small incident-triage workflow. It accepts an Alertmanager webhook, runs configurable rules against available evidence, and optionally asks an LLM to explain hypotheses and safe next checks. Notice that it distinguishes evidence from guesses and doesn't perform mutations. I built the integration, orchestration logic, rules and dashboard myself, and tested what happens when telemetry is missing. The next step would be a read-only Prometheus/Kubernetes metrics connector, structured evaluations and approval-gated remediation."

### Before you show it

- Run locally and test the three scenarios.
- If you need to demonstrate true AI reasoning, configure a working API key **ahead of time**; otherwise call it an offline deterministic agent workflow or rules-driven SRE prototype.
- Be honest about any code assistance from ChatGPT: explain the architecture and walk through code you personally understand or modified.
- Emphasize KPI ideas: triage time, % actionable reports, false-positive rates, and operator time saved. Those are *proposed metrics*, not measured improvements.

## Scope and limitations

- **Not production-ready**: no authentication, persistence, proper observability, access controls, distributed system or infrastructure integrations, or automated evaluation pipeline.
- Does not claim verified RCA, no external Prometheus or Kubernetes API connected, no actual auto-remediation.
- HTTP API is intended for local demonstration. Config must be reviewed before connecting any real operations data.
- Model output is not trusted for direct shell execution; no command execution exists in this project.
