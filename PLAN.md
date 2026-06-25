# AI Qlik Sense Master Skill Plan

## Objective

Create an AI Qlik Sense Master Skill that routes Qlik-related requests to the smallest correct skill, tool, or reference set. The master skill should reduce token usage while helping Qlik Sense developers solve issues across scripting, data modelling, frontend expressions, visualisations, performance, reload failures, QSEoW administration, app building, best-practice reviews, and future Qlik-related workflows.

The master skill should act as an orchestrator, not as another large Qlik knowledge base.

The skill will be shared publicly. It should discover specialist Qlik skills and tools from a maintained public catalog of GitHub repositories, while still supporting local/private overrides for a user's environment.

## Core Design Principle

The master skill should load only routing knowledge by default. It should not copy detailed content from specialist skills. Specialist knowledge remains in specialist skills and tools, loaded only when the user request requires it.

Default flow:

1. Classify the user request.
2. Select the narrowest matching Qlik skill.
3. Check the local source catalog snapshot and any configured local overrides.
4. Check whether the selected skill and its tools are available locally.
5. If available, reference and use it.
6. If missing or outdated, produce an install/update plan from declared public GitHub sources.
7. Run the specialist skill's retrieval/search tool before reading large references.
8. Return a solution with evidence, commands, files, or next actions.

## Proposed Skill Name

Folder/name:

```text
ai-qlik-sense-master
```

Display name:

```text
AI Qlik Sense Master Skill
```

## Scope

The master skill should route and coordinate these categories:

| Category | User Need | Likely Specialist Skill |
| --- | --- | --- |
| App development | Load script, data model, expressions, visualisation design, Section Access, QVD patterns | `QlikSense` |
| App diagnostics | Reload failures, logs, local script snapshots, QVF backup/export, live-vs-local script drift | `qlik-sense-diagnostic-tool` |
| Enterprise administration | QSEoW QRS/Engine API, reload tasks, streams, security rules, publishing, schedules, server-level QA | `qlik-sense-enterprise-suite` |
| Komment/write-back | Komment extension, Kaptain service, write-back, partial reload workflows | `QlikSense` first; diagnostic or enterprise skills if server/API evidence is needed |
| Performance optimisation | Reload time, QVD optimisation, app RAM, expression performance, data model shape | `QlikSense`; diagnostic skill when logs or app snapshots are needed |
| Best-practice review | Script/data model/expression/app review against Qlik conventions | `QlikSense`; enterprise suite for formal QA/sign-off |
| App/frontend creation | Building Qlik-adjacent front ends, mashups, embedded analytics, extensions | Future specialist skill, initially route to general coding plus QlikSense references |
| Future domains | New Qlik tools, cloud APIs, extension frameworks, governance packs | Add catalog entry and routing rule |

## Non-Goals

- Do not merge all Qlik skill content into one large skill.
- Do not read whole Qlik reference files unless the relevant specialist skill explicitly requires it as a last resort.
- Do not install or update live-production integrations without explicit user approval.
- Do not make routing depend on vague model memory when a local registry can describe the available skills.
- Do not trust arbitrary repository URLs supplied by a prompt. Install and update only from the configured public catalog or explicit user-approved local overrides.
- Do not require network access for normal routing. A cached catalog snapshot should be enough to route and explain what is missing.

## Public Catalog Model

The master skill should support an ever-growing public list of Qlik Sense skills and tools. The maintained list should live in a public GitHub repository as a versioned catalog file, for example:

```text
https://raw.githubusercontent.com/<owner>/<repo>/<branch>/qlik-skill-catalog.yaml
```

The exact URL remains configurable and should be declared in `references/source-registry.yaml`. The repository should also keep a cached snapshot in `references/public-catalog.yaml` so the skill can work offline with the last known public list.

Catalog responsibilities:

- List public GitHub repositories that host Qlik specialist skills, tools, or reference packs.
- Declare stable IDs, display names, descriptions, routing categories, repository URLs, default branches or tags, install paths, setup commands, and validation commands.
- Mark whether an entry is a skill, tool, reference pack, or composite package.
- Declare compatibility constraints such as minimum Codex skill format version, supported operating systems, and required runtimes.
- Separate public defaults from private/local overrides.

The public catalog should be append-friendly. Adding a new Qlik skill should require adding a catalog entry and route mapping, not changing the master skill's core logic.

Example public catalog entry:

