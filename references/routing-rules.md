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

## Partial Reload, Section Access, and Komment Write-Back

For QSEoW apps with Komment/QIX write-back plus a partial-reload model, route diagnostics and
read `references/qseow-partial-reload-section-access-playbook.md` when the request matches:

- "partial reload does not update, but full reload does" (likely an unprefixed load in the
  partial-executed path aborting with `Table 'X' not found`).
- "Komment write-back saved / QVD updated but the front-end reverts" (the fold-back partial
  reload is failing — check `CheckScriptSyntax` first, then probe a partial reload).
- "`Table 'SA_AdminUsers' not found`" or Section Access breaking only on partial reload
  (guard the Section Access build with `If not IsPartialReload()`).

Key facts the playbook encodes: a partial reload runs only `Add`/`Replace`/`Merge` loads; a
reload compiles the whole script (including code after `Exit Script`) before running; and you
can trigger/inspect a partial reload via the Engine API `DoReloadEx({qPartial:true})` +
`GetProgress` (QRS task start only does full reloads).
