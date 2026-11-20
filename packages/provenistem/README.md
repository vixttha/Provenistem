# Idea + Feature Library — v0.0.1

**Status: historical Provenistem v0.0.1 template.**

This branch contains exactly two portable record libraries:

- [Ideas](ideas/README.md): possibilities, pros/cons, reasons, exploration, and human decisions.
- [Features](features/README.md): stable capability identities, implementation status, scoped evidence, and references to ideas.

A human can use the files directly in GitHub. An LLM can read and suggest edits by following [the agent guide](LIBRARY-AGENT-GUIDE.md). No plugin, Governance installation, cloud service, runner, Python, or local environment is required to *use the records*.

**Starts empty.** `ideas/records/` and `features/records/` intentionally contain no project-specific ideas or features. Example documents in `templates/` are examples only, never canonical records.

## Quick use (GitHub website only)

1. Copy `ideas/`, `features/`, and optionally `templates/` and `LIBRARY-AGENT-GUIDE.md` into your project's repository, avoiding overwriting any existing paths. See [adoption instructions](docs/ADOPTION.md).
2. For a new idea, copy [the example](templates/idea.example.json) into `ideas/records/IDEA-000001.json`, edit its ID, title, and facts. For a new feature, use [the feature example](templates/feature.example.json) at `features/records/FEAT-000001.json`. Use the next unused ID, never recycle an ID.
3. Link features to existing ideas by `idea_ids`; keep decisions, implementation, tests, and release claims separate.
4. Edit or regenerate `INDEX.md` as a **read-only view** of records; records always prevail if an index becomes stale. An optional standard-library-only Python helper can validate and generate indexes, but is *not required*.

Run optional checks when Python happens to be available: `python tools/library.py check`, `python tools/library.py build`, `python -m unittest discover -s tests -v`. Copy `tools/` and `tests/` if those helpers are wanted.

## One-way Governance isolation

[The one-way boundary contract](docs/ONE-WAY-BOUNDARY.md) prohibits a Governance-Branch dependency on this side template, upstream registration, automatic synchronization, and overwriting Governance-owned `ideas/` or `features/` paths. The template may know the concept of Governance but cannot make Governance know it exists.

## Authority and trust

An idea is not approval to implement. A feature record is not permission to run a tool, proof of test success, or evidence of release. This library never supersedes project owner decisions, `AGENTS.md`, code owners, protected branches, official release records or external acceptance gates.

Only an actual project's release authority can assert shipped versions. The template's `release_membership` field must stay `NOT_ASSERTED`. Evidence references and SHAs are *claims to independently check*, not authenticated receipts.

## Read next

- [Library agent guide](LIBRARY-AGENT-GUIDE.md)
- [Lifecycle and state meanings](docs/LIFECYCLE.md)
- [Zero-install adoption](docs/ADOPTION.md)
- [Isolation / threat boundaries](docs/ISOLATION.md)
- [Provenance and source separation](docs/PROVENANCE.md)

Template version: `0.0.1`. This is **not** the version of any adopting project's product.
