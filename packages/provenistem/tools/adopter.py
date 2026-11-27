#!/usr/bin/env python3
"""Read-only, no-clobber adoption/upgrade preflight.

Never copies, modifies, deletes or overwrites host or source files.
Only the selected candidate is inspected; no unrelated repository is accessed.
This is NOT an atomic safeguard against concurrent filesystem changes.
"""
import argparse
import json
from pathlib import Path

import library
from license_guard import verify_notices

PACKAGE_ROOTS = ("ideas", "features", "templates")
PACKAGE_TOPLEVEL = ("README.md", "LICENSE", "LIBRARY-AGENT-GUIDE.md",
                    "PROVENISTEM-LICENSE.md", "PROVENISTEM-NOTICE.md")
PACKAGE_DOCS = {
    "ADOPTION.md", "ISOLATION.md", "LIFECYCLE.md",
    "ONE-WAY-BOUNDARY.md", "PROVENANCE.md",
    "PORTABILITY-AND-MODULE-CONTRACT.md", "PORTABILITY-AND-MODULE-CONTRACT.json",
    "PRODUCT-SCOPE-LOCK.md",
}
PACKAGE_TOOL_FILES = {"library.py", "adopter.py", "license_guard.py"}
PACKAGE_TEST_FILES = {
    "test_library.py", "test_one_way_boundary.py", "test_hardening.py",
    "test_adopter_profiles.py", "test_v002_six_team_repairs.py",
    "test_modularity_contract.py", "test_unicode_index_integrity.py",
}


# The basic distribution includes the documented blank-record placeholders.
PACKAGE_BASIC_FILES = (
    set(PACKAGE_TOPLEVEL)
    | {f"docs/{name}" for name in PACKAGE_DOCS}
    | {f"{section}/{name}" for section in ("ideas", "features")
       for name in ("README.md", "INDEX.md", "records/.gitkeep")}
    | {"ideas/schema/v1/idea.schema.json", "features/schema/v1/feature.schema.json",
       "templates/idea.example.json", "templates/feature.example.json"}
)
PROFILES = ("auto", "basic", "tools", "full")
# Revision-specific legal inventory; not source authentication or authorization.
LICENSE_DIGESTS = {
    "LICENSE": "c12fd1b8185dd55dc131bce9529719650d928b3b2d92016d721ff8258e083c93",
    "PROVENISTEM-LICENSE.md": "9eb48619fbc193ab7bb327b090cfcc703000265b83e670f81f231d0b1c43c56e",
    "PROVENISTEM-NOTICE.md": "65fb104fc08c63534e4366ceadca61fe79aa7b9ba3ecfc787ba8b4ffb4013255"
}


def candidates(source, profile="auto"):
    if profile not in PROFILES:
        raise ValueError(f"unknown source profile: {profile}")
    if profile == "auto":
        # A present (even malformed) optional group selects its entire inventory.
        # Explicit full/tools selection also catches entirely absent groups.
        tests = source / "tests"
        tools = source / "tools"
        if tests.is_symlink() or tests.exists():
            profile = "full"
        elif tools.is_symlink() or tools.exists():
            profile = "tools"
        else:
            profile = "basic"

    required = set(PACKAGE_BASIC_FILES)
    if profile in ("tools", "full"):
        required.update(f"tools/{name}" for name in PACKAGE_TOOL_FILES)
    if profile == "full":
        required.update(f"tests/{name}" for name in PACKAGE_TEST_FILES)
    for name in sorted(required):
        path = source / name
        if library.has_link_component(source, path):
            raise ValueError(f"source symlink component forbidden: {name}")
        if not path.is_file():
            raise ValueError(f"required source file missing or not a regular file: {name}")

    verify_notices(source, LICENSE_DIGESTS)
    files = [Path(name) for name in required]
    for section in PACKAGE_ROOTS:
        folder = source / section
        if not folder.is_dir() or library.has_link_component(source, folder):
            raise ValueError(f"source section absent or linked: {section}")
        for path in folder.rglob("*"):
            if library.has_link_component(source, path):
                raise ValueError(f"source symlink is forbidden: {path}")
            if path.is_file():
                files.append(path.relative_to(source))
    return sorted(set(files), key=lambda p: p.as_posix())


