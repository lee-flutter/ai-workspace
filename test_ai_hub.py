import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import ai_hub


ROOT = Path(__file__).resolve().parent


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "workspace.json"
        self.data = {
            "agents": [
                {
                    "name": "dev",
                    "instructions": "Build carefully.",
                    "skills": ["coding"],
                    "contexts": ["project"],
                }
            ],
            "skills": [
                {"name": "coding", "instructions": "Write tests."},
                {"name": "review", "instructions": "Find defects."},
            ],
            "contexts": [{"name": "project", "instructions": "Use Python."}],
        }

    def load(self):
        self.path.write_text(json.dumps(self.data), encoding="utf-8")
        return ai_hub.load_workspace(self.path)

    def test_render_combines_definitions_and_deduplicates(self):
        output = ai_hub.render(
            self.load(), "dev", ["coding", "review"], ["project"], "Fix the bug"
        )
        self.assertEqual(
            output,
            "# Agent: dev\n\nBuild carefully.\n\n"
            "# Skill: coding\n\nWrite tests.\n\n"
            "# Skill: review\n\nFind defects.\n\n"
            "# Context: project\n\nUse Python.\n\n"
            "# Task\n\nFix the bug",
        )

    def test_invalid_definitions_and_references_are_rejected(self):
        cases = [
            ("duplicate", lambda data: data["skills"].append(data["skills"][0])),
            ("missing instructions", lambda data: data["agents"][0].update(instructions="")),
            ("invalid references", lambda data: data["agents"][0].update(skills="coding")),
            ("unknown reference", lambda data: data["agents"][0].update(skills=["missing"])),
        ]
        for label, mutate in cases:
            with self.subTest(label=label):
                original = json.loads(json.dumps(self.data))
                mutate(self.data)
                with self.assertRaises(ai_hub.WorkspaceError):
                    self.load()
                self.data = original

    def test_unknown_agent_and_extra_definition_are_rejected(self):
        workspace = self.load()
        with self.assertRaisesRegex(ai_hub.WorkspaceError, "Unknown agent"):
            ai_hub.render(workspace, "missing")
        with self.assertRaisesRegex(ai_hub.WorkspaceError, "Unknown skills"):
            ai_hub.render(workspace, "dev", skills=["missing"])
        with self.assertRaisesRegex(ai_hub.WorkspaceError, "Unknown contexts"):
            ai_hub.render(workspace, "dev", contexts=["missing"])

    def test_cli_with_external_workspace_and_errors(self):
        self.load()
        command = [sys.executable, str(ROOT / "ai_hub.py"), "--workspace", str(self.path)]
        result = subprocess.run(command + ["list", "agents"], capture_output=True, text=True)
        self.assertEqual((result.returncode, result.stdout), (0, "dev\n"))
        result = subprocess.run(command + ["render", "missing"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Unknown agent", result.stderr)

    def test_unreadable_or_invalid_json_is_reported(self):
        with self.assertRaisesRegex(ai_hub.WorkspaceError, "Cannot load workspace"):
            ai_hub.load_workspace(self.path)
        self.path.write_text("{", encoding="utf-8")
        with self.assertRaisesRegex(ai_hub.WorkspaceError, "Cannot load workspace"):
            ai_hub.load_workspace(self.path)


if __name__ == "__main__":
    unittest.main()
