"""Confirm reported behavior in a disposable copy of the pinned starter."""
import json
import subprocess
import sys
from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory

PIN = "e36fcd6d12633395e9b573228c0797ade9e775b0"


def call(root, tool, *arguments):
    return subprocess.run(
        [sys.executable, str(root / "tools" / tool), *map(str, arguments)],
        capture_output=True,
        text=True,
        check=False,
    )


def main(target):
    target = target.resolve()
    head = subprocess.check_output(["git", "-C", str(target), "rev-parse", "HEAD"], text=True).strip()
    assert head == PIN, head
    starter = target / "packages/provenistem"
    assert call(starter, "library.py", "check", "--expect-empty").returncode == 0
    print(f"CONTROL: unique, valid empty starter at {head}")

    with TemporaryDirectory() as scratch:
        root = Path(scratch)
        duplicate = root / "duplicate"
        copytree(starter, duplicate)
        record = duplicate / "ideas/records/IDEA-000001.json"
        original = (duplicate / "templates/idea.example.json").read_text(encoding="utf-8")
        record.write_text(original, encoding="utf-8")
        assert call(duplicate, "library.py", "build").returncode == 0
        assert call(duplicate, "library.py", "check").returncode == 0
        changed = original.replace(
            '"lifecycle_status": "captured",',
            '"lifecycle_status": "adopted",\n  "lifecycle_status": "captured",',
            1,
        )
        assert changed != original
        record.write_text(changed, encoding="utf-8")
        result = call(duplicate, "library.py", "check")
        assert result.returncode == 0, result.stderr
        print("CONFIRMED duplicate_member: conflicting lifecycle values passed check")

        partial = root / "partial"
        copytree(starter, partial)
        initial = partial / "ideas/INDEX.md"
        initial.write_text("Previous index\n", encoding="utf-8")
        before = initial.read_bytes()
        second = partial / "features/INDEX.md"
        second.unlink()
        second.mkdir()
        result = call(partial, "library.py", "build")
        assert result.returncode != 0 and "Traceback" in result.stderr
        assert initial.read_bytes() != before and second.is_dir()
        print("CONFIRMED partial_index_build: first index changed before failure on the second")

        ordinary = root / "fresh"
        result = call(starter, "adopter.py", ordinary)
        assert result.returncode == 0
        ordinary_plan = json.loads(result.stdout)
        assert ordinary_plan["status"] == "NEW_DESTINATION" and ordinary_plan["writes"] is False
        assert not ordinary.exists()
        print("CONTROL: a genuinely fresh destination yields a read-only plan")

        blocked = root / "occupied"
        blocked.write_text("Existing project file\n", encoding="utf-8")
        result = call(starter, "adopter.py", blocked / "new-library")
        assert result.returncode == 0
        blocked_plan = json.loads(result.stdout)
        assert blocked_plan == ordinary_plan and not (blocked / "new-library").exists()
        print("CONFIRMED blocked_parent: planner reports ADD beneath an existing regular file")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
