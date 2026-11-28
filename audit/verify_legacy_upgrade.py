"""Active compatibility test against an exact legacy MIT input; not historical replay."""
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "packages/provenistem"
BASE = "4b57d194e8f79351dd41a548e7c0a574c97ecb94"
BASE_TREE = "de00e24ff22ba563262859064f3634d54bab2d89"
PREFIX = "packages/provenistem"
NOTICES = ("LICENSE", "PROVENISTEM-LICENSE.md", "PROVENISTEM-NOTICE.md")
NEW_LEGAL = (*NOTICES[1:], "tools/license_guard.py")
ENV = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1"}
ENV.pop("PYTHONPATH", None)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def git(*args):
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True,
                            timeout=90, check=False)
    require(result.returncode == 0, f"Git fixture command failed ({args[0]}): "
            + result.stderr.decode("utf-8", errors="replace"))
    return result.stdout


def snapshot(root):
    return {p.relative_to(root).as_posix(): p.read_bytes()
            for p in root.rglob("*") if p.is_file()}


def materialize(commit, expected_tree, destination):
    require(git("rev-parse", "--verify", commit + ":" + PREFIX).decode().strip()
            == expected_tree, "legacy package tree mismatch")
    entries = git("ls-tree", "-rz", commit + ":" + PREFIX).split(b"\0")
    files = {}
    for entry in filter(None, entries):
        metadata, raw_path = entry.split(b"\t", 1)
        mode, kind, blob = metadata.decode("ascii").split()
        relative = raw_path.decode("utf-8")
        path = PurePosixPath(relative)
        require(mode in ("100644", "100755") and kind == "blob" and
                not path.is_absolute() and ".." not in path.parts and
                "\\" not in relative and ":" not in relative,
                "unsafe legacy fixture entry: " + relative)
        files[relative] = git("cat-file", "blob", blob)
    require(len(files) == 30 and "LICENSE" in files and
            all(name not in files for name in NEW_LEGAL), "wrong legacy inventory")
    for relative, data in files.items():
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    require(snapshot(destination) == files, "legacy reconstruction differs")
    return files


def run_python(script, *args):
    return subprocess.run([sys.executable, str(script), *map(str, args)],
                          cwd=ROOT, env=ENV, capture_output=True, text=True,
                          encoding="utf-8", timeout=120, check=False)


def check_catalog(destination, action="check"):
    result = run_python(SOURCE / "tools/library.py", action, "--root", destination)
    require(result.returncode == 0 and "PASS: 1 ideas, 1 features" in result.stdout,
            "legacy catalog " + action + " failed: " + result.stdout + result.stderr)


def plan_upgrade(destination, source_files):
    result = run_python(SOURCE / "tools/adopter.py", destination,
                        "--source", SOURCE, "--profile", "full")
    require(result.returncode in (0, 1), "upgrade preflight failed: " + result.stdout + result.stderr)
    plan = json.loads(result.stdout)
    require(plan["status"] == "EXISTING_DESTINATION" and plan["writes"] is False,
            "legacy upgrade must be a read-only existing-destination plan")
    actions = {}
    for entry in plan["entries"]:
        path, action = entry["path"], entry["action"]
        require(path in source_files and path not in actions, "unsafe or duplicate plan path: " + path)
        require(action in {"ADD", "SAME", "KEEP_HOST", "REVIEW_LOCAL_DIFFERENCE"},
                "unexpected upgrade action: " + path)
        actions[path] = action
    require(set(actions) == set(source_files), "full upgrade inventory differs from current source")
    require(result.returncode == int("REVIEW_LOCAL_DIFFERENCE" in actions.values()),
            "upgrade preflight exit status does not match plan")
    return actions


