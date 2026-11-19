<div align="center">

# 🐾 Android-AutoTests

**AI-driven Android UI automation testing platform**

[![CI](https://github.com/Kahoku-lazy/Android-AutoTests/actions/workflows/ci-phase1.yml/badge.svg?branch=Kahoku)](https://github.com/Kahoku-lazy/Android-AutoTests/actions/workflows/ci-phase1.yml)
[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-6.0.6-green.svg)](https://www.djangoproject.com/)
[![Vue](https://img.shields.io/badge/Vue-3.5-brightgreen.svg)](https://vuejs.org/)
[![AgentScope](https://img.shields.io/badge/AgentScope-2.0.9%2B-orange.svg)](https://docs.agentscope.io/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**English** | [中文](README.md)

</div>

> ⚠️ Early-stage project (0.x): APIs and features may change without backward-compatibility guarantees. Documentation is currently Chinese-first; this page is an English overview.

## What is it?

Android-AutoTests is an **AI Agent platform for Android test engineers**. One Agent role = **Model + Harness**, with a three-layer architecture:

| Layer | Stack | Responsibility |
| --- | --- | --- |
| **Frontend** | Vue 3.5 + Vite 5 + Element Plus + Pinia + TypeScript | Visualization of tasks, costs, capabilities and run status (10 business modules, hand-drawn "Doodle Craft" theme) |
| **Backend** | Python 3.13 · Django 6.0.6 + DRF + Daphne | Task dispatch, auth and accounting; 12 apps, OpenAPI contract baseline |
| **Engines** | AgentScope ≥ 2.0.9 + ADB | The capability core: agent runtime, harness primitives, device / serial / vision support |

The primary scenario: published **SOP workflows** (an *executor* role operates the device, a *verifier* role checks results with read-only tools) run end-to-end, and results flow back into **tasks** and **test reports**.

## Key features

- **Device pool** — USB / WiFi ADB, occupation locks, heartbeats; same-device serial queue, cross-device parallelism
- **Case management** — automation / functional test libraries; project → case → steps
- **AI assistant** — model & agent configuration (executor / verifier / planner), SOP workflows, test conversations and evaluation
- **Task list & reports** — submit / rerun / close tasks from published workflows; read-only report ledger; failure → bug ticket
- **Knowledge base** — module registry, read-only retrieval, automatic evaluation
- **Ops console & usage ledger** — user / agent / model administration; one record per model call, cost dashboards
- **Security hygiene** — API keys only from root `.env` (never in UI or code); CI credential gates; secret scanning + push protection enabled

Out of scope for now: iOS / Web / API test engines, device cloud, multi-team isolation, OAuth / SSO, distributed execution clusters.

## Quick start

Requires Python 3.13, Node.js, and MySQL (or SQLite).

```bash
git clone https://github.com/Kahoku-lazy/Android-AutoTests.git
cd Android-AutoTests
pip install -r requirements.txt
cd frontend && npm install && cd ..
cp .env.example .env        # then fill in your model API keys
python run.py setup         # installs project-local adb (first run)
python run.py start         # start the platform; status / stop also available
python run.py check         # local quality gates (same checks as CI)
```

## Contributing

All changes go through **feature branch → PR → green CI** into the single trunk `Kahoku` (branch protection enforced, admins included).

- Contribution guide: [CONTRIBUTING.md](CONTRIBUTING.md) (Chinese-first)
- Code of conduct: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- Security reports: **private channel only**, see [SECURITY.md](SECURITY.md)
- Questions & ideas: [Discussions](https://github.com/Kahoku-lazy/Android-AutoTests/discussions)
- Changelog: [CHANGELOG.md](CHANGELOG.md) · Releases: [v0.1.0](https://github.com/Kahoku-lazy/Android-AutoTests/releases/tag/v0.1.0)

## License

[MIT](LICENSE)