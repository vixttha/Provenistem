"""CI-only protected licensing checks; no imports of portable product modules."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "audit/ci-lifecycle-policy.json"

def require(condition, message):
    if not condition:
        raise ValueError(message)

def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.STDOUT)

def tree_entries(root, name, recursive=False):
    flags = ["-r"] if recursive else []
    raw = git(root, "ls-tree", *flags, "-z", "HEAD", "--", name)
    result = {}
    for item in raw.split(b"\0"):
        if item:
            meta, path = item.split(b"\t", 1)
            result[path.decode("utf-8")] = tuple(meta.decode("ascii").split())
    return result

def plain(path, directory=False):
    return (not path.is_symlink() and not path.is_junction()
            and (path.is_dir() if directory else path.is_file()))

def checked_path(root, relative, directory=False):
    path = root
    parts = Path(relative).parts
    require(parts and not Path(relative).is_absolute() and ".." not in parts, "invalid policy path")
    for i, part in enumerate(parts):
        path = path / part
        require(plain(path, directory or i < len(parts) - 1), "missing or unsafe path: " + relative)
    return path

def verify(root):
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    require(policy["schema"] == "provenistem/ci-lifecycle/v1", "unsupported policy")
    require(Path(git(root, "rev-parse", "--show-toplevel").decode("utf-8").strip()).resolve() == root.resolve(),
            "not the Git checkout root")
    for name, expected in policy["protected_files"].items():
        require(tree_entries(root, name) == {name: ("100644", "blob", expected["blob"])},
                "protected committed path differs: " + name)
        data = checked_path(root, name).read_bytes()
        require(hashlib.sha256(data).hexdigest() == expected["sha256"],
                "protected working-tree bytes differ: " + name)
    archive = policy["historical_directory"]
    name = archive["path"]
    require(tree_entries(root, name) == {name: ("040000", "tree", archive["tree"])},
            "historical tree differs: " + name)
    directory = checked_path(root, name, directory=True)
    entries = tree_entries(root, name, recursive=True)
    # The frozen archive is flat; reject even ignored or empty extra directories.
    actual = {p.relative_to(root).as_posix() for p in directory.iterdir()}
    require(actual == set(entries), "historical working-tree inventory differs: " + name)
    for path, (mode, kind, _) in entries.items():
        require(mode == "100644" and kind == "blob", "unsafe historical entry: " + path)
        data = checked_path(root, path).read_bytes()
        require(data == git(root, "show", "HEAD:" + path), "historical working-tree bytes differ: " + path)
    print("CURRENT_LICENSING_PASS", git(root, "rev-parse", "HEAD").decode().strip(),
          "protected paths and historical archive unchanged; no release authority")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="Git checkout root (fixture testing supported)")
    args = parser.parse_args()
    try:
        verify(args.root.absolute())
    except (ValueError, OSError, KeyError, TypeError, subprocess.CalledProcessError) as exc:
        print("CURRENT_LICENSING_FAIL:", exc, file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
