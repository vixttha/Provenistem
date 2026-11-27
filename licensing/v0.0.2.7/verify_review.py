"""Check review-only proposal and simulated packaging; never authorize distribution."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
DRAFT = ROOT / "licensing/v0.0.2.7"
SOURCE = ROOT / "packages/provenistem"
sys.path.insert(0, str(SOURCE / "tools"))
import adopter
M = json.loads((DRAFT / "baseline-pins.json").read_text(encoding="utf-8"))
S = json.loads((DRAFT / "scope.json").read_text(encoding="utf-8"))
PAIR = ("PROVENISTEM-LICENSE.md", "PROVENISTEM-NOTICE.md")

def require(ok, msg):
    if not ok:
        raise ValueError(msg)

def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)

def snapshot(root):
    return {p.relative_to(root).as_posix(): p.read_bytes()
            for p in root.rglob("*") if p.is_file()}

def verify_pair(root, expected, *, distribution=False):
    for name in PAIR:
        p = root / name
        require(p.is_file() and not p.is_symlink(), "missing or unsafe: " + name)
        require(p.read_bytes() == expected[name], "changed: " + name)
    if distribution:
        require(S["status"] != "REVIEW_ONLY" and S["operative"] is True,
                "review-only; distribution not authorized")

def reject(fn, msg):
    try:
        fn()
    except ValueError as exc:
        require(msg in str(exc), "unexpected rejection: " + str(exc))
    else:
        raise RuntimeError("negative control accepted: " + msg)

def main():
    require(S["status"] == "REVIEW_ONLY" and not S["operative"]
            and S["approved_additions"] == [] and S["owner_declaration"] == "PENDING",
            "scope activated")
    require(S["baseline"] == M["base"], "baseline mismatch")
    for row in M["main_inventory"]:
        require(git("rev-parse", "HEAD:" + row["path"]).decode().strip() == row["blob"],
                "changed baseline: " + row["path"])
    for row in M["refs"]:
        subprocess.run(["git","fetch","--no-tags","--depth=1","origin",row["commit"]],
                       cwd=ROOT, check=True)
        require(git("rev-parse","FETCH_HEAD").decode().strip() == row["commit"], "wrong source")
        for p, sha in row["notices"].items():
            require(git("rev-parse",row["commit"]+":"+p).decode().strip()==sha,"notice drift")
        print("NOTICE_PIN",row["ref"],len(row["notices"]))
    expected = {n: git("show", "HEAD:licensing/v0.0.2.7/" + n) for n in PAIR}
    require(git("hash-object", str(DRAFT / PAIR[0])).decode().strip() ==
            S["polyform_license_blob"] == "90abd0e6c64a135f42451762337a397bf27f4862",
            "official PolyForm text changed")
    require(b"REVIEW ONLY" in expected[PAIR[1]], "missing draft label")
    verify_pair(DRAFT, expected)
    reject(lambda: verify_pair(DRAFT, expected, distribution=True), "review-only")
    for p in S["prospective_path_allowlist"]:
        require((SOURCE / p).is_file(), "invalid prospective path")
    require(len(S["prospective_path_allowlist"]) == 9, "scope count")
    mit = git("show", M["base"] + ":packages/provenistem/LICENSE")
    require(mit == (ROOT/"LICENSE").read_bytes() == (SOURCE/"LICENSE").read_bytes(), "MIT changed")
    before = snapshot(SOURCE)
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        for profile, count in M["expected_profiles"].items():
            host = root / profile
            plan = adopter.plan(SOURCE, host, profile)
            require(not plan["writes"] and len(plan["entries"]) == count and not host.exists(),
                    "existing package changed")
            require(not any(e["path"] in PAIR for e in plan["entries"]), "draft leaked")
            for e in plan["entries"]:
                p = host / e["path"]
                p.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(SOURCE / e["path"], p)
            require((host/"LICENSE").read_bytes() == mit, "missing MIT")
            for name in PAIR:
                (host/name).write_bytes(expected[name])
            require(len(snapshot(host)) == count+2, "preview inventory")
            verify_pair(host, expected)
            reject(lambda: verify_pair(host, expected, distribution=True), "review-only")
            for name in PAIR:
                p = host/name
                p.unlink()
                reject(lambda: verify_pair(host,expected), name)
                p.mkdir()
                reject(lambda: verify_pair(host,expected), name)
                p.rmdir()
                p.write_bytes(expected[name]+b"tampered")
                reject(lambda: verify_pair(host,expected), name)
                p.write_bytes(expected[name])
            (host/"LICENSE").write_bytes(b"HOST LICENSE")
            for n in PAIR:
                (host/n).write_bytes(b"HOST OWNED "+n.encode())
            saved = snapshot(host)
            result = adopter.plan(SOURCE,host,profile)
            require(not result["writes"] and {"path":"LICENSE","action":"REVIEW_LOCAL_DIFFERENCE"}
                    in result["entries"], "host license collision missed")
            reject(lambda: verify_pair(host, expected), "changed")
            require(snapshot(host)==saved, "host changed")
            print("PROFILE_PREVIEW_PASS",profile,count,count+2)
    require(snapshot(SOURCE)==before,"source changed")
    print("REVIEW_PASS: exact draft pair, preserved MIT, draft refusal, 3 preview profiles")
if __name__ == "__main__":
    main()
