# Provenistem

Provenistem is a portable Ideas & Features tracker. Give each idea or feature a
stable ID, link features to the ideas that led to them, and record implementation
and testing progress alongside links to the original evidence.

This is the standalone development repository. Its portable starter begins with
empty catalogs and synthetic examples. Each adopter keeps its own records,
evidence, and approvals in its repository.

## Project catalog

Open the [Ideas & Features catalog](https://github.com/vixttha/Provenistem/blob/Provenistem/catalog/README.md) for the current project inventory, proposals, and evidence.

## Versions

- [v0.0.2.4](https://github.com/vixttha/Provenistem/tree/v0.0.2.4) — accepted product snapshot preceding the architectural reconciliation.
- [v0.0.2](https://github.com/vixttha/Provenistem/tree/v0.0.2) — historical standalone baseline.
- [v0.0.1](https://github.com/vixttha/Provenistem/tree/v0.0.1) — historical starter.

The v0.0.2.5 checkpoint reconciled the [Veraphify workspace](https://github.com/vixttha/Provenistem/tree/45d0d7a7bf55650d8f71cbfbf1fec656c99c319e), without changing product main or publishing a product release. See the [decision reconciliation](ENGINEERING-LAWS.md#decision-reconciliation--v0026-candidate) for the scope and authority boundaries.

## Start here

- [Portable package](packages/provenistem/README.md) — record structure, schemas,
  examples, and optional validation.
- [Adoption guide](packages/provenistem/docs/ADOPTION.md) — copy the starter into
  an isolated destination and inspect upgrades for file conflicts.
- [Agent guide](packages/provenistem/LIBRARY-AGENT-GUIDE.md) — read and edit
  project-local catalogs within the host's instructions.
- [Product scope](packages/provenistem/docs/PRODUCT-SCOPE-LOCK.md) — the tracker
  covers ideas, features, their relationships, and their progress.

GitHub's web interface is sufficient to browse and edit records. The optional
Python tools validate records, generate indexes, and preview adoption changes.
Run them from the portable package directory:

```sh
python tools/library.py check --expect-empty
python -m unittest discover -s tests -v
```

## Development

[CI lifecycle and historical replay](audit/CI-LIFECYCLE.md) distinguish frozen licensing evidence from current package validation.

The initial import preserves the portable source files and the upstream MIT
notice. The previous private package release remains historical. New release
claims belong to this repository's own tags and validation evidence.

Planned work includes separate, tested branch-first adoption walkthroughs for
humans and agents, and a read-only project map generated from a pinned catalog.
Each walkthrough should show the selected source revision, the destination and
its collision checks, and how the adopter reviews the result. Generated maps and
other outputs follow the adopter's own publication policy.

## Prospective license policy

The root and portable MIT notices remain unchanged. The [package scope and installation notice](packages/provenistem/PROVENISTEM-NOTICE.md) schedules only one new optional module for [PolyForm Strict 1.0.0](packages/provenistem/PROVENISTEM-LICENSE.md) in an owner-authorized distribution. All prior MIT grants and all other current package code and documentation remain MIT-covered to the extent of rights held; the standard license text retains upstream terms. No review branch is an authorized release. See the [exact licensing scope](licensing/v0.0.2.7/operative-scope.json) and the [bounded provenance record](licensing/v0.0.2.7/README.md).

## Engineering ecosystem

[Owner-approved six architectural laws](ENGINEERING-LAWS.md) apply to this product. Standalone operation and owner authority remain unchanged. The product has no mandatory coordination-tool dependency.

## Agent capability discovery — v1

<!-- agent-capability:v1
{"schema_version":1,"id":"provenistem","branch":"Provenistem","entrypoint":"LIBRARY-AGENT-GUIDE.md","scope":"Ideas and features; owner decisions and progress","required_ecosystem_tools":[],"authority":"owner","discovery":"read-only","versioning":"independent"}
-->

A compatible agent may enumerate the target repository's branch refs, resolve this branch to a commit, and read its entry point at that exact commit. Read-only discovery confers no execution, write, integration or release authority. If this branch or marker is absent, the tool is absent or legacy/unverified; continue independently. Check the target's own instructions and owner scope before any action. The marker describes a capability, not a required registry or package version.

Installation convention: human or agent selects a reviewed exact source SHA, checks the dedicated target branch and collisions, follows this product's own installation guide, and records source/target SHA and preserved product state. Never merge a template workspace wholesale into product source. Existing installations require explicit reviewed upgrades; preserve local records and prior receipts. Optional evidence links do not authorize writes. No mandatory coordinator or other ecosystem tool.
