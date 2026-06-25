# AI Qlik Sense Master Skill

AI Qlik Sense Master Skill is a small Codex skill that routes Qlik Sense requests to the narrowest useful specialist skill, tool, or reference set.

It is designed as an orchestrator. It does not copy the full Qlik knowledge base into one large skill. Instead, it keeps routing and source metadata locally, then points the agent to the right specialist skill when the request needs deeper Qlik expertise.

## What This Skill Does

This skill helps an AI agent answer questions such as:

- "My Set Analysis returns zero when I select a month."
- "This reload failed; here is the log."
- "Review this app script for QVD optimisation."
- "Komment write-back is not saving comments."
- "Create a QSEoW reload task and schedule it."
- "Build a small embedded analytics frontend for this Qlik app."

The master skill classifies the request, chooses a specialist, checks whether that specialist is installed, and produces a safe install plan when it is missing.

## Why It Exists

Qlik Sense work spans several different domains:

- Load scripts and QVD patterns
- Data model design
- Set Analysis and chart expressions
- Visualisation behaviour
- Reload failures and logs
- QVF backup and export workflows
- QSEoW administration
- Komment/write-back workflows
- Embedded analytics, mashups, and extensions

Loading every specialist reference for every Qlik question wastes context and makes the agent less precise. This skill keeps the default context small and routes to detailed material only when needed.

## Repository Contents

```text
.
|-- SKILL.md
|-- README.md
|-- LICENSE
|-- qlik-skill-catalog.yaml
|-- references/
|   |-- install-policy.md
|   |-- routing-map.yaml
|   |-- routing-rules.md
|   |-- routing-tests.yaml
|   `-- source-registry.yaml
|-- scripts/
|   |-- qlik_master.py
|   `-- validate_registry.py
`-- .gitignore
```

## Core Concepts

### Master Skill

`SKILL.md` contains the concise instructions an AI agent loads when this skill triggers.

It tells the agent to:

1. Classify the Qlik request.
2. Read the routing map.
3. Select the smallest correct specialist.
4. Check local availability.
5. Use the specialist skill if installed.
6. Produce an install plan if the specialist is missing.
7. Avoid loading large references until the selected specialist requires them.

### Routing Map

`references/routing-map.yaml` maps request signals to specialist skill IDs.

Examples:

- Set Analysis, `Aggr`, chart expressions, QVDs, synthetic keys, and Section Access route to `qliksense`.
- Reload failures, reload logs, script snapshots, and QVF backup/export work route to `qlik-sense-diagnostic-tool`.
- QSEoW administration and QRS/Engine API work currently route to `qlik-sense-enterprise-suite`, with fallback behaviour until that public catalog entry is added.

### Public Catalog

`qlik-skill-catalog.yaml` is both the local catalog used by the skill and the public catalog file fetched from GitHub by `sync-catalog`.

The starter catalog includes:

- `https://github.com/sean-gordon/qlik-ai-skill`
- `https://github.com/sean-gordon/ai-qlik-sense-diagnostic-tool`

More Qlik skills and tools can be added over time by adding catalog entries and route mappings.

### Source Registry

`references/source-registry.yaml` tells the master tool where to fetch the public catalog and where to look for local skills.

The default public catalog URL is:

```text
https://raw.githubusercontent.com/sean-gordon/ai-qlik-sense-master/main/qlik-skill-catalog.yaml
```

### Install Policy

`references/install-policy.md` documents the safety model:

- Normal routing works offline from the cached catalog.
- Prompt-supplied repository URLs are not trusted by default.
- Network access, Git clone, package install, writes outside the workspace, and overwrites require explicit approval.
- Install commands default to plan-only unless `install-skill --execute` is used.

## Installation

Install this folder into your Codex skills directory.

On Windows:

```powershell
git clone https://github.com/sean-gordon/ai-qlik-sense-master.git "$env:USERPROFILE\.codex\skills\ai-qlik-sense-master"
```

On macOS or Linux:

```bash
git clone https://github.com/sean-gordon/ai-qlik-sense-master.git "${CODEX_HOME:-$HOME/.codex}/skills/ai-qlik-sense-master"
```

The same folder can also be copied into compatible skill locations for other agent tools that understand Codex-style skills.

## Quick Start

Run commands from the skill root.

### Validate the skill

```powershell
py scripts\qlik_master.py doctor
```

Expected result:

```json
{
  "status": "ok",
  "errors": []
}
```