def verify():
    git("fetch", "--no-tags", "--depth=1", "origin", BASE)
    require(git("rev-parse", "FETCH_HEAD").decode().strip() == BASE, "wrong historical input")
    source_before = snapshot(SOURCE)
    with tempfile.TemporaryDirectory() as scratch:
        host = Path(scratch) / "host"
        host.mkdir()
        sentinel = host / "README.md"
        sentinel.write_bytes(b"host-owned outside package\n")
        legacy = host / "provenistem"
        # Missing or wrong fixture must fail before creating any destination.
        for commit, tree in (("0" * 40, BASE_TREE), (BASE, "0" * 40)):
            absent = host / "must-not-exist"
            try:
                materialize(commit, tree, absent)
            except ValueError as exc:
                require("fixture command failed" in str(exc) or "tree mismatch" in str(exc),
                        "unexpected fixture rejection")
                require(not absent.exists(), "invalid fixture created files")
            else:
                raise ValueError("invalid legacy fixture accepted")
        print("LEGACY_FIXTURE_NEGATIVE_PASS")
        baseline = materialize(BASE, BASE_TREE, legacy)
        for section, kind in (("ideas", "idea"), ("features", "feature")):
            row = json.loads((legacy / "templates" / (kind + ".example.json")).read_text(encoding="utf-8"))
            if kind == "feature":
                row["idea_ids"] = ["IDEA-000001"]
            (legacy / section / "records" / (row["id"] + ".json")).write_bytes(
                (json.dumps(row, indent=2) + "\n").encode("utf-8"))
        check_catalog(legacy, "build")
        old = snapshot(legacy)
        check_catalog(legacy)
        require(snapshot(legacy) == old, "catalog check modified the legacy fixture")
        actions = plan_upgrade(legacy, source_before)
        require(snapshot(legacy) == old, "upgrade planner modified host files")
        require(actions["LICENSE"] == "SAME" and
                all(actions[name] == "ADD" for name in NEW_LEGAL),
                "legacy legal action differs")
        protected = {path: data for path, data in old.items()
                     if "/records/" in path or path.endswith("/INDEX.md") or path == "LICENSE"}
        for path, action in actions.items():
            if path in protected:
                require(action == ("SAME" if path == "LICENSE" else "KEEP_HOST"),
                        "unsafe host data action: " + path)
                continue
            if action == "ADD":
                require(path not in old, "ADD would replace existing host file: " + path)
            elif action == "REVIEW_LOCAL_DIFFERENCE":
                # Only explicit fixture-local updates of exact upstream-owned legacy bytes.
                require(path in baseline and old.get(path) == baseline[path],
                        "refusing to simulate update of host-owned bytes: " + path)
            elif action == "SAME":
                require(old.get(path) == source_before[path], "incorrect SAME action: " + path)
                continue
            else:
                raise ValueError("unexpected KEEP_HOST action: " + path)
            target = legacy / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(SOURCE / path, target)
        after = snapshot(legacy)
        require(all(after.get(path) == data for path, data in protected.items()),
                "legacy records, indexes or MIT notice changed")
        require(all(after.get(path) == source_before[path] for path in NEW_LEGAL),
                "new legal inventory differs")
        check_catalog(legacy)
        require(snapshot(legacy) == after, "upgraded catalog check wrote")
        # Exercise local differences in every notice without ever applying the conflict plan.
        for name in NOTICES:
            (legacy / name).write_bytes(("HOST OWNED " + name).encode("utf-8"))
        conflict = snapshot(legacy)
        actions = plan_upgrade(legacy, source_before)
        require(all(actions[name] == "REVIEW_LOCAL_DIFFERENCE" for name in NOTICES),
                "host notice conflict not identified")
        require(snapshot(legacy) == conflict and sentinel.read_bytes() == b"host-owned outside package\n",
                "host-owned files changed")
    require(snapshot(SOURCE) == source_before, "current package changed during compatibility test")
    print("LEGACY_UPGRADE_PASS", BASE, "current candidate", git("rev-parse", "HEAD").decode().strip(),
          "records, indexes, MIT notice and host conflicts preserved; no release authority")


if __name__ == "__main__":
    try:
        verify()
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        print("LEGACY_UPGRADE_FAIL:", exc, file=sys.stderr)
        sys.exit(1)
