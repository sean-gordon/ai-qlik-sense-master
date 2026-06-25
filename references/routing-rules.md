# Routing Rules

Use deterministic routing before reading specialist material.

## Priority

1. Score every source listed in `qlik-skill-catalog.yaml` before reading specialist material.
2. Prefer diagnostics when the catalog signals match reload logs, script snapshots, QVF backup/export, task failure evidence, QSEoW tool work, or live-vs-local script drift.
3. Prefer the Qlik Sense App Dev Skill when the catalog signals match load script, data model, Set Analysis, chart expression, visualisation, Section Access, QVD, Komment, or performance questions.
4. Only select or install repositories that are listed in the maintained catalog.
5. When a new public Qlik skill is added, add its GitHub source, tools, capabilities, routing signals, evidence hints, risk, and route tests to the catalog.

## Evidence

Ask for the narrowest missing evidence only after routing:

- Expressions: expression text, dimensions, measures, selections, expected result, actual result.
- Load scripts: relevant script section, table names, source/QVD pattern, error line if present.
- Reload failures: reload log, app ID/name, task ID when available, recent script changes.
- QSEoW administration: environment, app/task IDs, intended change, approval context.
- Frontend/mashup: framework, embedding method, authentication pattern, target app.

## Token Control

Read only the selected specialist `SKILL.md` after routing. Use specialist search or retrieval tools before opening large references.
