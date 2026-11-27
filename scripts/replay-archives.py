"""Replay committed archive pins without a producer or product checkout."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSIONS = ("v0.0.1", "v0.0.2", "v0.0.2.1", "v0.0.2.2", "v0.0.2.3", "v0.0.2.4")
PROJECT = "vixttha/Provenistem"
INDEX = "packages/provenistem/tools/library.py"


def require(condition, message):
    if not condition:
        raise SystemExit(message)


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def invoke(action, options, *, reject=None):
    result = subprocess.run(["node", str(ROOT / "veraphifiy.mjs"), action, *options],
                            capture_output=True, text=True, encoding="utf-8", timeout=60)
    if reject is not None:
        require(result.returncode != 0 and reject in result.stderr,
                f"negative control failed: {reject}: {result.stderr}")
        return
    require(result.returncode == 0, result.stderr)
    return json.loads(result.stdout)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--collect", action="store_true",
                        help="bootstrap only: collect candidate pins; not final qualification")
    args = parser.parse_args()
    root = args.output.resolve()
    committed = load(ROOT / "archive-pins.json")
    require(set(committed) <= set(VERSIONS), "unknown committed version")
    require(args.collect or set(committed) == set(VERSIONS), "incomplete committed pins")
    require(set(VERSIONS[:2]) <= set(committed), "historical pins required")
    before = {p.name: digest(p) for p in (root / "archive").glob("*.json")}
    require(len(before) == len(VERSIONS), "archive inventory mismatch")
    for version in VERSIONS:
        manifest = load(ROOT / "manifests" / (version + ".json"))
        imported = load(root / version / "import.json")
        lookup = load(root / version / "lookup.json")
        row = {k: imported[k] for k in ("source", "graph_sha256", "receipt_sha256", "archive_sha256")}
        row["index_line"] = lookup["citations"][0]["line"]
        require(row["source"] == manifest["source_commit"], f"{version}: source mismatch")
        require(all(re.fullmatch("[a-f0-9]{64}", row[k]) for k in
                    ("graph_sha256", "receipt_sha256", "archive_sha256")), "invalid digest")
        if version in committed:
            require(row == committed[version], f"{version}: durable pin mismatch")
        else:
            require(args.collect, "missing durable pin")
        for name in ("graph", "receipt"):
            path = root / version / (name + ".json")
            require(digest(path) == row[name + "_sha256"], f"{version}: {name} mismatch")
            checked = ROOT / "graphs" / version / (name + ".json")
            if checked.exists():
                require(path.read_bytes() == checked.read_bytes(), f"{version}: committed map mismatch")
            else:
                require(args.collect, f"{version}: committed map absent")
        base = ["--archive", str(root / "archive"), "--project", PROJECT,
                "--version", version]
        options = base + ["--source", row["source"], "--archive-sha256", row["archive_sha256"]]
        verified = invoke("verify", options)
        located = invoke("lookup", options + ["--feature", "feature:generated-indexes"])
        require(all(verified[k] == row[k] for k in ("source", "graph_sha256", "receipt_sha256", "archive_sha256")),
                f"{version}: replay digest mismatch")
        require(located["citations"] == [{"path": INDEX, "line": row["index_line"]}],
                f"{version}: replay location mismatch")
        wrong = "0" * 64
        require(wrong != row["archive_sha256"], "negative control collision")
        invoke("verify", base + ["--source", row["source"], "--archive-sha256", wrong],
               reject="Archive SHA-256 mismatch")
        invoke("verify", base + ["--source", "0" * 40, "--archive-sha256", row["archive_sha256"]],
               reject="Archive source commit mismatch")
        print("ARCHIVE_PIN " + json.dumps({"version": version, **row}, sort_keys=True))
        if args.collect and version not in committed:
            for name in ("graph", "receipt"):
                data = (root / version / (name + ".json")).read_bytes().decode("utf-8")
                for offset in range(0, len(data), 1000):
                    print("MAP_CHUNK " + json.dumps({"version": version, "name": name,
                          "offset": offset, "text": data[offset:offset+1000]}, ensure_ascii=True))
    require(before == {p.name: digest(p) for p in (root / "archive").glob("*.json")},
            "read-only replay changed archive")
    print("REPLAY PASS: six archives; exact digests, citations, negative controls and read-only preservation"
          + (" (collection only)" if args.collect else ""))


if __name__ == "__main__":
    main()