Warnings for future skills such as `qlik-sense-enterprise-suite` or `qlik-frontend-builder` are acceptable until those entries are added to the public catalog.

### Route a Qlik app-development question

```powershell
py scripts\qlik_master.py route "My Set Analysis returns zero when I select a month."
```

Expected primary skill:

```json
{
  "primary_skill": "qliksense"
}
```

### Route a reload failure

```powershell
py scripts\qlik_master.py route "This reload failed; here is the log."
```

Expected primary skill:

```json
{
  "primary_skill": "qlik-sense-diagnostic-tool"
}
```

### List known public sources

```powershell
py scripts\qlik_master.py list-sources
```

This shows catalog entries, GitHub source repositories, local availability, and installed paths.

## CLI Reference

### `detect`

Find locally installed catalog entries and check basic tool readiness.

```powershell
py scripts\qlik_master.py detect
```

### `route "<request>"`

Classify a Qlik request and return the recommended specialist chain.

```powershell
py scripts\qlik_master.py route "Review this Qlik app script for QVD optimisation."
```

If the selected specialist is missing, the route output includes an `install_plan_hint`.

### `list-sources`

List public catalog entries and local status.

```powershell
py scripts\qlik_master.py list-sources
```

### `install-plan <skill-id>`

Show the exact GitHub source, ref, target path, setup commands, validation commands, and approval requirements for a specialist.

```powershell
py scripts\qlik_master.py install-plan qliksense
```

This command does not install anything.

### `install-skill <skill-id>`

Return the plan-only install result.

```powershell
py scripts\qlik_master.py install-skill qliksense
```

### `install-skill <skill-id> --execute`

Clone and install a specialist from the approved public catalog.

```powershell
py scripts\qlik_master.py install-skill qliksense --execute
```

Use this only after reviewing the install plan. The command can perform network access, clone a GitHub repository, copy files into a skills directory, and run setup/validation commands declared by the catalog entry.

If a target already exists, use:

```powershell
py scripts\qlik_master.py install-skill qliksense --execute --allow-overwrite
```

### `sync-catalog`

Fetch the public catalog from GitHub and replace the cached snapshot only if validation passes.

```powershell
py scripts\qlik_master.py sync-catalog
```

This requires network access.

### `doctor`

Validate the source registry, cached catalog, route map, routing tests, and local detection.

```powershell
py scripts\qlik_master.py doctor
```

## Adding a New Qlik Specialist

1. Add a new entry to `qlik-skill-catalog.yaml`.
2. Add route signals to `references/routing-map.yaml`.
3. Add at least one route test to `references/routing-tests.yaml`.
4. Run:

```powershell
py scripts\qlik_master.py doctor
```

5. Confirm the new route returns the expected primary skill.

## Catalog Entry Format

Each public catalog entry should include:

```json
{
  "id": "example-skill-id",
  "kind": "skill",
  "display_name": "Example Skill",
  "description": "Short explanation of what the skill does.",
  "github": {
    "repo": "https://github.com/sean-gordon/example-skill.git",
    "ref": "main",
    "path": "."
  },
  "install": {
    "target_name": "example-skill-id",
    "setup_commands": [],
    "validation_commands": [
      "SKILL.md"
    ]
  },
  "capabilities": [
    "example-capability"
  ]
}
```

Keep IDs stable. Route rules and installed paths depend on them.

## Security Notes

This repository intentionally avoids storing credentials, Qlik certificates, app exports, reload logs, environment files, or customer data.

Before publishing changes, run a local scan for common sensitive values:

```powershell
rg -n -i "password|secret|token|apikey|api_key|client_secret|private key|certificate|BEGIN RSA|BEGIN OPENSSH|connectionstring|qlik.*(cert|key)" .
```

Also check for generated files:

```powershell
git status --short
```

Do not commit:

- `.env` files
- Qlik certificates or private keys
- QVF app exports
- Reload logs containing customer data
- Local virtual environments
- Search indexes
- Python caches
- Tool output or temporary clone folders

## Current Limitations

- The starter public catalog contains only the first two specialist repositories.
- `qlik-sense-enterprise-suite` and `qlik-frontend-builder` routes are present as future routes and will warn until their public catalog entries are added.
- `install-skill --execute` can run specialist setup commands. Some specialist setup commands may download packages or build indexes and can take time.

## License

MIT. See [LICENSE](LICENSE).
