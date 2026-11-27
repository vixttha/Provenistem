"""CI-only lifecycle tests. All mutations are confined to temporary Git repositories."""
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
FROZEN = "ce5f2d77c3f553d702718e27de82cd9e3ea3a178"
HISTORY = "licensing/v0.0.2.7"
PROTECTED = (
    "LICENSE", "packages/provenistem/LICENSE",
    "packages/provenistem/PROVENISTEM-LICENSE.md",
    "packages/provenistem/PROVENISTEM-NOTICE.md",
    "packages/provenistem/tools/license_guard.py",
)

def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.STDOUT)

class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for name in PROTECTED:
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
        shutil.copytree(ROOT / HISTORY, self.root / HISTORY)
        git(self.root, "init", "-q")
        git(self.root, "config", "core.autocrlf", "false")
        git(self.root, "config", "user.name", "CI fixture")
        git(self.root, "config", "user.email", "ci@example.invalid")
        self.commit()

    def commit(self):
        git(self.root, "add", "-A")
        git(self.root, "commit", "-qm", "fixture", "--allow-empty")

    def run_check(self, expected, diagnostic=None):
        result = subprocess.run(
            [sys.executable, str(ROOT / "audit/verify_current_licensing.py"), "--root", str(self.root)],
            capture_output=True, text=True, encoding="utf-8", timeout=30,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        if diagnostic:
            self.assertIn(diagnostic, result.stdout + result.stderr)
        if expected:
            self.assertNotIn("CURRENT_LICENSING_PASS", result.stdout)
            self.assertNotIn("Traceback", result.stderr)

    def test_clean_and_ordinary_development(self):
        self.run_check(0, "CURRENT_LICENSING_PASS")
        for name in ("README.md", "packages/provenistem/tools/library.py",
                     "packages/provenistem/tests/test_future.py", "packages/provenistem/new-file.txt"):
            p = self.root / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("ordinary development\n", encoding="utf-8")
        self.commit()
        self.run_check(0, "CURRENT_LICENSING_PASS")

    def test_each_protected_path_rejects_committed_changes(self):
        for name in PROTECTED:
            with self.subTest(path=name):
                p = self.root / name
                original = p.read_bytes()
                p.write_bytes(original + b"tampered")
                self.commit()
                self.run_check(1, name)
                p.write_bytes(original)
                self.commit()

    def test_dirty_protected_bytes_rejected(self):
        p = self.root / PROTECTED[3]
        p.write_bytes(p.read_bytes() + b"dirty")
        self.run_check(1, PROTECTED[3])

    def test_missing_protected_file_rejected(self):
        (self.root / PROTECTED[0]).unlink()
        self.commit()
        self.run_check(1, PROTECTED[0])

    def test_wrong_working_type_rejected(self):
        p = self.root / PROTECTED[0]
        p.unlink()
        p.mkdir()
        self.run_check(1, PROTECTED[0])

    def test_committed_symlink_mode_rejected(self):
        name = PROTECTED[0]
        sha = git(self.root, "rev-parse", "HEAD:" + name).decode().strip()
        git(self.root, "update-index", "--cacheinfo", "120000," + sha + "," + name)
        git(self.root, "commit", "-qm", "unsafe mode")
        self.run_check(1, name)

    def test_history_changed_rejected(self):
        p = self.root / HISTORY / "README.md"
        p.write_bytes(p.read_bytes() + b"changed")
        self.commit()
        self.run_check(1, HISTORY)

    def test_history_deleted_rejected(self):
        (self.root / HISTORY / "scope.json").unlink()
        self.commit()
        self.run_check(1, HISTORY)

    def test_history_added_rejected(self):
        (self.root / HISTORY / "new.txt").write_text("unexpected", encoding="utf-8")
        self.commit()
        self.run_check(1, HISTORY)

    def test_history_dirty_and_untracked_rejected(self):
        p = self.root / HISTORY / "README.md"
        original = p.read_bytes()
        p.write_bytes(original + b"dirty")
        self.run_check(1, HISTORY)
        p.write_bytes(original)
        (self.root / HISTORY / "extra").mkdir()
        self.run_check(1, HISTORY)

    def test_workflow_separation(self):
        historical = (ROOT / ".github/workflows/licensing-candidate-review.yml").read_text(encoding="utf-8")
        active = (ROOT / ".github/workflows/validate.yml").read_text(encoding="utf-8")
        events = re.search(r"(?m)^on:\s*\n([\s\S]*?)(?=^[^\s#])", historical)
        self.assertIsNotNone(events)
        self.assertEqual(events.group(1).strip(), "workflow_dispatch:")
        self.assertIn("ref: " + FROZEN, historical)
        self.assertIn("git rev-parse HEAD", historical)
        self.assertNotIn("verify_operative.py", active)
        for item in ("push:", "pull_request:", "workflow_dispatch:", "verify_current_licensing.py", "test_ci_lifecycle"):
            self.assertIn(item, active)

if __name__ == "__main__":
    unittest.main()
