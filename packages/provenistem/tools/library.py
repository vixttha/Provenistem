#!/usr/bin/env python3
"""Optional, dependency-free structural validator and index builder.

Not a JSON-Schema compliance engine; does not authenticate evidence or approve releases.
"""
import argparse
import json
import re
from pathlib import Path, PurePosixPath, PureWindowsPath

ROOT = Path(__file__).resolve().parents[1]
DECISION_STATES = {"adopted", "parked", "rejected", "superseded", "duplicate", "retired"}


def shape(value, schema, where):
    """Check only the JSON-Schema v1 keywords used by this template."""
    issues = []
    kind = schema.get("type")
    types = {"object": lambda x: isinstance(x, dict),
             "array": lambda x: isinstance(x, list),
             "string": lambda x: isinstance(x, str),
             "integer": lambda x: type(x) is int}
    if kind in types and not types[kind](value):
        return [f"{where}: expected {kind}"]
    if "const" in schema and (type(value) is not type(schema["const"]) or value != schema["const"]):
        issues.append(f"{where}: const mismatch")
    if "enum" in schema and value not in schema["enum"]:
        issues.append(f"{where}: invalid enum value")
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            issues.append(f"{where}: text too short")
        if "pattern" in schema and not re.fullmatch(schema["pattern"], value):
            issues.append(f"{where}: invalid format")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            issues.append(f"{where}: too few entries")
        if schema.get("uniqueItems") and len(set(map(json.dumps, value))) != len(value):
            issues.append(f"{where}: duplicate entries")
        for i, item in enumerate(value):
            issues.extend(shape(item, schema.get("items", {}), f"{where}[{i}]"))
    if isinstance(value, dict):
        props = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in value:
                issues.append(f"{where}: missing {key}")
        if schema.get("additionalProperties") is False:
            for key in value.keys() - props.keys():
                issues.append(f"{where}: unknown field {key}")
        for key in value.keys() & props.keys():
            issues.extend(shape(value[key], props[key], f"{where}.{key}"))
    return issues


def safe_repo_path(value):
    return (isinstance(value, str) and bool(value) and
            "\\" not in value and not PurePosixPath(value).is_absolute() and
            not PureWindowsPath(value).is_absolute() and
            all(p not in ("", ".", "..") for p in value.split("/")))


def read_records(root, section, schema):
    problems, records = [], {}
    folder = root / section / "records"
    if not folder.is_dir():
        return [f"missing {section}/records directory"], records
    for path in sorted(folder.iterdir()):
        if path.name == ".gitkeep":
            continue
        if not path.is_file() or path.suffix != ".json":
            problems.append(f"{path}: unexpected record entry")
            continue
        try:
            row = json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, OSError) as exc:
            problems.append(f"{path}: bad JSON: {exc}")
            continue
        if not isinstance(row, dict):
            problems.append(f"{path}: expected object")
            continue
        ident = row.get("id")
        if not isinstance(ident, str) or path.stem != ident:
            problems.append(f"{path}: mismatched ID and filename")
            continue
        problems.extend(shape(row, schema, str(path)))
        if ident in records:
            problems.append(f"{path}: repeated record ID")
        records[ident] = row
    return problems, records


def validate(root=ROOT):
    problems = []
    try:
        idea_schema = json.loads((root / "ideas/schema/v1/idea.schema.json").read_text(encoding="utf-8"))
        feat_schema = json.loads((root / "features/schema/v1/feature.schema.json").read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        return [f"schema unavailable or invalid: {exc}"], {}, {}
    for path, schema in (("ideas", idea_schema), ("features", feat_schema)):
        if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            problems.append(f"{path}: schema dialect changed")
    p, ideas = read_records(root, "ideas", idea_schema)
    problems.extend(p)
    p, feats = read_records(root, "features", feat_schema)
    problems.extend(p)
    for ident, row in ideas.items():
        if row.get("lifecycle_status") in DECISION_STATES and "decision" not in row:
            problems.append(f"{ident}: decision-bearing state without recorded decision")
        test = row.get("testing") or {}
        if test.get("status") == "tested" and (
            test.get("outcome") not in {"pass", "fail", "mixed", "inconclusive"} or
            not test.get("refs")):
            problems.append(f"{ident}: tested without outcome and references")
        for target in row.get("related_ideas", []):
            if target == ident or target not in ideas:
                problems.append(f"{ident}: missing or self-linked idea {target}")
        for ev in row.get("evidence", []):
            if not safe_repo_path(ev.get("path")):
                problems.append(f"{ident}: unsafe evidence path")
    for ident, row in feats.items():
        for target in row.get("idea_ids", []):
            if target not in ideas:
                problems.append(f"{ident}: unresolved idea {target}")
        test = row.get("testing") or {}
        if test.get("status") == "tested" and (
            test.get("outcome") not in {"pass", "fail", "mixed", "inconclusive"} or
            not test.get("refs")):
            problems.append(f"{ident}: tested without outcome and references")
        if row.get("lifecycle_status") == "verified":
            if (row.get("implementation_status") != "implemented" or
                test.get("status") != "tested" or test.get("outcome") != "pass" or
                not any(e.get("kind") in ("test", "audit") for e in row.get("evidence", []))):
                problems.append(f"{ident}: unsupported verified claim")
        for ev in row.get("evidence", []):
            if not safe_repo_path(ev.get("source_path")):
                problems.append(f"{ident}: unsafe evidence path")
    return problems, ideas, feats


def cell(text):
    return (str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace("|", "&#124;").replace("\r", " ").replace("\n", " "))


def index(kind, rows):
    name = "Ideas" if kind == "ideas" else "Features"
    prefix = "IDEA" if kind == "ideas" else "FEAT"
    singular = "idea" if kind == "ideas" else "feature"
    description = (f"No canonical {singular} records yet." if not rows
                   else f"Generated from canonical {singular} records.")
    output = [f"# {name} — index (derived)", "",
              (f"> {description} This index is a convenience view; the records in "
               f"`{kind}/records/` are authoritative. Optional generator: "
               "`python tools/library.py build`."), "",
              f"| ID | {singular.title()} | Lifecycle | Implementation |",
              "| --- | --- | --- | --- |"]
    for ident, data in sorted(rows.items()):
        output.append(f"| {cell(ident)} | {cell(data.get('title', ''))} | "
                      f"{cell(data.get('lifecycle_status', ''))} | "
                      f"{cell(data.get('implementation_status', ''))} |")
    return "\n".join(output) + "\n"


def run(root, action):
    problems, ideas, feats = validate(root)
    if problems:
        for issue in problems:
            print("FAIL:", issue)
        return 1
    views = {"ideas": index("ideas", ideas), "features": index("features", feats)}
    if action == "build":
        for kind, content in views.items():
            (root / kind / "INDEX.md").write_text(content, encoding="utf-8")
    else:
        for kind, expected in views.items():
            path = root / kind / "INDEX.md"
            if not path.is_file() or path.read_text(encoding="utf-8") != expected:
                problems.append(f"{kind}/INDEX.md: stale or missing; run build")
    if problems:
        for issue in problems:
            print("FAIL:", issue)
        return 1
    print(f"PASS: {len(ideas)} ideas, {len(feats)} features, index {action}; "
          "STRUCTURE ONLY — no external evidence or authority verified")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["check", "build"])
    args = parser.parse_args()
    raise SystemExit(run(ROOT, args.action))
