# Provenistem

Provenistem is a portable Ideas & Features tracker. Give each idea or feature a
stable ID, link features to the ideas that led to them, and record implementation
and testing progress alongside links to the original evidence.

This is the standalone development repository. Its portable starter begins with
empty catalogs and synthetic examples. Each adopter keeps its own records,
evidence, and approvals in its repository.

## Versions

- [v0.0.2](https://github.com/vixttha/Provenistem/tree/v0.0.2) — current standalone baseline.
- [v0.0.1](https://github.com/vixttha/Provenistem/tree/v0.0.1) — historical starter.

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

The initial import preserves the portable source files and the upstream MIT
notice. The previous private package release remains historical. New release
claims belong to this repository's own tags and validation evidence.

Planned work includes separate, tested branch-first adoption walkthroughs for
humans and agents, and a read-only project map generated from a pinned catalog.
Each walkthrough should show the selected source revision, the destination and
its collision checks, and how the adopter reviews the result. Generated maps and
other outputs follow the adopter's own publication policy.
