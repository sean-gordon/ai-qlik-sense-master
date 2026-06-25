# AI Qlik Sense Master Skill

AI Qlik Sense Master Skill is a small Codex skill that routes Qlik Sense requests to the narrowest useful specialist skill, tool, or reference set.

It is designed as an orchestrator. It does not copy the full Qlik knowledge base into one large skill. Instead, it uses a maintained public catalog of Qlik repositories, routing signals, and tools, then points the agent to the right specialist skill when the request needs deeper Qlik expertise.

## What This Skill Does

This skill helps an AI agent answer questions such as:

- "My Set Analysis returns zero when I select a month."
- "This reload failed; here is the log."
- "Review this app script for QVD optimisation."
- "Komment write-back is not saving comments."
- "Create a QSEoW reload task and schedule it."
- "Build a small embedded analytics frontend for this Qlik app."

The master skill looks up the request against the catalog, chooses the best specialist/tool, checks whether that specialist is installed, and produces a safe install plan when it is missing.

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
2. Score every listed catalog source by routing signals and capabilities.
3. Select the smallest correct specialist/tool.
4. Check local availability.
5. Use the specialist skill if installed.
6. Produce an install plan if the specialist is missing.
7. Avoid loading large references until the selected specialist requires them.

### Catalog Lookup

`qlik-skill-catalog.yaml` is the maintained lookup table. Every public Qlik skill or tool repository that the master skill may select or install must be listed there.

Each catalog entry includes:

- GitHub repository, branch, and source path
- install target and validation commands
- tools exposed by the specialist
- capabilities
- routing signals
- evidence hints and risk level

The router scores those catalog entries at runtime. Adding a new repository to the catalog with routing signals makes it eligible for selection.

Examples:

- Set Analysis, `Aggr`, chart expressions, QVDs, synthetic keys, and Section Access route to `qlik-sense-app-dev`.
- Reload failures, reload logs, script snapshots, and QVF backup/export work route to `qlik-sense-diagnostic-tool`.

### Public Catalog

`qlik-skill-catalog.yaml` is both the local catalog used by the skill and the public catalog file fetched from GitHub by `sync-catalog`.

The starter catalog includes:

- `https://github.com/sean-gordon/qlik-sense-app-dev-skill`
- `https://github.com/sean-gordon/ai-qlik-sense-diagnostic-tool`

More Qlik skills and tools can be added over time by adding catalog entries. The catalog is the source of truth for lookup, install planning, and source listing.

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

Clone this repository into the skill or extension directory used by your agent.

### Windows PowerShell

Claude:

```powershell
git clone https://github.com/sean-gordon/ai-qlik-sense-master.git "$env:USERPROFILE\.claude\skills\ai-qlik-sense-master"
```

Codex:

```powershell
git clone https://github.com/sean-gordon/ai-qlik-sense-master.git "$env:USERPROFILE\.codex\skills\ai-qlik-sense-master"
```

Gemini CLI:

```powershell
$d="$env:USERPROFILE\.gemini\extensions\ai-qlik-sense-master"; git clone https://github.com/sean-gordon/ai-qlik-sense-master.git $d; Copy-Item "$d\SKILL.md" "$d\GEMINI.md" -Force; '{"name":"ai-qlik-sense-master","version":"1.0.0","contextFileName":"GEMINI.md"}' | Set-Content "$d\gemini-extension.json" -Encoding utf8
```

Antigravity:

```powershell
git clone https://github.com/sean-gordon/ai-qlik-sense-master.git "$env:USERPROFILE\.antigravity\skills\ai-qlik-sense-master"
```

Antigravity IDE variant:

```powershell
git clone https://github.com/sean-gordon/ai-qlik-sense-master.git "$env:USERPROFILE\.antigravity-ide\skills\ai-qlik-sense-master"
```

### macOS Or Linux

Claude:

```bash
git clone https://github.com/sean-gordon/ai-qlik-sense-master.git "$HOME/.claude/skills/ai-qlik-sense-master"
```

Codex:

```bash
git clone https://github.com/sean-gordon/ai-qlik-sense-master.git "${CODEX_HOME:-$HOME/.codex}/skills/ai-qlik-sense-master"
```

Gemini CLI:

```bash
d="$HOME/.gemini/extensions/ai-qlik-sense-master"; git clone https://github.com/sean-gordon/ai-qlik-sense-master.git "$d" && cp "$d/SKILL.md" "$d/GEMINI.md" && printf '%s\n' '{"name":"ai-qlik-sense-master","version":"1.0.0","contextFileName":"GEMINI.md"}' > "$d/gemini-extension.json"
```

Antigravity:

```bash
git clone https://github.com/sean-gordon/ai-qlik-sense-master.git "$HOME/.antigravity/skills/ai-qlik-sense-master"
```

Antigravity IDE variant:

```bash
git clone https://github.com/sean-gordon/ai-qlik-sense-master.git "$HOME/.antigravity-ide/skills/ai-qlik-sense-master"
```

For Gemini CLI, the one-liner installs this repository as a Gemini extension and creates `GEMINI.md` plus `gemini-extension.json` so Gemini can load the skill instructions as extension context.

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

The command should return `status: ok`. Any selected source must be present in the catalog.

### Route a Qlik app-development question

```powershell
py scripts\qlik_master.py route "My Set Analysis returns zero when I select a month."
```

Expected primary skill:

```json
{
  "primary_skill": "qlik-sense-app-dev"
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

This shows catalog entries, GitHub source repositories, local availability, installed paths, tools, capabilities, and routing signals.

## CLI Reference

### `detect`

Find locally installed catalog entries and check basic tool readiness.

```powershell
py scripts\qlik_master.py detect
```

### `route "<request>"`

Classify a Qlik request by scoring all catalog entries and return the recommended specialist/tool chain.

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
py scripts\qlik_master.py install-plan qlik-sense-app-dev
```

This command does not install anything.

### `install-skill <skill-id>`

Return the plan-only install result.

```powershell
py scripts\qlik_master.py install-skill qlik-sense-app-dev
```

### `install-skill <skill-id> --execute`

Clone and install a specialist from the approved public catalog.

```powershell
py scripts\qlik_master.py install-skill qlik-sense-app-dev --execute
```

Use this only after reviewing the install plan. The command can perform network access, clone a GitHub repository, copy files into a skills directory, and run setup/validation commands declared by the catalog entry.

If a target already exists, use:

```powershell
py scripts\qlik_master.py install-skill qlik-sense-app-dev --execute --allow-overwrite
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
2. Add routing signals, tools, capabilities, evidence hints, and risk to that catalog entry.
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
  "tools": [
    {
      "id": "example-tool",
      "command": "tool/example.py",
      "purpose": "Describe when the agent should use this tool."
    }
  ],
  "routing": {
    "priority": 50,
    "signals": [
      "example signal"
    ],
    "evidence_needed": [
      "example evidence"
    ],
    "risk": "local-advice",
    "fallback": []
  },
  "capabilities": [
    "example-capability"
  ]
}
```

Keep IDs stable. Route tests, aliases, and installed paths depend on them.

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
- A repository cannot be selected or installed until it is listed in `qlik-skill-catalog.yaml` or the synced public catalog.
- `install-skill --execute` can run specialist setup commands. Some specialist setup commands may download packages or build indexes and can take time.

## License

MIT. See [LICENSE](LICENSE).
