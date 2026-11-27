"""Check standalone adaptations against exact approved upstream Git blobs."""
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = "ed5650085e33cf142a37de695757a4df999a7cf3"
BUNDLE = "6c5d22c1f11a4952d4a79d800b946f4f8d76d778"
FILES = (
    ("LICENSE", "LICENSE", None),
    ("lib/LYDITE-LICENSE", "test-vault/LICENSE", None),
    ("lib/handoff-profile.json", "test-vault/handoff-profile.json", None),
    ("veraphifiy.mjs", "veraphifiy.mjs",
     (b"./test-vault/javascript/inspect-evidence.mjs", b"./lib/inspect-evidence.mjs")),
    ("lib/inspect-evidence.mjs", "test-vault/javascript/inspect-evidence.mjs",
     (b"../handoff-profile.json", b"./handoff-profile.json")),
)


def main():
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["git", "init", "-q", tmp], check=True)
        def git(*args):
            return subprocess.check_output(["git", "-C", tmp, *args])
        for repo, commit in (("Veraphify", UPSTREAM), ("Version-Issues-Hub", BUNDLE)):
            git("fetch", "-q", "--no-tags", "--depth=1",
                f"https://github.com/vixttha/{repo}.git", commit)
            if git("rev-parse", "FETCH_HEAD").decode().strip() != commit:
                raise SystemExit("upstream pin mismatch")
        for local, source, change in FILES:
            upstream = git("show", f"{UPSTREAM}:{source}")
            if change:
                if upstream.count(change[0]) != 1:
                    raise SystemExit("unexpected adaptation anchor")
                upstream = upstream.replace(*change)
            local_bytes = (ROOT / local).read_bytes()
            if local_bytes != upstream or local_bytes != git("show", f"{BUNDLE}:{local}"):
                raise SystemExit("runtime provenance mismatch: " + local)
            print("RUNTIME MATCH " + local)


if __name__ == "__main__":
    main()
