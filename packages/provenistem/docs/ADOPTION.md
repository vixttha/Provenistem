# How any project can adopt v0.0.1

## Zero-install copy
Use GitHub's web UI, Git, or whatever file tooling is already available. Copy the `ideas/` and `features/` folders from this branch into a separate host project, keeping the blank `records/` folders (represented by `.gitkeep`). Copy the `templates/` for quick intake, and optionally the agent guide, `tools/`, `tests/` and documentation.

**Never overwrite** an existing host file or `AGENTS.md`. Stop and reconcile if a directory already exists or an ID conflicts. No account credentials, cloud API, plugin, hosted service, local runner, Python package or new execution environment is necessary for record storage or browsing.

## Host-local records
Each adopter starts at `IDEA-000001` / `FEAT-000001` in its own repository, with its own evidence, metadata and approvals. IDs are scoped **to the host repository**, not globally. Host paths are relative; do not link to another project's private data or inherit its record status.

Examples are stored in `templates/`, never in `*/records/`. Remove example-only placeholders before declaring a record meaningful. Update the two indexes manually or with the optional tool.

## Optional validation
If Python 3 is already available, the dependency-free `tools/library.py` helper offers `check` and `build` actions; `tests/` provides offline regressions. They are not installed by default, are not a runtime dependency, and do not grant authority.

## Scope of this branch
This branch preserves the original standalone template. Adopters own the resulting catalog and its maintenance. No auto-merge, product release, CI provisioning, or policy mutation is part of adoption.
