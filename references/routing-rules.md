# Routing Rules

Use deterministic routing before reading specialist material.

## Priority

1. Prefer diagnostics when the user provides or asks about reload logs, script snapshots, QVF backup/export, task failure evidence, or live-vs-local script drift.
2. Prefer the Qlik Sense App Dev Skill for load script, data model, Set Analysis, chart expression, visualisation, Section Access, QVD, and performance questions.
3. Prefer enterprise administration only when the user explicitly asks for QSEoW platform/server changes such as QRS, Engine API, reload tasks, schedules, streams, publishing, security rules, virtual proxies, or formal QA/sign-off.
4. Prefer the Qlik Sense App Dev Skill first for Komment/write-back unless logs, services, security rules, or platform APIs are needed.
5. For future skills that are not installed or not in the catalog, return the intended skill ID plus the fallback chain.

## Evidence

Ask for the narrowest missing evidence only after routing:

- Expressions: expression text, dimensions, measures, selections, expected result, actual result.
- Load scripts: relevant script section, table names, source/QVD pattern, error line if present.
- Reload failures: reload log, app ID/name, task ID when available, recent script changes.
- QSEoW administration: environment, app/task IDs, intended change, approval context.
- Frontend/mashup: framework, embedding method, authentication pattern, target app.

## Token Control

Read only the selected specialist `SKILL.md` after routing. Use specialist search or retrieval tools before opening large references.