```yaml
catalog_version: 1
updated_at: 2026-06-25
entries:
  - id: qliksense
    kind: skill
    display_name: QlikSense
    description: App development, scripting, data modelling, expressions, visualisation design, Section Access, QVD patterns, and Qlik app performance.
    github:
      repo: https://github.com/<owner>/qlik-sense-skill.git
      ref: main
      path: QlikSense
    install:
      target_name: QlikSense
      setup_commands:
        - tool/setup.py
      validation_commands:
        - tool/qlik_search.py --self-test
    capabilities:
      - app-development
      - expressions
      - load-script
      - data-model
      - performance
```

`source-registry.yaml` should point to the public catalog and define local policy:

```yaml
public_catalog:
  url: https://raw.githubusercontent.com/<owner>/<repo>/<branch>/qlik-skill-catalog.yaml
  cached_snapshot: references/public-catalog.yaml
local_overrides:
  enabled: true
  paths:
    - C:/Users/sean_/.codex/skills
install_policy:
  default_mode: plan-only
  require_approval_for:
    - network
    - writes_outside_workspace
    - overwrite_existing_skill
```

`routing-map.yaml` should remain the single source for routing signals. It may refer to catalog entry IDs, but it should not duplicate GitHub URLs, setup commands, or install policy.

## Repository Structure

Planned structure:

```text
ai-qlik-sense-master/
  SKILL.md
  agents/
    openai.yaml
  references/
    routing-map.yaml
    source-registry.yaml
    public-catalog.yaml
    routing-rules.md
    install-policy.md
    routing-tests.yaml
  scripts/
    qlik_master.py
    validate_registry.py
```

If this repository is intended to become the skill folder directly, create the same files at the repo root:

```text
SKILL.md
agents/openai.yaml
references/routing-map.yaml
references/source-registry.yaml
references/public-catalog.yaml
references/routing-rules.md
references/install-policy.md
references/routing-tests.yaml
scripts/qlik_master.py
scripts/validate_registry.py
```

## Skill Responsibilities

### 1. Request Classification

The master skill should classify each Qlik request by:

- Layer: backend script, data model, frontend expression, visualisation, app lifecycle, platform administration, diagnostics, automation, frontend/mashup, governance.
- Evidence needed: script, expression, screenshot, reload log, QVF, QVD metadata, QRS/Engine API, local files, production environment.
- Risk level: local-only, app-editing, server-admin, production-impacting.
- Required specialist: one skill if possible, multiple only when the problem crosses boundaries.

### 2. Routing and Source Lookup

Maintain separate compact files for routing and sources:

- `routing-map.yaml`: maps request signals to catalog entry IDs and fallback chains.
- `source-registry.yaml`: declares the public catalog URL, cached snapshot path, local override locations, and install/update policy.
- `public-catalog.yaml`: cached public catalog snapshot containing GitHub repositories, package metadata, setup commands, and validation commands.

Example routing fields:

```yaml
routes:
  - id: app-development
    primary: qliksense
    fallback:
      - qliksense
    signals:
      - load script
      - set analysis
      - qvd
      - synthetic key
      - section access
      - visualization
    evidence_needed:
      - script
      - expression
      - dimensions
    risk: local-advice
```

The source lookup should resolve `qliksense` against the cached public catalog first, then apply local overrides. If the catalog is stale and network access is allowed, the tool may refresh the snapshot from the configured public URL.

### 3. Local Skill Detection

Before installing anything, the master tool should check:

- Whether the skill folder exists in known local locations.
- Whether `SKILL.md` exists and has matching frontmatter.
- Whether bundled tools exist.
- Whether tool setup is complete, for example a Python virtual environment or search index.

### 4. On-Demand Install or Repair

If a required specialist skill or tool is missing, the master tool should:

1. Resolve the selected skill ID from `routing-map.yaml`.
2. Resolve the catalog entry from the cached `public-catalog.yaml`.
3. Produce a plan that shows the GitHub repository, ref, target install path, setup commands, validation commands, and overwrite risk.
4. Refuse to install if the source is undefined, not in the catalog, or blocked by policy.
5. Require the agent/user approval path for network access, credentials, production access, or writes outside the workspace.
6. Clone, copy, or install into the configured Codex skills directory only after approval where required.
7. Run the specialist skill's setup command if defined.
8. Validate the installed skill.
9. Retry the original specialist lookup.

Installation should be idempotent. Re-running the command should not duplicate skills or overwrite user changes without explicit approval.

### 5. Token-Control Rules

The master skill should enforce these defaults:

- Load only the master `SKILL.md` and routing references first.
- Prefer registry lookups over reading specialist `SKILL.md` files when only routing is needed.
- After selecting a specialist, read only that specialist's `SKILL.md`.
- Prefer specialist retrieval tools over full reference reads.
- Use narrow searches per sub-question.
- Avoid loading multiple specialist skills unless the request truly crosses domains.
- Summarise findings from specialist tools; do not paste large source excerpts.

