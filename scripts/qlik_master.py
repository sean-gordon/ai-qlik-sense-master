#!/usr/bin/env python3
"""Deterministic router for the AI Qlik Sense Master Skill."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REFERENCES = ROOT / "references"
SOURCE_REGISTRY = REFERENCES / "source-registry.yaml"
DEFAULT_CATALOG = ROOT / "qlik-skill-catalog.yaml"
ROUTING_MAP = REFERENCES / "routing-map.yaml"
ROUTING_TESTS = REFERENCES / "routing-tests.yaml"


def load_data(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        raise SystemExit(f"Missing required file: {path}") from None
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON-compatible YAML in {path}: {exc}") from None


def write_data_atomic(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=str(path.parent)) as handle:
        json.dump(data, handle, indent=2)
        handle.write("\n")
        temp_name = handle.name
    temp_path = Path(temp_name)
    try:
        temp_path.replace(path)
    except PermissionError:
        # Some managed Windows workspaces allow file writes but block replace/unlink.
        # Keep sync usable in that environment while preserving atomic replace elsewhere.
        with path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
            handle.write("\n")
        try:
            temp_path.unlink()
        except OSError:
            pass


def emit(data: Any) -> None:
    print(json.dumps(data, indent=2))


def expand_path(raw_path: str) -> Path | None:
    expanded = os.path.expandvars(raw_path)
    if "$" in expanded or "%" in expanded:
        return None
    return Path(expanded).expanduser()


def source_registry() -> dict[str, Any]:
    return load_data(SOURCE_REGISTRY)


def catalog_path() -> Path:
    registry = source_registry()
    raw_path = registry.get("public_catalog", {}).get("cached_snapshot", str(DEFAULT_CATALOG))
    path = expand_path(raw_path)
    if path is None:
        return DEFAULT_CATALOG
    if not path.is_absolute():
        path = ROOT / path
    return path


def catalog() -> dict[str, Any]:
    return load_data(catalog_path())


def routing_map() -> dict[str, Any]:
    return load_data(ROUTING_MAP)


def catalog_entries() -> dict[str, dict[str, Any]]:
    entries: dict[str, dict[str, Any]] = {}
    for entry in catalog().get("entries", []):
        entries[entry["id"]] = entry
        for alias in entry.get("aliases", []):
            entries.setdefault(alias, entry)
    return entries


def catalog_entry_list() -> list[dict[str, Any]]:
    return list(catalog().get("entries", []))


def local_search_roots() -> list[Path]:
    registry = source_registry()
    roots: list[Path] = []
    for raw_path in registry.get("local_overrides", {}).get("paths", []):
        path = expand_path(raw_path)
        if path is not None:
            roots.append(path)
    roots.append(ROOT)
    unique: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        key = str(root).lower()
        if key not in seen:
            unique.append(root)
            seen.add(key)
    return unique


def skill_candidate_names(entry: dict[str, Any]) -> list[str]:
    names = [
        entry.get("id", ""),
        entry.get("display_name", ""),
        entry.get("install", {}).get("target_name", ""),
        *entry.get("aliases", []),
    ]
    normalized = []
    for name in names:
        if name and name not in normalized:
            normalized.append(name)
    return normalized


def check_entry(entry: dict[str, Any]) -> dict[str, Any]:
    matches = []
    for root in local_search_roots():
        for name in skill_candidate_names(entry):
            candidate = root / name
            skill_md = candidate / "SKILL.md"
            if skill_md.exists():
                matches.append(candidate)

    if not matches and (ROOT / "SKILL.md").exists() and entry.get("id") == "ai-qlik-sense-master":
        matches.append(ROOT)

    if not matches:
        return {
            "id": entry.get("id"),
            "status": "missing",
            "path": None,
            "tools": [],
            "missing_tools": entry.get("install", {}).get("validation_commands", []),
        }

    path = matches[0]
    validation = entry.get("install", {}).get("validation_commands", [])
    tools = []
    missing_tools = []
    for command in validation:
        first = str(command).split()[0]
        check_path = path / first
        if check_path.exists():
            tools.append(first)
        else:
            missing_tools.append(first)

    status = "ready" if not missing_tools else "partial"
    return {
        "id": entry.get("id"),
        "status": status,
        "path": str(path),
        "tools": tools,
        "missing_tools": missing_tools,
    }


def install_plan(skill_id: str) -> dict[str, Any]:
    entries = catalog_entries()
    entry = entries.get(skill_id)
    if not entry:
        return {
            "skill_id": skill_id,
            "action": "refuse",
            "reason": "Skill ID is not declared in the cached public catalog.",
        }

    status = check_entry(entry)
    install = entry.get("install", {})
    github = entry.get("github", {})
    target_root = next((root for root in local_search_roots() if str(root) != str(ROOT)), local_search_roots()[0])
    target_path = target_root / install.get("target_name", entry["id"])
    approvals = list(source_registry().get("install_policy", {}).get("require_approval_for", []))

    action = "repair" if status["status"] == "partial" else "install"
    if status["status"] == "ready":
        action = "none"

    return {
        "skill_id": skill_id,
        "action": action,
        "source": github.get("repo"),
        "ref": github.get("ref", "main"),
        "source_path": github.get("path", "."),
        "target_path": str(target_path),
        "current_status": status,
        "requires_approval": approvals,
        "mode": source_registry().get("install_policy", {}).get("default_mode", "plan-only"),
        "setup_commands": install.get("setup_commands", []),
        "validation_commands": install.get("validation_commands", []),
    }


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def score_route(route: dict[str, Any], request: str) -> tuple[int, list[str]]:
    text = normalize(request)
    matched = []
    score = 0
    for signal in route.get("signals", []):
        signal_text = normalize(signal)
        if signal_text and signal_text in text:
            matched.append(signal)
            score += max(1, len(signal_text.split()))
    return score, matched


def add_match(matched: list[str], value: str) -> None:
    if value and value not in matched:
        matched.append(value)


def score_catalog_entry(entry: dict[str, Any], request: str) -> tuple[int, list[str]]:
    text = normalize(request)
    matched: list[str] = []
    score = 0

    routing = entry.get("routing", {})
    for signal in routing.get("signals", []):
        signal_text = normalize(signal)
        if signal_text and signal_text in text:
            add_match(matched, signal)
            score += max(3, len(signal_text.split()) * 3)

    for capability in entry.get("capabilities", []):
        capability_text = normalize(str(capability).replace("-", " "))
        if capability_text and capability_text in text:
            add_match(matched, str(capability))
            score += max(1, len(capability_text.split()))

    for name in [entry.get("id", ""), entry.get("display_name", ""), *entry.get("aliases", [])]:
        name_text = normalize(str(name).replace("-", " "))
        if name_text and name_text in text:
            add_match(matched, str(name))
            score += max(2, len(name_text.split()) * 2)

    return score, matched


def route_from_catalog(request: str) -> tuple[dict[str, Any] | None, list[str], list[dict[str, Any]]]:
    scored = []
    for index, entry in enumerate(catalog_entry_list()):
        score, matched = score_catalog_entry(entry, request)
        if score:
            priority = int(entry.get("routing", {}).get("priority", 0))
            scored.append((score, priority, -index, entry, matched))

    if scored:
        scored.sort(reverse=True, key=lambda item: (item[0], item[1], item[2]))
        candidates = [
            {
                "skill_id": entry.get("id"),
                "score": score,
                "priority": priority,
                "matched": matched,
            }
            for score, priority, _, entry, matched in scored[:5]
        ]
        _, _, _, selected, matched = scored[0]
        return selected, matched, candidates

    default = next((entry for entry in catalog_entry_list() if entry.get("id") == "qlik-sense-app-dev"), None)
    return default, [], []


def route_from_legacy_map(request: str) -> tuple[dict[str, Any] | None, list[str], list[dict[str, Any]]]:
    routes = routing_map().get("routes", [])
    scored = []
    for index, route in enumerate(routes):
        score, matched = score_route(route, request)
        if score:
            scored.append((score, -index, route, matched))

    if not scored:
        return None, [], []

    scored.sort(reverse=True, key=lambda item: (item[0], item[1]))
    candidates = [
        {
            "skill_id": route.get("primary"),
            "score": score,
            "matched": matched,
        }
        for score, _, route, matched in scored[:5]
    ]
    _, _, selected, matched = scored[0]
    return selected, matched, candidates


def selected_route_payload(selected: dict[str, Any], request: str, matched: list[str], candidates: list[dict[str, Any]], source: str) -> dict[str, Any]:
    entries = catalog_entries()
    if source == "catalog":
        entry = selected
        primary = selected.get("id")
        routing = selected.get("routing", {})
        secondary = routing.get("fallback", [])
        evidence_needed = routing.get("evidence_needed", [])
        risk = routing.get("risk", "local-advice")
        route_id = f"catalog:{primary}"
        tools = selected.get("tools", [])
    else:
        primary = selected.get("primary")
        secondary = selected.get("fallback", [])
        entry = entries.get(primary)
        evidence_needed = selected.get("evidence_needed", [])
        risk = selected.get("risk")
        route_id = selected.get("id")
        tools = entry.get("tools", []) if entry else []

    availability = (
        check_entry(entry)
        if entry
        else {
            "id": primary,
            "status": "not-in-catalog",
            "path": None,
            "tools": [],
            "missing_tools": [],
        }
    )
    result = {
        "primary_skill": primary,
        "secondary_skills": secondary,
        "route_id": route_id,
        "lookup_source": source,
        "reason": "Matched catalog signals: " + ", ".join(matched) if matched else "No specific signal matched; defaulted to app-development.",
        "evidence_needed": evidence_needed,
        "risk": risk,
        "tools": tools,
        "candidates": candidates,
        "availability": availability,
    }
    if availability["status"] != "ready":
        result["install_plan_hint"] = install_plan(primary)
    return result


def route_request(request: str) -> dict[str, Any]:
    selected, matched, candidates = route_from_catalog(request)
    if selected:
        return selected_route_payload(selected, request, matched, candidates, "catalog")

    selected, matched, candidates = route_from_legacy_map(request)
    if selected:
        return selected_route_payload(selected, request, matched, candidates, "routing-map")

    return {
        "primary_skill": None,
        "secondary_skills": [],
        "route_id": None,
        "lookup_source": "none",
        "reason": "No catalog entry or routing-map entry matched the request.",
        "evidence_needed": [],
        "risk": None,
        "tools": [],
        "candidates": [],
        "availability": {
            "id": None,
            "status": "not-in-catalog",
            "path": None,
            "tools": [],
            "missing_tools": [],
        },
    }


def detect() -> dict[str, Any]:
    return {
        "skills": [check_entry(entry) for entry in catalog().get("entries", [])],
        "search_roots": [str(root) for root in local_search_roots()],
    }


def list_sources() -> dict[str, Any]:
    entries = []
    for entry in catalog().get("entries", []):
        status = check_entry(entry)
        entries.append(
            {
                "id": entry.get("id"),
                "kind": entry.get("kind"),
                "display_name": entry.get("display_name"),
                "catalog_ref": entry.get("github", {}).get("ref"),
                "source": entry.get("github", {}).get("repo"),
                "local_status": status.get("status"),
                "path": status.get("path"),
                "capabilities": entry.get("capabilities", []),
                "tools": entry.get("tools", []),
                "routing_signals": entry.get("routing", {}).get("signals", []),
            }
        )
    return {
        "catalog_version": catalog().get("catalog_version"),
        "updated_at": catalog().get("updated_at"),
        "entries": entries,
    }


def validate_catalog(data: dict[str, Any]) -> list[str]:
    errors = []
    ids = set()
    if not isinstance(data.get("entries"), list):
        errors.append("Catalog must contain an entries list.")
        return errors
    for index, entry in enumerate(data["entries"]):
        prefix = f"entries[{index}]"
        for field in ("id", "kind", "display_name", "github", "install", "tools", "routing"):
            if field not in entry:
                errors.append(f"{prefix} missing required field: {field}")
        entry_id = entry.get("id")
        if entry_id in ids:
            errors.append(f"Duplicate catalog id: {entry_id}")
        ids.add(entry_id)
        github = entry.get("github", {})
        if github and not github.get("repo"):
            errors.append(f"{prefix}.github missing repo")
        install = entry.get("install", {})
        if install and not install.get("target_name"):
            errors.append(f"{prefix}.install missing target_name")
        routing = entry.get("routing", {})
        if routing and not isinstance(routing.get("signals", []), list):
            errors.append(f"{prefix}.routing.signals must be a list")
        if routing and not routing.get("signals"):
            errors.append(f"{prefix}.routing must include at least one signal")
        tools = entry.get("tools", [])
        if tools and not isinstance(tools, list):
            errors.append(f"{prefix}.tools must be a list")
    return errors


def validate_routing(data: dict[str, Any], entries: dict[str, dict[str, Any]]) -> tuple[list[str], list[str]]:
    errors = []
    warnings = []
    if not isinstance(data.get("routes"), list):
        return ["routing-map.yaml must contain a routes list."], warnings
    for index, route in enumerate(data["routes"]):
        prefix = f"routes[{index}]"
        for field in ("id", "primary", "signals", "risk"):
            if field not in route:
                errors.append(f"{prefix} missing required field: {field}")
        primary = route.get("primary")
        fallback = route.get("fallback", [])
        if primary not in entries:
            fallback_available = any(skill_id in entries for skill_id in fallback)
            message = f"{prefix} primary skill is not in catalog: {primary}"
            if fallback_available:
                warnings.append(message)
            else:
                errors.append(message)
        for skill_id in fallback:
            if skill_id not in entries:
                warnings.append(f"{prefix} fallback skill is not in catalog: {skill_id}")
    return errors, warnings


def validate_routing_tests() -> list[str]:
    errors = []
    tests = load_data(ROUTING_TESTS).get("tests", [])
    for index, test in enumerate(tests):
        prompt = test.get("prompt")
        expected = test.get("expected_primary")
        if not prompt or not expected:
            errors.append(f"tests[{index}] must include prompt and expected_primary")
            continue
        actual = route_request(prompt).get("primary_skill")
        if actual != expected:
            errors.append(f"tests[{index}] expected {expected}, got {actual}: {prompt}")
    return errors


def doctor() -> dict[str, Any]:
    catalog_data = catalog()
    entries = catalog_entries()
    errors = []
    warnings = []
    errors.extend(validate_catalog(catalog_data))
    routing_errors, routing_warnings = validate_routing(routing_map(), entries)
    errors.extend(routing_errors)
    warnings.extend(routing_warnings)
    errors.extend(validate_routing_tests())
    return {
        "status": "ok" if not errors else "failed",
        "errors": errors,
        "warnings": warnings,
        "sources": list_sources(),
        "detect": detect(),
    }


def sync_catalog() -> dict[str, Any]:
    registry = source_registry()
    url = registry.get("public_catalog", {}).get("url")
    if not url:
        return {"status": "failed", "reason": "No public_catalog.url configured."}

    with urllib.request.urlopen(url, timeout=30) as response:
        raw = response.read().decode("utf-8")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        return {"status": "failed", "reason": f"Fetched catalog is not JSON-compatible YAML: {exc}"}

    errors = validate_catalog(data)
    if errors:
        return {"status": "failed", "errors": errors}

    snapshot = expand_path(registry.get("public_catalog", {}).get("cached_snapshot", str(DEFAULT_CATALOG)))
    if snapshot is None:
        snapshot = DEFAULT_CATALOG
    if not snapshot.is_absolute():
        snapshot = ROOT / snapshot
    write_data_atomic(snapshot, data)
    return {
        "status": "updated",
        "catalog_version": data.get("catalog_version"),
        "entries": len(data.get("entries", [])),
        "source_url": url,
        "cached_snapshot": str(snapshot),
    }


def run_command(command: str, cwd: Path) -> dict[str, Any]:
    parts = command.split()
    if not parts:
        return {"command": command, "returncode": 0, "stdout": "", "stderr": ""}

    executable = cwd / parts[0]
    if executable.exists() and executable.suffix.lower() == ".py":
        args = ["py", str(executable), *parts[1:]]
    elif executable.exists():
        if not parts[1:] and executable.is_file():
            return {
                "command": command,
                "returncode": 0,
                "stdout": f"exists: {executable}",
                "stderr": "",
            }
        args = [str(executable), *parts[1:]]
    else:
        args = parts

    timeout = int(os.environ.get("QLIK_MASTER_COMMAND_TIMEOUT_SECONDS", "300"))
    try:
        completed = subprocess.run(args, cwd=str(cwd), text=True, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command,
            "returncode": 124,
            "stdout": exc.stdout or "",
            "stderr": f"Command timed out after {timeout} seconds.",
        }
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def copy_tree_contents(source: Path, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    for item in source.iterdir():
        if item.name in {".git", "__pycache__"}:
            continue
        destination = target / item.name
        if item.is_dir():
            if destination.exists():
                shutil.rmtree(destination)
            shutil.copytree(item, destination)
        else:
            shutil.copy2(item, destination)


def execute_install(plan: dict[str, Any], allow_overwrite: bool) -> dict[str, Any]:
    if plan.get("action") == "refuse":
        return {"status": "refused", "performed": False, "plan": plan}
    if plan.get("action") == "none":
        return {"status": "already-ready", "performed": False, "plan": plan}

    target_path = Path(plan["target_path"])
    if target_path.exists() and not allow_overwrite:
        return {
            "status": "refused",
            "performed": False,
            "reason": "Target path already exists. Re-run with --allow-overwrite to replace it.",
            "plan": plan,
        }

    with tempfile.TemporaryDirectory(prefix="qlik-master-install-") as temp_dir:
        clone_root = Path(temp_dir) / "repo"
        clone_args = ["git", "clone", "--depth", "1"]
        if plan.get("ref"):
            clone_args.extend(["--branch", plan["ref"]])
        clone_args.extend([plan["source"], str(clone_root)])
        clone = subprocess.run(clone_args, text=True, capture_output=True)
        if clone.returncode != 0:
            return {
                "status": "failed",
                "performed": False,
                "stage": "clone",
                "command": " ".join(clone_args),
                "stdout": clone.stdout,
                "stderr": clone.stderr,
                "plan": plan,
            }

        source_path = clone_root / plan.get("source_path", ".")
        if not source_path.exists():
            return {
                "status": "failed",
                "performed": False,
                "stage": "source_path",
                "reason": f"Source path does not exist in cloned repository: {source_path}",
                "plan": plan,
            }

        if target_path.exists():
            shutil.rmtree(target_path)
        copy_tree_contents(source_path, target_path)

    setup_results = [run_command(command, target_path) for command in plan.get("setup_commands", [])]
    validation_results = [run_command(command, target_path) for command in plan.get("validation_commands", [])]
    failed = [result for result in [*setup_results, *validation_results] if result["returncode"] != 0]
    return {
        "status": "failed" if failed else "installed",
        "performed": True,
        "target_path": str(target_path),
        "setup_results": setup_results,
        "validation_results": validation_results,
        "plan": plan,
    }


def install_skill(skill_id: str, execute: bool = False, allow_overwrite: bool = False) -> dict[str, Any]:
    plan = install_plan(skill_id)
    if plan.get("action") == "none":
        return {"status": "already-ready", "performed": False, "plan": plan}
    if execute:
        return execute_install(plan, allow_overwrite)
    if plan.get("mode") == "plan-only" or plan.get("action") in ("none", "refuse"):
        plan["status"] = "planned"
        plan["performed"] = False
        return plan
    return {
        "status": "refused",
        "performed": False,
        "reason": "Direct installs are not implemented yet. Use install-plan and perform approved actions explicitly.",
        "plan": plan,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("detect")
    route_parser = sub.add_parser("route")
    route_parser.add_argument("request")
    sub.add_parser("sync-catalog")
    sub.add_parser("list-sources")
    check_parser = sub.add_parser("check-skill")
    check_parser.add_argument("skill_id")
    plan_parser = sub.add_parser("install-plan")
    plan_parser.add_argument("skill_id")
    install_parser = sub.add_parser("install-skill")
    install_parser.add_argument("skill_id")
    install_parser.add_argument("--execute", action="store_true", help="Clone/copy from the approved catalog source.")
    install_parser.add_argument("--allow-overwrite", action="store_true", help="Replace an existing target directory.")
    sub.add_parser("doctor")

    args = parser.parse_args(argv)
    if args.command == "detect":
        emit(detect())
    elif args.command == "route":
        emit(route_request(args.request))
    elif args.command == "sync-catalog":
        emit(sync_catalog())
    elif args.command == "list-sources":
        emit(list_sources())
    elif args.command == "check-skill":
        entries = catalog_entries()
        entry = entries.get(args.skill_id)
        emit(check_entry(entry) if entry else {"id": args.skill_id, "status": "not-in-catalog"})
    elif args.command == "install-plan":
        emit(install_plan(args.skill_id))
    elif args.command == "install-skill":
        emit(install_skill(args.skill_id, execute=args.execute, allow_overwrite=args.allow_overwrite))
    elif args.command == "doctor":
        result = doctor()
        emit(result)
        return 0 if result["status"] == "ok" else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
