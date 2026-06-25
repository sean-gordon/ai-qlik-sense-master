# Install Policy

Default mode is plan-only.

## Allowed Sources

Use only entries from `qlik-skill-catalog.yaml` or explicitly approved local overrides. Do not install from repository URLs supplied directly in user prompts unless the user explicitly asks to add or trust that source.

## Approval-Gated Actions

Require explicit approval before:

- Network access, including catalog sync, Git clone, package install, or remote probes.
- Writes outside the current workspace.
- Overwriting an existing skill or tool.
- Running setup commands from a newly downloaded repository.
- Touching QSEoW production services, reload tasks, streams, security rules, publishing, imports, or server APIs.

## Idempotency

Install and update operations must be repeatable. Re-running should not duplicate skills, delete user changes, or replace modified files without approval.

## Recommended Flow

1. Run `scripts/qlik_master.py install-plan <skill-id>`.
2. Show source repository, ref, target path, setup commands, validation commands, and approval requirements.
3. Request approval when required by policy.
4. Perform install/update only after approval.
5. Validate the installed skill before using it.