### 6. Safety Rules

The master skill should distinguish between advice and action:

- Local file inspection and static analysis are low risk.
- Editing Qlik scripts, app exports, or generated files is medium risk and should preserve backups when possible.
- QSEoW administration, reload task changes, security rules, publishing, imports, and production API calls are high risk and require explicit user intent.
- Network install, Git clone, package install, or access to remote services may require approval depending on the execution environment.

## Tool Requirements

Create a small deterministic CLI tool:

```text
scripts/qlik_master.py
```

Initial commands:

```text
detect
route "<user request>"
sync-catalog
list-sources
check-skill <skill-id>
install-plan <skill-id>
install-skill <skill-id>
doctor
```

### `detect`

Find known local Qlik skills and tool readiness.

Output:

```json
{
  "skills": [
    {
      "id": "qliksense",
      "status": "ready",
      "path": "C:/Users/sean_/.codex/skills/QlikSense",
      "tools": ["tool/qlik_search.py"]
    }
  ]
}
```

### `route`

Classify a user request using `routing-map.yaml`, resolve catalog IDs against `public-catalog.yaml`, and return the recommended skill chain.

Output:

```json
{
  "primary_skill": "qliksense",
  "secondary_skills": [],
  "reason": "Request mentions Set Analysis and chart expression behavior.",
  "evidence_needed": ["expression", "dimensions", "selection context"],
  "risk": "local-advice",
  "availability": {
    "status": "ready",
    "source": "local",
    "path": "C:/Users/sean_/.codex/skills/QlikSense"
  }
}
```

If the selected specialist is not installed, `route` should still return the best catalog match and include an install-plan hint instead of failing.

### `sync-catalog`

Fetch the configured public catalog URL from `source-registry.yaml`, validate it, and update `references/public-catalog.yaml`.

This command requires network access. It should fail without modifying the cached snapshot if the fetched catalog is invalid.

Output:

```json
{
  "status": "updated",
  "catalog_version": 1,
  "entries": 8,
  "source_url": "https://raw.githubusercontent.com/<owner>/<repo>/<branch>/qlik-skill-catalog.yaml"
}
```

### `list-sources`

List catalog entries, local availability, installed versions or refs when detectable, and update status.

Output:

```json
{
  "entries": [
    {
      "id": "qliksense",
      "kind": "skill",
      "catalog_ref": "main",
      "local_status": "ready",
      "path": "C:/Users/sean_/.codex/skills/QlikSense"
    }
  ]
}
```

### `check-skill`

Verify that the selected skill exists and that its tool setup is ready.

### `install-skill`

Install or repair a missing skill using the public catalog and local policy. This command should refuse to use undefined sources.

By default, install behavior should be plan-only unless policy explicitly allows direct installs. The command must not overwrite an existing skill with uncommitted or user-modified files unless the user explicitly approves that operation.

### `install-plan`

Return the exact install/update plan without performing the operation.

Output:

```json
{
  "skill_id": "qliksense",
  "action": "install",
  "source": "https://github.com/<owner>/qlik-sense-skill.git",
  "ref": "main",
  "source_path": "QlikSense",
  "target_path": "C:/Users/sean_/.codex/skills/QlikSense",
  "requires_approval": ["network", "writes_outside_workspace"],
  "setup_commands": ["tool/setup.py"],
  "validation_commands": ["tool/qlik_search.py --self-test"]
}
```

### `doctor`

Validate the routing map, source registry, cached public catalog, known local paths, routing test cases, and tool readiness.

## Routing Heuristics

Start with explicit keyword and context routing:

| Signals | Route |
| --- | --- |
| `Set Analysis`, `Aggr`, `TOTAL`, `Above`, chart expression, KPI wrong, frontend dash/null | `QlikSense` |
| `LOAD`, `Resident`, `ApplyMap`, `Join`, `Keep`, `QVD`, `incremental`, synthetic key, circular reference | `QlikSense` |
| reload failed, log, script snapshot, QVF backup, export app, live script drift | `qlik-sense-diagnostic-tool` |
| QRS, Engine API, reload task, schedule, stream, publish, security rule, virtual proxy, QSEoW | `qlik-sense-enterprise-suite` |
| formal QA, go-live sign-off, data-integrity balancing | `qlik-sense-enterprise-suite` |
| Komment, Kaptain, write-back, partial reload comments | `QlikSense`; escalate to diagnostic/enterprise if logs, services, or security rules are involved |
| extension, mashup, embedded frontend, nebula, capability API | future `qlik-frontend-builder` skill |

