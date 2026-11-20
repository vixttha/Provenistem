# Provenistem project catalog

This branch uses the Provenistem v0.0.2 starter to track the Provenistem project itself. Project records live in this catalog. The starter package has its own empty record directories.

[Adopter bug audit and dogfooding milestone](ADOPTER-BUG-AUDIT.md) · [Rollout to reusable template branches](BRANCH-TEMPLATE-ROLLOUT.md)

## Ideas

| Record | Idea |
| --- | --- |
| [IDEA-000001](ideas/records/IDEA-000001.json) | Keep the project catalog on a dedicated branch |
| [IDEA-000002](ideas/records/IDEA-000002.json) | Design a human branch-first install |
| [IDEA-000003](ideas/records/IDEA-000003.json) | Design an agent branch-first install |
| [IDEA-000004](ideas/records/IDEA-000004.json) | Publish an explicit portable copy manifest |
| [IDEA-000005](ideas/records/IDEA-000005.json) | Generate a project map from canonical records |
| [IDEA-000006](ideas/records/IDEA-000006.json) | Link project records to exact code and tests |
| [IDEA-000007](ideas/records/IDEA-000007.json) | Pair branch-first adoption with output-only publication |
| [IDEA-000008](ideas/records/IDEA-000008.json) | Make index rows open their records |
| [IDEA-000009](ideas/records/IDEA-000009.json) | Use multiple adopter catalogs for conformance |
| [IDEA-000010](ideas/records/IDEA-000010.json) | Keep external technique catalogs separate |
| [IDEA-000011](ideas/records/IDEA-000011.json) | Reject duplicate JSON fields in canonical records |

## Features

| Record | Capability | Lifecycle |
| --- | --- | --- |
| [FEAT-000001](features/records/FEAT-000001.json) | Structured idea and feature catalogs | verified |
| [FEAT-000002](features/records/FEAT-000002.json) | Offline structural validation | verified |
| [FEAT-000003](features/records/FEAT-000003.json) | Reproducible Markdown indexes | verified |
| [FEAT-000004](features/records/FEAT-000004.json) | Read-only adoption and upgrade preflight | verified |
| [FEAT-000005](features/records/FEAT-000005.json) | Manual starter and record guides | implemented |
| [FEAT-000006](features/records/FEAT-000006.json) | Dedicated version branch snapshots | verified |
| [FEAT-000007](features/records/FEAT-000007.json) | Scoped evidence and delivery status | verified |
| [FEAT-000008](features/records/FEAT-000008.json) | GitHub-web install walkthrough for humans | planned |
| [FEAT-000009](features/records/FEAT-000009.json) | Branch-first install walkthrough for agents | planned |
| [FEAT-000010](features/records/FEAT-000010.json) | Complete portable install manifest | proposed |
| [FEAT-000011](features/records/FEAT-000011.json) | Reusable offline project map | proposed |
| [FEAT-000012](features/records/FEAT-000012.json) | Optional derived-output receipts | proposed |
| [FEAT-000013](features/records/FEAT-000013.json) | Public adopter conformance checks | proposed |
| [FEAT-000014](features/records/FEAT-000014.json) | Clickable generated catalog indexes | proposed |
| [FEAT-000015](features/records/FEAT-000015.json) | Optional Graphify evidence links | proposed |
| [FEAT-000016](features/records/FEAT-000016.json) | Provenistem tracks its own development | verified |

## Audit sources

- [Provenistem v0.0.2 checks](https://github.com/vixttha/Provenistem/actions/runs/44687183121) exercise the portable starter. The adoption planner is a read-only preview and its file listing omits the starter README and license.
- [README-HQ's pinned catalog](https://github.com/vixttha/README-HQ/tree/526f07a0775fe515960d413d2ec0681eef30e6fa) shows project-owned records on a dedicated branch and references to an external technique library.
- [Veraphify's pinned map run](https://github.com/vixttha/Veraphify/actions/runs/44687998633) generated and retained the offline map and receipt. The reusable Provenistem baseline still needs its own map implementation and validation.
- [AlderVale's validation run](https://github.com/vixttha/AlderVale-Pact-of-Ten/actions/runs/43731809086) and [BART's pinned Graphify HQ kit](https://github.com/vixttha/Blender-Agent-Refinement-Toolkit/tree/6af3c2025be3f51e02dca4e4502088c526aae6d1/versions/v0.0.8) illustrate how to reference test execution and source anchors separately.

## Update the catalog

Edit the canonical JSON records. Use the v0.0.2 schemas stored with this catalog and keep source and test evidence scoped to the revision and project that produced it. The Veraphify map run is adopter evidence for future upstream work.

From the repository root, regenerate and check the [Ideas index](ideas/INDEX.md) and [Features index](features/INDEX.md).

```sh
python packages/provenistem/tools/library.py build --root catalog
python packages/provenistem/tools/library.py check --root catalog
```
