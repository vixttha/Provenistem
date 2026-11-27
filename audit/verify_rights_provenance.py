"""Technical notice/provenance audit; no legal-title assertion."""
import ast
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
M = json.loads((ROOT / "audit/rights-provenance-pins.json").read_text(encoding="utf-8"))
SOURCE = ROOT / "packages/provenistem"
sys.path.insert(0, str(SOURCE / "tools"))
import adopter

def require(ok, message):
    if not ok:
        raise RuntimeError(message)

def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)

def snapshot(path):
    return {p.relative_to(path).as_posix(): p.read_bytes()
            for p in path.rglob("*") if p.is_file()}

def main():
    subprocess.run(["git", "fetch", "--no-tags", "--depth=1", "origin", M["base"]],
                   cwd=ROOT, check=True)
    require(git("diff", "--name-only", M["base"], "HEAD").decode().splitlines()
            == [".github/workflows/rights-provenance-audit.yml",
                "audit/rights-provenance-pins.json", "audit/verify_rights_provenance.py"],
            "audit changed non-audit content")
    for row in M["main_inventory"]:
        require(git("rev-parse", "HEAD:" + row["path"]).decode().strip() == row["blob"],
                "changed baseline blob: " + row["path"])
    print("BASELINE_BLOBS", len(M["main_inventory"]))
    for row in M["refs"]:
        subprocess.run(["git", "fetch", "--no-tags", "--depth=1", "origin", row["commit"]],
                       cwd=ROOT, check=True)
        require(git("rev-parse", "FETCH_HEAD").decode().strip() == row["commit"], "wrong pin")
        for path, expected in row["notices"].items():
            require(git("rev-parse", row["commit"] + ":" + path).decode().strip() == expected,
                    "notice drift: " + row["ref"] + "/" + path)
        print("NOTICE_PIN", row["ref"], row["commit"], len(row["notices"]))
    license_bytes = git("show", M["base"] + ":packages/provenistem/LICENSE")
    require(license_bytes == git("show", M["base"] + ":LICENSE"), "MIT pair differs")
    require((SOURCE / "LICENSE").read_bytes() == license_bytes, "working notice differs")
    print("MIT_SHA256", hashlib.sha256(license_bytes).hexdigest())
    before = snapshot(SOURCE)
    imports = {}
    for p in sorted(SOURCE.rglob("*.py")):
        names = set()
        for n in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
            if isinstance(n, ast.Import):
                names.update(a.name.split(".")[0] for a in n.names)
            elif isinstance(n, ast.ImportFrom) and n.module:
                names.add(n.module.split(".")[0])
        imports[p.relative_to(SOURCE).as_posix()] = sorted(names)
    require(all(n in sys.stdlib_module_names or n in {"library", "adopter"}
                for names in imports.values() for n in names), "nonstandard import")
    print("STATIC_IMPORTS", json.dumps(imports, sort_keys=True))
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        for profile, count in M["expected_profiles"].items():
            dest = root / profile
            plan = adopter.plan(SOURCE, dest, profile)
            require(plan["status"] == "NEW_DESTINATION" and not plan["writes"], "bad plan")
            require(len(plan["entries"]) == count and not dest.exists(), "wrong inventory")
            require([e for e in plan["entries"] if e["path"] == "LICENSE"] ==
                    [{"path": "LICENSE", "action": "ADD"}], "missing notice")
            for e in plan["entries"]:
                require(e["action"] == "ADD", "unexpected action")
                p = dest / e["path"]
                p.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(SOURCE / e["path"], p)
            require((dest / "LICENSE").read_bytes() == license_bytes, "copy notice differs")
            require(len(snapshot(dest)) == count, "copied inventory differs")
            for payload, action in ((license_bytes, "SAME"),
                                    (b"HOST-OWNED LICENSE\n", "REVIEW_LOCAL_DIFFERENCE")):
                (dest / "LICENSE").write_bytes(payload)
                saved = snapshot(dest)
                review = adopter.plan(SOURCE, dest, profile)
                require(not review["writes"] and {"path":"LICENSE","action":action} in review["entries"],
                        "license conflict misclassified")
                require(snapshot(dest) == saved, "host bytes changed")
            (dest / "LICENSE").unlink()
            (dest / "LICENSE").mkdir()
            review = adopter.plan(SOURCE, dest, profile)
            require({"path":"LICENSE","action":"CONFLICT_DIRECTORY"} in review["entries"],
                    "directory conflict missed")
            require((dest / "LICENSE").is_dir(), "directory replaced")
            print("PROFILE_PASS", profile, count, "notice copy and conflict preservation")
        fixture = root / "source"
        shutil.copytree(SOURCE, fixture)
        (fixture / "LICENSE").unlink()
        for profile in M["expected_profiles"]:
            try:
                adopter.plan(fixture, root / "missing", profile)
            except ValueError as exc:
                require("LICENSE" in str(exc), "missing license diagnostic")
            else:
                raise RuntimeError("missing license accepted")
        (fixture / "LICENSE").write_bytes(b"not an authenticated license")
        result = adopter.plan(fixture, root / "unverified", "full")
        require(result["status"] == "NEW_DESTINATION" and not result["writes"],
                "unexpected inventory-only behavior")
        require(not (root / "unverified").exists(), "planner wrote destination")
        print("KNOWN_LIMIT: present arbitrary license bytes pass inventory-only preflight")
    require(snapshot(SOURCE) == before, "source changed")
    print("AUDIT_PASS: exact notices, 3 copy profiles, conflict preservation; no rights clearance")

if __name__ == "__main__":
    main()