Then refine with evidence:

- If the user provides a reload log, prefer diagnostic workflow.
- If the user asks for a platform change, prefer enterprise suite.
- If the user asks for a conceptual fix or expression rewrite, prefer app-development workflow.
- If multiple skills apply, start with diagnosis before administration or edits.

## Build Phases

### Phase 1: Planning and Registry Design

Deliverables:

- `PLAN.md`
- Draft route categories.
- Draft registry schema.
- Draft public catalog schema.
- Decide canonical install locations and source URLs.
- Decide initial public catalog URL.

Acceptance criteria:

- The plan explains how token usage is reduced.
- Each existing Qlik skill has a clear initial routing role.
- Missing source information is marked as `TBD`, not guessed.
- Public GitHub source discovery is defined through a catalog, not hard-coded in the master tool.

### Phase 2: Skill Scaffold

Deliverables:

- `SKILL.md`
- `agents/openai.yaml`
- `references/routing-map.yaml`
- `references/source-registry.yaml`
- `references/public-catalog.yaml`
- `references/routing-rules.md`
- `references/install-policy.md`
- `references/routing-tests.yaml`

Acceptance criteria:

- `SKILL.md` is concise and mostly procedural.
- Detailed routing and install behavior lives in references.
- Frontmatter description clearly triggers for Qlik routing/orchestration.
- Public source metadata is separated from routing rules.

### Phase 3: Master CLI Prototype

Deliverables:

- `scripts/qlik_master.py`
- `scripts/validate_registry.py`
- JSON output for `detect`, `route`, `list-sources`, `check-skill`, `install-plan`, and `doctor`.

Acceptance criteria:

- Tool works without network access for local detection and routing.
- Tool fails clearly when an install source is missing.
- Registry validation catches missing required fields.
- Missing specialists produce install plans rather than dead-end routing results.

### Phase 4: Public Catalog Sync

Deliverables:

- Public catalog schema validation.
- `sync-catalog` command.
- Cached snapshot update workflow.
- Stale catalog warning in `detect`, `route`, and `doctor`.

Acceptance criteria:

- Catalog sync validates before replacing the local snapshot.
- Normal routing works from the cached snapshot when offline.
- A newly added public GitHub repository can be discovered by updating only the public catalog and route map.

### Phase 5: Installation Workflow

Deliverables:

- Idempotent install/repair logic.
- Configurable source registry.
- Setup command support per skill.
- Plan-only install mode.

Acceptance criteria:

- Existing local skills are reused.
- Missing skills are installed only from declared sources.
- User changes are not overwritten without approval.
- Network access and writes outside the workspace are surfaced as approval requirements before action.

### Phase 6: Validation

Test prompts:

1. "My Set Analysis returns zero when I select a month."
2. "This reload failed; here is the log."
3. "Create a QSEoW reload task and schedule it."
4. "Review this app script for QVD optimisation."
5. "Komment write-back is not saving comments."
6. "Build a small embedded analytics frontend for this Qlik app."

Acceptance criteria:

- Each prompt routes to the expected specialist.
- The master skill loads only routing context before selecting a specialist.
- The selected specialist uses its retrieval tool where available.
- Cross-domain requests produce an ordered specialist chain.
- Routing tests are stored in a machine-readable file and checked by `doctor`.

### Phase 7: Future Skill Expansion

When adding a new Qlik skill:

1. Add the skill or tool repository to the maintained public catalog.
2. Add routing signals to `routing-map.yaml`.
3. Add any safety constraints to `install-policy.md`.
4. Run `scripts/qlik_master.py sync-catalog`.
5. Run `scripts/validate_registry.py`.
6. Add at least one routing test prompt.

## Open Decisions

- Canonical install location: likely `C:/Users/sean_/.codex/skills`, but the shared skill should also support repository-local installs and user-specific override paths.
- Public catalog URL and ownership need to be declared.
- Source URLs for each existing Qlik skill need to be added to the public catalog.
- Decide whether the master tool should call Git directly after approval or delegate installs to the existing `skill-installer` workflow.
- Decide whether future Qlik frontend/mashup work deserves a separate specialist skill immediately or after the first real use case.
- Decide whether the route command should remain deterministic keyword matching or include an optional LLM-assisted classification fallback.
- Decide whether catalog entries should pin immutable tags/commit SHAs by default or allow branch tracking with stale/update warnings.

## Immediate Next Step

Create the skill scaffold and initial registry/catalog files, then implement `scripts/qlik_master.py detect`, `route`, `list-sources`, and `install-plan` as the first working slice. Defer live install/update execution until the catalog schema and approval policy are validated.
