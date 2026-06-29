# QSEoW Partial Reload, Section Access, and Komment Write-Back Playbook

Field-tested diagnostic notes for QSEoW apps that use Komment/QIX write-back plus a
partial-reload data model. Route here when the symptoms below appear; hand the deep
script work to the Qlik Sense App Dev specialist and the live-engine work to the
Qlik Sense Diagnostic Tool.

## Core rule: what a partial reload actually runs

A partial reload executes **only** `LOAD`/`SELECT` statements prefixed with `Add`,
`Replace`, or `Merge`. Every other `LOAD`, `JOIN`, `CONCATENATE`, inline load, and
resident load is **skipped**. Control statements (`IF`, `FOR`, `LET`, `SET`, `DROP`,
`STORE`, `TRACE`) still run. Existing in-memory tables persist from the last full reload.

Consequences that cause real production failures:

- A block that builds tables with **unprefixed** `INLINE`/`Resident`/`JOIN` loads is
  skipped on partial reload, so those tables are never created. A later
  `Join (ThatTable) …` or `Resident ThatTable` then aborts with
  **`Table 'X' not found`**, and the abort **rolls back** any earlier rebuild that had
  already succeeded in the same reload (e.g. a `[QlikUsers]` write-back merge).
  Net symptom: *full reload works, partial reload does not.*
- Fix: either wrap the full-reload-only block in `If not IsPartialReload() then … End If;`,
  or prefix its loads with `Add`/`Replace` so they run on partial too. Guarding is the
  safer default for heavy/sensitive blocks (e.g. Section Access).

## Section Access GRID builds belong in the full-reload path

A Section Access GRID build (inline `ADMIN` rows, `SA_AllKeys`, `SA_Access_Build`,
joins onto the store×date grid, `Section Access; … Section Application;`) is built almost
entirely from unprefixed loads. If it sits in the partial-executed path it will fail on
partial with `Table 'SA_AdminUsers' not found` (or the first such table).

Recommended pattern:

```qvs
///$tab Security
// Section Access GRID build runs on FULL reload only. Its tables use unprefixed
// INLINE/Resident loads, which a partial reload skips -> 'table not found' abort.
If not IsPartialReload() then
    ... build Map_AFBStore / StoreDateOwner / SA_* tables ...
    Section Access;
    SA_Access: NoConcatenate LOAD ACCESS, USERID, STOREDATEKEY Resident SA_Access_Build;
    Section Application;
    Drop Table SA_Access_Build; Drop Table StoreDateOwner; ...
End If;
```

Keep the write-back merge / table rebuild (the part that *must* refresh on a Komment
submit) **above and outside** this guard so it still runs on partial.

**Trade-off to state explicitly:** with the guard, a partial reload refreshes the
write-back *field value display* immediately, but the Section Access *reduction*
(what each user may see) only rebuilds on a full reload. If access scope must change
without a full reload, make the SA build partial-safe instead — and test on a copy
(`Drop Tables` inside Section Access has its own partial-reload quirks).

## Komment write-back "saved but reverts" — how to diagnose

The Komment/QIX extension on Submit does two independent things:

1. Writes the write-back QVD **directly through the engine (QIX)** — this happens even if
   no reload runs, which is why *the QVD is updated/created* on the file system.
2. Triggers a **partial reload** to fold the change into the model (`[QlikUsers]`,
   `[Store Data]`, etc.).

So "the QVD has my change but the front-end reverts after save" almost always means the
**fold-back partial reload is failing**, not the write. Two common causes:

- **Script does not compile.** A reload compiles the *entire* script — including dead code
  after `Exit Script` — before executing anything. A single syntax error anywhere aborts
  every reload (full and partial). Watch for a stray token at EOF, duplicated generated
  blocks appended after `Exit Script`, and **`GROUP BY` combined with `ORDER BY`** in one
  `LOAD` (illegal in Qlik). Validate with engine `CheckScriptSyntax` (`check-script`).
- **Runtime abort on partial.** See the unprefixed-load / Section Access failure above.

### Latest-row merge pattern (deterministic)

For "keep the most recent write-back per key", do **not** rely on `FirstValue()` + load
order, and do not combine `GROUP BY` with `ORDER BY`. Use:

```qvs
FirstSortedValue([Komment_x.Company Allocation], -Num([Komment_x.CreatedAt])) AS [..._Agg]
... RESIDENT [Komment_x] GROUP BY [QlikUsers_id];
```

If `CreatedAt` is ISO text (`2026-06-26T13:39:26.967Z`), parse it robustly before `Num()`,
e.g. `Alt(Num(CreatedAt), Num(Timestamp#(SubField(SubField(Replace(CreatedAt,'T',' '),'+',1),'Z',1),'YYYY-MM-DD hh:mm:ss[.fff]')), 0)`,
and add a monotonic load-sequence tie-breaker.

## Triggering and inspecting a partial reload from the Engine API

QRS `task/<id>/start` runs a **full** reload only. To exercise and debug a **partial**
reload directly (without the UI), open the doc with data over the Engine websocket and call:

```
DoReloadEx  ->  [{"qMode": 0, "qPartial": true, "qDebug": false}]
GetProgress ->  [0]
```

The `DoReloadEx` result gives `qSuccess`, `qErrorData`, and `qScriptLogFile` (the exact
log path), and `GetProgress` returns the failing statement text — this is how you catch a
`Table 'X' not found` partial-reload abort in seconds instead of waiting on a full reload.
Read a single user's value back with `EvaluateEx` on the open doc handle, e.g.
`=Concat(DISTINCT If(WildMatch([QlikUsers_userId],'*marsh*'), [QlikUsers_userId] & ' => ' & [Company Allocation]), Chr(10))`.

Diagnosis-only runs should **not** call `DoSave`; note that the script's `STORE` statements
still write their QVDs during the reload, so avoid pushing synthetic write-back payloads
through production.

## Quick triage table

| Symptom | Likely cause | First check |
| --- | --- | --- |
| Full reload updates, partial does not | Unprefixed load in partial path aborts reload | `DoReloadEx` partial + `GetProgress` for `Table 'X' not found` |
| QVD updates but front-end reverts | Fold-back reload failing (syntax or runtime) | `check-script`; then partial-reload probe |
| Reload fails immediately, any mode | Script does not compile | `CheckScriptSyntax`; look after `Exit Script`, `GROUP BY`+`ORDER BY`, EOF tokens |
| `Table 'SA_AdminUsers' not found` on partial | Section Access build runs on partial | Guard SA build with `If not IsPartialReload()` |
| Latest write-back not chosen | `FirstValue`/load-order or unparsed `CreatedAt` | Use `FirstSortedValue(v, -Num(ts))`, robust timestamp parse |
