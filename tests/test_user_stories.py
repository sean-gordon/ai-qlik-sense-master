import importlib.util
import io
import json
import unittest
import uuid
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "qlik_master.py"

spec = importlib.util.spec_from_file_location("qlik_master", MODULE_PATH)
qlik_master = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(qlik_master)


class QlikMasterUserStoryTests(unittest.TestCase):
    def setUp(self):
        self.temp_parent = REPO_ROOT / "tmp" / "user-story-tests"
        self.temp_parent.mkdir(parents=True, exist_ok=True)
        self.root = self.temp_parent / f"{self.id().replace('.', '_')}_{uuid.uuid4().hex}"
        self.root.mkdir()
        self.refs = self.root / "references"
        self.refs.mkdir()
        self.skills_root = self.root / "skills-root"
        self.skills_root.mkdir()
        self.snapshot = self.root / "qlik-skill-catalog.yaml"
        self.routing_map = self.refs / "routing-map.yaml"
        self.routing_tests = self.refs / "routing-tests.yaml"
        self.source_registry = self.refs / "source-registry.yaml"

        self.catalog = {
            "catalog_version": 1,
            "updated_at": "2026-06-25",
            "entries": [
                {
                    "id": "qlik-sense-app-dev",
                    "kind": "skill",
                    "display_name": "Qlik Sense App Dev Skill",
                    "aliases": ["QlikSense"],
                    "description": "Qlik Sense app development guidance.",
                    "github": {
                        "repo": "https://github.com/example/app.git",
                        "ref": "main",
                        "path": ".",
                    },
                    "install": {
                        "target_name": "QlikSense",
                        "setup_commands": ["tool/setup.py"],
                        "validation_commands": ["tool/qlik_search.py --self-test"],
                    },
                    "tools": [
                        {
                            "id": "qlik-search",
                            "command": "tool/qlik_search.py",
                            "purpose": "Search app-development references.",
                        }
                    ],
                    "routing": {
                        "priority": 80,
                        "signals": ["set analysis", "qvd", "komment"],
                        "evidence_needed": ["script or expression"],
                        "risk": "local-advice",
                        "fallback": [],
                    },
                    "capabilities": ["app-development", "qvd"],
                },
                {
                    "id": "qlik-sense-diagnostic-tool",
                    "kind": "skill",
                    "display_name": "Qlik Sense Diagnostic Tool",
                    "description": "Qlik Sense diagnostics.",
                    "github": {
                        "repo": "https://github.com/example/diag.git",
                        "ref": "main",
                        "path": ".",
                    },
                    "install": {
                        "target_name": "qlik-sense-diagnostic-tool",
                        "setup_commands": [],
                        "validation_commands": ["SKILL.md"],
                    },
                    "tools": [
                        {
                            "id": "diagnostic-workflow",
                            "command": "SKILL.md",
                            "purpose": "Guide diagnostic workflows.",
                        }
                    ],
                    "routing": {
                        "priority": 90,
                        "signals": ["reload failed", "qseow", "reload task"],
                        "evidence_needed": ["reload log"],
                        "risk": "diagnostic",
                        "fallback": ["qlik-sense-app-dev"],
                    },
                    "capabilities": ["diagnostics"],
                },
                {
                    "id": "qlik-ai-skill",
                    "kind": "skill",
                    "display_name": "Qlik Sense AI Skill",
                    "aliases": ["QlikSenseAI", "qlik-ai-skill"],
                    "description": "Qlik Sense AI skill with local knowledge retrieval tools.",
                    "github": {
                        "repo": "https://github.com/example/qlik-ai-skill.git",
                        "ref": "main",
                        "path": ".",
                    },
                    "install": {
                        "target_name": "QlikSense",
                        "setup_commands": ["tool/setup.py"],
                        "validation_commands": [
                            "tool/qlik_search.py --domains",
                            "tool/qlik_mcp_server.py",
                        ],
                    },
                    "tools": [
                        {
                            "id": "qlik-knowledge-search-cli",
                            "command": "tool/qlik_search.py",
                            "purpose": "Search Qlik references from the command line.",
                        },
                        {
                            "id": "qlik-knowledge-mcp",
                            "command": "tool/qlik_mcp_server.py",
                            "purpose": "Expose qlik_knowledge_search via MCP.",
                        },
                    ],
                    "routing": {
                        "priority": 70,
                        "signals": [
                            "qlik-ai-skill",
                            "qlik_knowledge_search",
                            "use qlik_knowledge_search",
                            "qlik_knowledge_search to find",
                            "qlik mcp server",
                            "retrieval tool",
                            "tool-first retrieval",
                        ],
                        "evidence_needed": ["target assistant or host"],
                        "risk": "local-tooling",
                        "fallback": ["qlik-sense-app-dev"],
                    },
                    "capabilities": ["knowledge-retrieval", "mcp"],
                },
                {
                    "id": "planned-missing-skill",
                    "kind": "skill",
                    "display_name": "Planned Missing Skill",
                    "description": "A catalog entry used to verify plan-only missing installs.",
                    "github": {
                        "repo": "https://github.com/example/missing.git",
                        "ref": "main",
                        "path": ".",
                    },
                    "install": {
                        "target_name": "planned-missing-skill",
                        "setup_commands": [],
                        "validation_commands": ["SKILL.md"],
                    },
                    "tools": [],
                    "routing": {
                        "priority": 10,
                        "signals": ["missing specialist"],
                        "evidence_needed": [],
                        "risk": "local-advice",
                        "fallback": [],
                    },
                    "capabilities": ["missing"],
                },
            ],
        }
        self.registry = {
            "public_catalog": {
                "url": "https://example.invalid/catalog.json",
                "cached_snapshot": str(self.snapshot),
            },
            "local_overrides": {"enabled": True, "paths": [str(self.skills_root)]},
            "install_policy": {
                "default_mode": "plan-only",
                "require_approval_for": [
                    "network",
                    "writes_outside_workspace",
                    "overwrite_existing_skill",
                ],
                "allow_prompt_supplied_sources": False,
            },
        }
        self.legacy_routes = {
            "routes": [
                {
                    "id": "legacy-diagnostics",
                    "primary": "qlik-sense-diagnostic-tool",
                    "fallback": ["qlik-sense-app-dev"],
                    "signals": ["script log"],
                    "risk": "diagnostic",
                }
            ]
        }
        self.route_tests = {
            "tests": [
                {
                    "prompt": "My Set Analysis returns zero.",
                    "expected_primary": "qlik-sense-app-dev",
                },
                {
                    "prompt": "This reload failed.",
                    "expected_primary": "qlik-sense-diagnostic-tool",
                },
                {
                    "prompt": "Use qlik_knowledge_search for retrieval.",
                    "expected_primary": "qlik-ai-skill",
                },
            ]
        }

        self._write_json(self.snapshot, self.catalog)
        self._write_json(self.source_registry, self.registry)
        self._write_json(self.routing_map, self.legacy_routes)
        self._write_json(self.routing_tests, self.route_tests)
        self._install_ready_skill("QlikSense", "tool/qlik_search.py")
        self._install_ready_skill("QlikSense", "tool/qlik_mcp_server.py")
        self._install_ready_skill("qlik-sense-diagnostic-tool", "SKILL.md")

        self.patches = [
            patch.object(qlik_master, "ROOT", self.root),
            patch.object(qlik_master, "REFERENCES", self.refs),
            patch.object(qlik_master, "SOURCE_REGISTRY", self.source_registry),
            patch.object(qlik_master, "DEFAULT_CATALOG", self.snapshot),
            patch.object(qlik_master, "ROUTING_MAP", self.routing_map),
            patch.object(qlik_master, "ROUTING_TESTS", self.routing_tests),
        ]
        for item in self.patches:
            item.start()

    def tearDown(self):
        for item in reversed(self.patches):
            item.stop()

    def _write_json(self, path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _install_ready_skill(self, name, validation_path):
        skill_root = self.skills_root / name
        target = skill_root / validation_path.split()[0]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# ready\n", encoding="utf-8")
        (skill_root / "SKILL.md").write_text("# Skill\n", encoding="utf-8")

    def test_routes_app_development_signal_to_app_dev_skill(self):
        result = qlik_master.route_request("My Set Analysis returns zero.")
        self.assertEqual(result["primary_skill"], "qlik-sense-app-dev")
        self.assertEqual(result["lookup_source"], "catalog")
        self.assertEqual(result["availability"]["status"], "ready")

    def test_routes_diagnostic_signal_to_diagnostic_skill_with_fallback(self):
        result = qlik_master.route_request("This reload failed on the server.")
        self.assertEqual(result["primary_skill"], "qlik-sense-diagnostic-tool")
        self.assertEqual(result["secondary_skills"], ["qlik-sense-app-dev"])
        self.assertEqual(result["risk"], "diagnostic")

    def test_routes_retrieval_tooling_prompt_to_qlik_ai_skill(self):
        result = qlik_master.route_request("Use qlik_knowledge_search for Qlik reference retrieval.")
        self.assertEqual(result["primary_skill"], "qlik-ai-skill")
        self.assertEqual(result["secondary_skills"], ["qlik-sense-app-dev"])
        self.assertEqual(result["risk"], "local-tooling")
        self.assertEqual(result["availability"]["status"], "ready")
        self.assertEqual(
            [tool["id"] for tool in result["tools"]],
            ["qlik-knowledge-search-cli", "qlik-knowledge-mcp"],
        )

    def test_keeps_general_qlik_prompts_on_existing_specialists(self):
        app_result = qlik_master.route_request("My Qlik data model has a synthetic key.")
        diagnostic_result = qlik_master.route_request("Create a QSEoW reload task and schedule it.")
        self.assertEqual(app_result["primary_skill"], "qlik-sense-app-dev")
        self.assertEqual(diagnostic_result["primary_skill"], "qlik-sense-diagnostic-tool")

    def test_defaults_unclear_qlik_request_to_app_development(self):
        result = qlik_master.route_request("I need help with a Qlik question.")
        self.assertEqual(result["primary_skill"], "qlik-sense-app-dev")
        self.assertIn("defaulted", result["reason"])

    def test_matches_aliases_and_capabilities(self):
        alias_result = qlik_master.route_request("Use QlikSense for this issue.")
        capability_result = qlik_master.route_request("Need app development help.")
        self.assertEqual(alias_result["primary_skill"], "qlik-sense-app-dev")
        self.assertEqual(capability_result["primary_skill"], "qlik-sense-app-dev")

    def test_detect_lists_ready_installed_skills(self):
        result = qlik_master.detect()
        statuses = {item["id"]: item["status"] for item in result["skills"]}
        self.assertEqual(statuses["qlik-sense-app-dev"], "ready")
        self.assertEqual(statuses["qlik-sense-diagnostic-tool"], "ready")

    def test_list_sources_includes_catalog_and_local_status(self):
        result = qlik_master.list_sources()
        app_dev = result["entries"][0]
        self.assertEqual(result["catalog_version"], 1)
        self.assertEqual(app_dev["id"], "qlik-sense-app-dev")
        self.assertEqual(app_dev["local_status"], "ready")
        self.assertEqual(app_dev["tools"][0]["id"], "qlik-search")

    def test_install_plan_for_ready_skill_requires_no_action(self):
        result = qlik_master.install_plan("qlik-sense-app-dev")
        self.assertEqual(result["action"], "none")
        self.assertEqual(result["current_status"]["status"], "ready")
        self.assertIn("network", result["requires_approval"])

    def test_install_skill_for_ready_skill_reports_already_ready(self):
        result = qlik_master.install_skill("qlik-sense-app-dev")
        self.assertEqual(result["status"], "already-ready")
        self.assertFalse(result["performed"])

    def test_install_plan_for_missing_skill_is_plan_only_install(self):
        result = qlik_master.install_plan("planned-missing-skill")
        self.assertEqual(result["action"], "install")
        self.assertEqual(result["mode"], "plan-only")
        self.assertEqual(result["current_status"]["status"], "missing")

    def test_install_skill_for_missing_skill_returns_plan_without_writing(self):
        missing_root = self.skills_root / "planned-missing-skill"
        result = qlik_master.install_skill("planned-missing-skill")
        self.assertEqual(result["status"], "planned")
        self.assertFalse(result["performed"])
        self.assertFalse(missing_root.exists())

    def test_execute_install_clones_copies_and_validates_approved_catalog_skill(self):
        clone_temp = self.root / "execute-temp"

        class NoCleanupTempDir:
            def __init__(self, *args, **kwargs):
                pass

            def __enter__(self):
                clone_temp.mkdir(parents=True, exist_ok=True)
                return str(clone_temp)

            def __exit__(self, exc_type, exc, tb):
                return False

        class Completed:
            returncode = 0
            stdout = ""
            stderr = ""

        def fake_run(args, text=True, capture_output=True):
            clone_root = Path(args[-1])
            clone_root.mkdir(parents=True, exist_ok=True)
            (clone_root / "SKILL.md").write_text("# Installed\n", encoding="utf-8")
            (clone_root / ".git").mkdir()
            (clone_root / "__pycache__").mkdir()
            return Completed()

        with (
            patch.object(qlik_master.tempfile, "TemporaryDirectory", NoCleanupTempDir),
            patch.object(qlik_master.subprocess, "run", side_effect=fake_run),
        ):
            result = qlik_master.install_skill("planned-missing-skill", execute=True)

        target = self.skills_root / "planned-missing-skill"
        self.assertEqual(result["status"], "installed")
        self.assertTrue(result["performed"])
        self.assertTrue((target / "SKILL.md").exists())
        self.assertFalse((target / ".git").exists())
        self.assertFalse((target / "__pycache__").exists())

    def test_unknown_skill_install_plan_is_refused(self):
        result = qlik_master.install_plan("unknown-skill")
        self.assertEqual(result["action"], "refuse")
        self.assertIn("not declared", result["reason"])

    def test_check_skill_reports_not_in_catalog_for_unknown_id(self):
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            code = qlik_master.main(["check-skill", "unknown-skill"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(stdout.getvalue())["status"], "not-in-catalog")

    def test_doctor_validates_catalog_routing_map_and_route_tests(self):
        result = qlik_master.doctor()
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["errors"], [])

    def test_doctor_reports_failed_route_tests(self):
        self._write_json(
            self.routing_tests,
            {
                "tests": [
                    {
                        "prompt": "This reload failed.",
                        "expected_primary": "qlik-sense-app-dev",
                    }
                ]
            },
        )
        result = qlik_master.doctor()
        self.assertEqual(result["status"], "failed")
        self.assertRegex(result["errors"][0], "expected qlik-sense-app-dev")

    def test_sync_catalog_fetches_valid_catalog_and_replaces_snapshot(self):
        new_catalog = dict(self.catalog)
        new_catalog["catalog_version"] = 2
        response = io.BytesIO(json.dumps(new_catalog).encode("utf-8"))
        response.__enter__ = lambda item: item
        response.__exit__ = lambda *args: None

        with patch.object(qlik_master.urllib.request, "urlopen", return_value=response):
            result = qlik_master.sync_catalog()

        self.assertEqual(result["status"], "updated")
        self.assertEqual(json.loads(self.snapshot.read_text(encoding="utf-8"))["catalog_version"], 2)

    def test_sync_catalog_rejects_invalid_fetched_catalog(self):
        bad_catalog = {"catalog_version": 3, "entries": [{"id": "broken"}]}
        response = io.BytesIO(json.dumps(bad_catalog).encode("utf-8"))
        response.__enter__ = lambda item: item
        response.__exit__ = lambda *args: None

        with patch.object(qlik_master.urllib.request, "urlopen", return_value=response):
            result = qlik_master.sync_catalog()

        self.assertEqual(result["status"], "failed")
        self.assertIn("missing required field", result["errors"][0])

    def test_run_command_validates_existing_file_without_executing_it(self):
        skill_root = self.skills_root / "qlik-sense-diagnostic-tool"
        result = qlik_master.run_command("SKILL.md", skill_root)
        self.assertEqual(result["returncode"], 0)
        self.assertIn("exists:", result["stdout"])


if __name__ == "__main__":
    unittest.main()
