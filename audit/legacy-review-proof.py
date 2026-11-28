"""Disposable runner-only mutation proof for three CodeRabbit findings."""
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
MODE = sys.argv[1]
ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1")
PYTHON = sys.executable
CASES = (
    ("commented-run", ".github/workflows/validate.yml",
     "        run: python audit/verify_legacy_upgrade.py",
     "        # run: python audit/verify_legacy_upgrade.py",
     ["-m", "unittest", "discover", "-s", "audit", "-p", "test_ci_lifecycle.py",
      "-k", "test_workflow_separation", "-v"], "legacy upgrade executable step"),
    ("empty-directory", "packages/provenistem/tools/adopter.py",
     "    destination = Path(destination).absolute()",
     "    destination = Path(destination).absolute()\n    if destination.is_dir():\n        (destination / 'upgrade-cache').mkdir(exist_ok=True)",
     ["audit/verify_legacy_upgrade.py"], "upgrade planner modified host files"),
    ("changed-renderer", "packages/provenistem/tools/library.py",
     'f"Generated from canonical {singular} records."',
     'f"Changed renderer for canonical {singular} records."',
     ["audit/verify_legacy_upgrade.py"], "legacy catalog check failed"),
)
for label, relative, before, after, command, diagnostic in CASES:
    path = ROOT / relative
    original = path.read_bytes()
    text = original.decode("utf-8")
    if text.count(before) != 1:
        raise RuntimeError("mutation anchor mismatch: " + label)
    try:
        path.write_bytes(text.replace(before, after).encode("utf-8"))
        result = subprocess.run([PYTHON, *command], cwd=ROOT, env=ENV,
                                capture_output=True, text=True, encoding="utf-8",
                                timeout=180)
        print(result.stdout, end="")
        print(result.stderr, end="")
        if MODE == "red":
            if result.returncode != 0:
                raise RuntimeError("old check did not miss mutation: " + label)
            print("EXPECTED_OLD_FALSE_PASS", label)
        elif MODE == "green":
            if result.returncode != 1 or diagnostic not in result.stdout + result.stderr:
                raise RuntimeError("corrected check did not detect mutation: " + label)
            print("MUTATION_REJECTED", label)
        else:
            raise ValueError("unknown proof mode")
    finally:
        path.write_bytes(original)
if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT):
    raise RuntimeError("proof checkout not clean")
print("REVIEW_REGRESSION_PROOF_PASS", MODE)

# One-time provenance check: independently generate the seeded golden bytes
# with the exact pinned historical library, in a disposable fixture only.
import json
import tempfile
from verify_legacy_upgrade import BASE, BASE_TREE, LEGACY_INDEXES, materialize
with tempfile.TemporaryDirectory() as scratch:
    fixture = Path(scratch) / "legacy"
    materialize(BASE, BASE_TREE, fixture)
    for section, kind in (("ideas", "idea"), ("features", "feature")):
        record = json.loads((fixture / "templates" / (kind + ".example.json")).read_text(encoding="utf-8"))
        if kind == "feature":
            record["idea_ids"] = ["IDEA-000001"]
        (fixture / section / "records" / (record["id"] + ".json")).write_bytes(
            (json.dumps(record, indent=2) + "\n").encode("utf-8"))
    subprocess.run([PYTHON, str(fixture / "tools/library.py"), "build", "--root", str(fixture)],
                   cwd=fixture, env=ENV, timeout=90, check=True)
    for relative, expected in LEGACY_INDEXES.items():
        if (fixture / relative).read_bytes() != expected:
            raise RuntimeError("golden bytes differ from pinned historical renderer: " + relative)
    print("PINNED_RENDERER_GOLDEN_BYTES_PASS")
