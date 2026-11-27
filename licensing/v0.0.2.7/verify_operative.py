"""CI-only exact-scope and real package verification. No publication or authority."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "packages/provenistem"
REVIEW = ROOT / "licensing/v0.0.2.7"
BASE = "4b57d194e8f79351dd41a548e7c0a574c97ecb94"
DRAFT = "2931c0742e83aca101f475b5afbffdc7fd9a8692"
ORIGIN = "bae5899a180ae52e05c896d758d01967e0d28a87"
MODULE = "packages/provenistem/tools/license_guard.py"
MODULE_BLOB = "7aff9c547bc2a8c529346a5ada90b538ba9480cb"
MODULE_SHA256 = "50b0d06b0ec8e6e92e85e6d9ed256d9ffdd599b3fdf8ab2962585ad7fa4b80bf"
NOTICE_PINS = {
    "LICENSE": "c12fd1b8185dd55dc131bce9529719650d928b3b2d92016d721ff8258e083c93",
    "PROVENISTEM-LICENSE.md": "9eb48619fbc193ab7bb327b090cfcc703000265b83e670f81f231d0b1c43c56e",
    "PROVENISTEM-NOTICE.md": "65fb104fc08c63534e4366ceadca61fe79aa7b9ba3ecfc787ba8b4ffb4013255",
}
CHANGED = {
    "README.md", "audit/adoption-copy-evidence.json",
    "packages/provenistem/README.md", "packages/provenistem/docs/ADOPTION.md",
    "packages/provenistem/tests/test_adopter_profiles.py",
    "packages/provenistem/tools/adopter.py",
}

def require(condition, message):
    if not condition:
        raise ValueError(message)

def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)

def fetch(commit):
    subprocess.run(["git", "fetch", "--no-tags", "--depth=1", "origin", commit],
                   cwd=ROOT, check=True)
    require(git("rev-parse", "FETCH_HEAD").decode().strip() == commit, "wrong fetch")

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def snapshot(path):
    return {p.relative_to(path).as_posix(): p.read_bytes()
            for p in path.rglob("*") if p.is_file()}

def tree(commit):
    result = {}
    for raw in git("ls-tree", "-rz", commit).split(b"\0"):
        if not raw:
            continue
        meta, path = raw.split(b"\t", 1)
        mode, kind, sha = meta.decode().split()
        require(kind == "blob", "unexpected non-blob entry")
        result[path.decode("utf-8")] = (mode, sha)
    return result

def copy_plan(source, dest, plan):
    require(not plan["writes"], "planner wrote")
    for row in plan["entries"]:
        require(row["action"] == "ADD", "unexpected blank action")
        target = dest / row["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / row["path"], target)

def main():
    # Validate checkout bytes before importing any portable module.
    current = tree("HEAD")
    for relative, (mode, _) in current.items():
        path = ROOT / relative
        require(mode in ("100644", "100755") and path.is_file()
                and not path.is_symlink()
                and all(not parent.is_symlink() for parent in path.parents
                        if parent != ROOT and ROOT in parent.parents)
                and path.read_bytes() == git("show", "HEAD:" + relative),
                "changed working-tree baseline: " + relative)
    fetch(BASE)
    baseline = tree(BASE)
    actual_changed = {p for p in baseline if current.get(p) != baseline[p]}
    require(actual_changed == CHANGED, "unexpected baseline change: " + str(actual_changed))
    require(len(baseline) == 43, "baseline count")
    print("BASELINE_PRESERVED", len(baseline) - len(CHANGED), "MIT-edited", len(CHANGED))
    fetch(DRAFT)
    require(git("show", DRAFT + ":licensing/v0.0.2.7/baseline-pins.json")
            == (REVIEW / "baseline-pins.json").read_bytes(), "historical inventory changed")
    history = json.loads((REVIEW / "baseline-pins.json").read_text(encoding="utf-8"))
    for row in history["refs"]:
        fetch(row["commit"])
        for path, sha in row["notices"].items():
            require(git("rev-parse", row["commit"] + ":" + path).decode().strip() == sha,
                    "historical notice changed")
        print("NOTICE_PIN", row["ref"], len(row["notices"]))
    scope = json.loads((REVIEW / "operative-scope.json").read_text(encoding="utf-8"))
    require(scope["status"] == "CANDIDATE_AWAITING_FINAL_OWNER_APPROVAL"
            and scope["distribution"] == "NOT_AUTHORIZED_BY_CANDIDATE"
            and scope["mit_baseline"] == BASE
            and scope["previous_review_commit"] == DRAFT
            and scope["owner_declaration_receipt"] ==
                "https://github.com/vixttha/Provenistem/issues/8#issuecomment-7228966383",
            "approval or baseline mismatch")
    require(set(scope["baseline_changes_retained_under_mit"]) == CHANGED, "MIT edit scope mismatch")
    require(scope["license_sha256"] == NOTICE_PINS, "notice pin manifest changed")
    rows = scope["scheduled_restricted_additions"]
    require(len(rows) == 1, "restricted scope expanded")
    row = rows[0]
    require(row["path"] == MODULE and row["origin_commit"] == ORIGIN
            and row["git_blob"] == MODULE_BLOB and row["sha256"] == MODULE_SHA256
            and row["license"] == "PolyForm-Strict-1.0.0"
            and MODULE not in baseline and current[MODULE][1] == MODULE_BLOB
            and digest(ROOT / MODULE) == MODULE_SHA256, "restricted module mismatch")
    fetch(ORIGIN)
    require(tree(ORIGIN)[MODULE][1] == MODULE_BLOB, "module origin mismatch")
    require(all(digest(SOURCE / n) == sha for n, sha in NOTICE_PINS.items()), "legal byte mismatch")
    require((ROOT / "LICENSE").read_bytes() == (SOURCE / "LICENSE").read_bytes(),
            "root MIT differs")
    require(current["packages/provenistem/PROVENISTEM-LICENSE.md"][1] ==
            "90abd0e6c64a135f42451762337a397bf27f4862", "official Strict text differs")
    notice = (SOURCE / "PROVENISTEM-NOTICE.md").read_text(encoding="utf-8")
    require(all(v in notice for v in (ORIGIN, MODULE_BLOB, MODULE_SHA256,
                                      "tools/license_guard.py", "prior", "MIT")),
            "notice scope mismatch")
    sys.path.insert(0, str(SOURCE / "tools"))
    import adopter
    import library
    require(adopter.LICENSE_DIGESTS == NOTICE_PINS, "planner pins mismatch")
    before = snapshot(SOURCE)
    with tempfile.TemporaryDirectory() as scratch:
        root = Path(scratch)
        profiles = {"basic": 23, "tools": 26, "full": 33}
        require(scope["expected_profiles"] == profiles, "profile pins mismatch")
        for profile, count in profiles.items():
            dest = root / profile
            plan = adopter.plan(SOURCE, dest, profile)
            require(not dest.exists() and plan["status"] == "NEW_DESTINATION"
                    and len(plan["entries"]) == count, "profile plan mismatch")
            copy_plan(SOURCE, dest, plan)
            actual = snapshot(dest)
            require(len(actual) == count and all(data == before[path] for path, data in actual.items()),
                    "actual copy differs")
            require(all(digest(dest / n) == sha for n, sha in NOTICE_PINS.items()),
                    "missing or changed copied legal notice")
            require(("tools/license_guard.py" in actual) == (profile != "basic"),
                    "incorrect optional scope")
            require(library.run(dest, "check") == 0, "invalid copied catalog")
            require(snapshot(dest) == actual, "copy check wrote")
            print("ACTUAL_PROFILE_PASS", profile, count)
        # Reconstruct the exact preceding MIT package, not an invented old fixture.
        legacy = root / "legacy"
        prefix = "packages/provenistem/"
        for path in baseline:
            if path.startswith(prefix):
                dest = legacy / path.removeprefix(prefix)
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(git("show", BASE + ":" + path))
        require(len(snapshot(legacy)) == 30, "legacy inventory mismatch")
        for section, kind in (("ideas", "idea"), ("features", "feature")):
            row = json.loads((legacy / "templates" / (kind + ".example.json")).read_text(encoding="utf-8"))
            if kind == "feature":
                row["idea_ids"] = ["IDEA-000001"]
            (legacy / section / "records" / (row["id"] + ".json")).write_text(
                json.dumps(row, indent=2), encoding="utf-8")
        require(library.run(legacy, "build") == 0, "legacy fixture invalid")
        old = snapshot(legacy)
        require(library.run(legacy, "check") == 0, "legacy check failed")
        plan = adopter.plan(SOURCE, legacy, "full")
        actions = {e["path"]: e["action"] for e in plan["entries"]}
        require(not plan["writes"] and actions["LICENSE"] == "SAME"
                and all(actions[n] == "ADD" for n in ("PROVENISTEM-LICENSE.md",
                      "PROVENISTEM-NOTICE.md", "tools/license_guard.py"))
                and snapshot(legacy) == old, "legacy upgrade preflight changed files")
        # In this disposable fixture only, simulate reviewed source-file updates.
        for row in plan["entries"]:
            if row["action"] in ("ADD", "REVIEW_LOCAL_DIFFERENCE"):
                path = legacy / row["path"]
                path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(SOURCE / row["path"], path)
        after = snapshot(legacy)
        for path in old:
            if "/records/" in path or path.endswith("/INDEX.md") or path == "LICENSE":
                require(after[path] == old[path], "legacy data or MIT changed: " + path)
        require(library.run(legacy, "check") == 0, "upgraded records invalid")
        (legacy / "PROVENISTEM-NOTICE.md").write_bytes(b"HOST OWNED NOTICE")
        (legacy / "LICENSE").write_bytes(b"HOST OWNED LICENSE")
        conflict = snapshot(legacy)
        plan = adopter.plan(SOURCE, legacy, "full")
        actions = {e["path"]: e["action"] for e in plan["entries"]}
        require(not plan["writes"] and actions["LICENSE"] == actions["PROVENISTEM-NOTICE.md"]
                == "REVIEW_LOCAL_DIFFERENCE" and snapshot(legacy) == conflict,
                "host license conflict overwritten")
        print("PINNED_LEGACY_UPGRADE_PASS: preserved MIT, records and host conflicts")
    require(snapshot(SOURCE) == before, "source changed")
    print("OPERATIVE_CANDIDATE_PASS: exact scoped module, historical rights, actual profiles; no release authorization")

if __name__ == "__main__":
    main()
