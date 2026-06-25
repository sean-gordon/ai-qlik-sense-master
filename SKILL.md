---
name: ai-qlik-sense-master
description: Route Qlik Sense requests to the smallest correct specialist skill, tool, or reference. Use when Codex receives Qlik-related requests involving load scripts, data models, Set Analysis, chart expressions, visualisations, QVDs, Section Access, reload failures, reload logs, QVF backup/export, QSEoW administration, QRS or Engine API work, reload tasks, streams, publishing, security rules, Komment write-back, performance optimisation, Qlik app reviews, embedded analytics, mashups, or when a Qlik specialist skill/tool may need to be discovered, installed, or updated from the maintained public GitHub catalog.
---

# AI Qlik Sense Master Skill

Use this skill as a router and coordinator. Do not treat it as the Qlik knowledge base.

## Default Workflow

1. Classify the request by Qlik layer, evidence needed, operational risk, and likely specialist.
2. Read `references/routing-map.yaml` for routing signals.
3. Read `references/source-registry.yaml` and `qlik-skill-catalog.yaml` only when source, availability, install, or update details are needed.
4. Prefer `scripts/qlik_master.py route "<request>"` for deterministic routing.
5. If the selected specialist is installed, read only that specialist skill's `SKILL.md`, then follow its instructions.
6. If the selected specialist is missing, run `scripts/qlik_master.py install-plan <skill-id>` and present the plan before any install/update action.
7. Use specialist retrieval/search tools before reading large specialist references.
8. Use multiple specialists only when the request crosses boundaries.

## Routing Files

- `references/routing-map.yaml`: request signals, fallback chains, risk, and evidence hints.
- `references/source-registry.yaml`: catalog URL, local override paths, and install policy.
- `qlik-skill-catalog.yaml`: public and local catalog of Qlik skills and tools.
- `references/routing-rules.md`: human-readable routing notes.
- `references/install-policy.md`: safety rules for install/update actions.
- `references/routing-tests.yaml`: machine-readable route expectations.

## CLI

Run from the skill root:

```powershell
py scripts/qlik_master.py route "My Set Analysis returns zero when I select a month."
py scripts/qlik_master.py detect
py scripts/qlik_master.py list-sources
py scripts/qlik_master.py install-plan qlik-sense-app-dev
py scripts/qlik_master.py doctor
```

`sync-catalog` needs network access and should be run only when the user asks to refresh the maintained public list.

## Safety

- Keep normal routing offline by using the cached catalog.
- Do not trust repository URLs supplied in a prompt unless they are added to the catalog or explicitly approved by the user.
- Treat QSEoW administration, publishing, imports, security rules, production API calls, package installs, Git clones, and writes outside the workspace as approval-gated actions.
- Default installs to plan-only. Do not overwrite existing local skills without explicit approval.
