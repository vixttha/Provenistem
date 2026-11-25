"""CI-only end-to-end adoption verification; never operates on real host records."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def verify_copied_installation(source):
    sys.path.insert(0, str(source / "tools"))
    import adopter

    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    env.pop("PYTHONPATH", None)

    def run(root, *args, expected=0):
        result = subprocess.run(
            [sys.executable, *args], cwd=root, env=env,
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=120, check=False,
        )
        print(result.stdout, end="")
        print(result.stderr, end="")
        if result.returncode != expected:
            raise RuntimeError(f"{args}: expected {expected}, got {result.returncode}")

    with tempfile.TemporaryDirectory() as scratch:
        host = Path(scratch) / "host"
        host.mkdir()
        sentinel = host / "README.md"
        sentinel.write_bytes(b"Host-owned README\n")
        dest = host / "modules" / "provenistem"
        plan = adopter.plan(source, dest)
        if plan["status"] != "NEW_DESTINATION" or plan["writes"] or dest.exists():
            raise RuntimeError("fresh plan must not write")
        for entry in plan["entries"]:
            if entry["action"] != "ADD":
                raise RuntimeError("unexpected plan action")
            relative = entry["path"]
            target = dest / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source / relative, target)
        expected = {
            p.relative_to(source).as_posix(): p.read_bytes()
            for p in source.rglob("*")
            if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
        }
        def snapshot():
            return {
                p.relative_to(dest).as_posix(): p.read_bytes()
                for p in dest.rglob("*") if p.is_file()
            }
        if snapshot() != expected:
            raise RuntimeError("planned copy is not byte-identical to portable source")
        run(dest, "tools/library.py", "check", "--expect-empty")
        run(dest, "-m", "unittest", "discover", "-s", "tests", "-v")
        if snapshot() != expected:
            raise RuntimeError("copied regression suite mutated portable files")
        print(f"Verified complete blank copy: {len(expected)} files; full suite passed.")

        # Populate only this disposable host using two synthetic record types.
        for section, kind in (("ideas", "idea"), ("features", "feature")):
            row = json.loads((dest / "templates" / f"{kind}.example.json").read_text(encoding="utf-8"))
            if kind == "feature":
                row["idea_ids"] = ["IDEA-000001"]
            (dest / section / "records" / f"{row['id']}.json").write_text(
                json.dumps(row, indent=2), encoding="utf-8")
        before = snapshot()
        run(dest, "tools/library.py", "build")
        built = snapshot()
        changed = {path for path in before if before[path] != built[path]}
        if changed != {"ideas/INDEX.md", "features/INDEX.md"} or before.keys() != built.keys():
            raise RuntimeError("build changed paths other than derived indexes")
        run(dest, "tools/library.py", "check")
        run(dest, "tools/library.py", "check", "--expect-empty", expected=1)
        # Portable modularity checks must also work on populated host records.
        run(dest, "-m", "unittest", "discover", "-s", "tests", "-p", "test_modularity_contract.py", "-v")
        run(dest, "tools/library.py", "build")
        if snapshot() != built or sentinel.read_bytes() != b"Host-owned README\n":
            raise RuntimeError("populated validation changed records, host files or stable indexes")
        print("Verified populated copy: check/build, empty-starter rejection, modularity and byte preservation.")


if __name__ == "__main__":
    verify_copied_installation(Path.cwd())
