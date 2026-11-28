"""Disposable exact-path and deterministic output proof in a nested full adoption."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parents[1]
source = root / "packages/provenistem"
sys.path.insert(0, str(source / "tools"))
import adopter

def require(condition, detail):
    if not condition:
        raise RuntimeError(detail)

def snapshot(path):
    return {p.relative_to(path).as_posix(): p.read_bytes()
            for p in path.rglob("*") if p.is_file()}

with tempfile.TemporaryDirectory(prefix="navigation-proof-") as scratch:
    host = Path(scratch)
    sentinel = host / "README.md"
    sentinel.write_bytes(b"host-owned\n")
    dest = host / "modules" / "deep" / "provenistem"
    source_before = snapshot(source)
    plan = adopter.plan(source, dest, "full")
    require(plan["status"] == "NEW_DESTINATION" and not plan["writes"] and not dest.exists(),
            "preflight wrote or did not identify a clean nested destination")
    for entry in plan["entries"]:
        require(entry["action"] == "ADD", "unexpected initial plan action")
        path = dest / entry["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / entry["path"], path)
    require(snapshot(dest) == source_before, "copied package differs")
    for section, kind, prefix in (("ideas", "idea", "IDEA"), ("features", "feature", "FEAT")):
        for number in (2, 1):
            row = json.loads((dest / "templates" / (kind + ".example.json")).read_text(encoding="utf-8"))
            row["id"] = f"{prefix}-{number:06d}"
            if kind == "feature":
                row["idea_ids"] = ["IDEA-000001"]
            (dest / section / "records" / (row["id"] + ".json")).write_bytes(
                (json.dumps(row, indent=2) + "\n").encode("utf-8"))
    def command(action):
        result = subprocess.run([sys.executable, str(dest / "tools/library.py"), action],
                                cwd=dest, capture_output=True, text=True, encoding="utf-8",
                                env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1"),
                                timeout=90)
        print(result.stdout, end="")
        require(result.returncode == 0, result.stderr)
    before = snapshot(host)
    command("build")
    after = snapshot(host)
    changed = {p for p, data in before.items() if after.get(p) != data}
    require(set(before) == set(after) and changed == {
        "modules/deep/provenistem/ideas/INDEX.md", "modules/deep/provenistem/features/INDEX.md"},
        "authorized build touched non-index files")
    for section, prefix in (("ideas", "IDEA"), ("features", "FEAT")):
        path = dest / section / "INDEX.md"
        raw = path.read_bytes()
        links = re.findall(r"\[([A-Z]+-\d{6})\]\((records/[^)]+)\)", raw.decode("utf-8"))
        expected_ids = [f"{prefix}-000001", f"{prefix}-000002"]
        require([ident for ident, _ in links] == expected_ids, "missing or unsorted record links")
        for ident, relative in links:
            target = path.parent / relative
            require(relative == "records/" + ident + ".json" and
                    target.resolve().parent == (path.parent / "records").resolve() and
                    target.is_file() and json.loads(target.read_text(encoding="utf-8"))["id"] == ident,
                    "incorrect nested target")
        require(b"\r" not in raw, "non-LF output")
        print("NAVIGATION_OUTPUT_SHA256", section, hashlib.sha256(raw).hexdigest())
    command("check")
    command("build")
    require(snapshot(host) == after, "non-deterministic output or host write")
    require(snapshot(source) == source_before, "source changed")
    print("NESTED_NAVIGATION_PROOF_PASS")