def governance_collision(destination):
    """Identify canonical Governance namespaces at the requested installation root.

    Do not scan parent directories: an isolated optional subdirectory is allowed.
    These are positive markers, not a claim to detect every Governance edition.
    """
    found = []
    for relative in ("ideas/library.yaml",
                     "src/governance_branch/libraries/ideas.py",
                     "governance"):
        if (destination / relative).exists() or (destination / relative).is_symlink():
            found.append(relative)
    idea_schema = destination / "ideas/schema/v1/idea.schema.json"
    if idea_schema.exists() or idea_schema.is_symlink():
        if library.has_link_component(destination, idea_schema):
            found.append("ideas/schema/v1/idea.schema.json (symlink)")
        else:
            try:
                if idea_schema.stat().st_size > library.MAX_RECORD_BYTES:
                    found.append("ideas/schema/v1/idea.schema.json (unrecognized oversized schema)")
                else:
                    spec = json.loads(idea_schema.read_text(encoding="utf-8"))
                    if isinstance(spec, dict) and (
                        "uid" in spec.get("required", []) or
                        "uid" in spec.get("properties", {}) or
                        "$defs" in spec or "$ref" in spec):
                        found.append("ideas/schema/v1/idea.schema.json (Governance schema signature)")
            except (OSError, ValueError, TypeError, RecursionError):
                found.append("ideas/schema/v1/idea.schema.json (unreadable schema)")
    return sorted(set(found))


def plan(source, destination, profile="auto"):
    source = Path(source).absolute()
    destination = Path(destination).absolute()
    if source == destination:
        raise ValueError("source and host destination may not be the same")
    if library.has_link_component(source, source):
        raise ValueError("source root symlink")
    # Check ancestors first: exists() can hide ENOTDIR for a missing child.
    for parent in reversed(destination.parents):
        if (parent.exists() or parent.is_symlink()) and not parent.is_dir():
            raise ValueError(f"host destination ancestor is not a directory: {parent}")
    if destination.is_symlink() or (destination.exists() and not destination.is_dir()):
        raise ValueError("host destination is not a safe directory")
    if not destination.exists():
        # Parent path cannot be treated as an authorized installation.
        return {"status": "NEW_DESTINATION", "writes": False,
                "entries": [{"path": p.as_posix(), "action": "ADD"}
                            for p in candidates(source, profile)]}
    if library.has_link_component(destination, destination):
        raise ValueError("host root symlink")
    collision = governance_collision(destination)
    if collision:
        # Deliberately no upgrade file actions: this is a hard stop.
        return {"status": "NAMESPACE_COLLISION", "writes": False,
                "entries": [], "markers": collision}
    entries = []
    for relative in candidates(source, profile):
        target = destination / relative
        # Walk from the selected host root before inspecting the leaf. A file
        # at an intermediate component can make the leaf appear merely absent.
        current = destination
        for part in relative.parts[:-1]:
            current = current / part
            if current.is_symlink():
                raise ValueError(f"host path symlink: {relative}")
            if current.exists() and not current.is_dir():
                raise ValueError(f"host path ancestor is not a directory: {current}")
        if library.has_link_component(destination, target):
            raise ValueError(f"host path symlink: {relative}")
        if target.is_dir():
            entries.append({"path": relative.as_posix(), "action": "CONFLICT_DIRECTORY"})
        elif target.is_file():
            # Do not interpret canonical host data or user documentation as upstream-managed.
            if "records" in relative.parts or relative.name == "INDEX.md":
                action = "KEEP_HOST"
            elif target.read_bytes() == (source / relative).read_bytes():
                action = "SAME"
            else:
                action = "REVIEW_LOCAL_DIFFERENCE"
            entries.append({"path": relative.as_posix(), "action": action})
        else:
            entries.append({"path": relative.as_posix(), "action": "ADD"})
    return {"status": "EXISTING_DESTINATION", "writes": False, "entries": entries}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path, help="chosen host library directory")
    parser.add_argument("--source", type=Path, default=library.ROOT)
    parser.add_argument("--profile", choices=PROFILES, default="auto",
                        help="source copy profile (default: detect optional groups)")
    args = parser.parse_args(argv)
    try:
        result = plan(args.source, args.destination, args.profile)
    except (ValueError, OSError) as exc:
        print(json.dumps({"status": "BLOCKED", "writes": False, "error": str(exc)}))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["status"] == "NAMESPACE_COLLISION":
        return 2
    return 1 if any(e["action"] in ("REVIEW_LOCAL_DIFFERENCE", "CONFLICT_DIRECTORY")
                    for e in result["entries"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
