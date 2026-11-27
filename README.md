# Veraphify for Provenistem

This branch holds Provenistem's Veraphify workspace. Its Graphify manifests
link selected capabilities to documentation, implementation, and test
definitions at the exact version commits.

| Provenistem version | Source commit | Feature map | Manifest |
| --- | --- | --- | --- |
| v0.0.1 | [5a689fb](https://github.com/vixttha/Provenistem/tree/5a689fbe3d6a6b26d77709889e28e1e02de363fc) | [Graph](graphs/v0.0.1/graph.json) · [Receipt](graphs/v0.0.1/receipt.json) | [Historical starter](manifests/v0.0.1.json) |
| v0.0.2 | [e36fcd6](https://github.com/vixttha/Provenistem/tree/e36fcd6d12633395e9b573228c0797ade9e775b0) | [Graph](graphs/v0.0.2/graph.json) · [Receipt](graphs/v0.0.2/receipt.json) | [Portable tracker](manifests/v0.0.2.json) |
| v0.0.2.1 | [0bacde8](https://github.com/vixttha/Provenistem/tree/0bacde8bcc8311fd3c08be371b4e76e524f35cd7) | [Graph](graphs/v0.0.2.1/graph.json) · [Receipt](graphs/v0.0.2.1/receipt.json) | [Manifest](manifests/v0.0.2.1.json) |
| v0.0.2.2 | [bc7c028](https://github.com/vixttha/Provenistem/tree/bc7c0287ea62a72e6c5cc654fca61d1ac0c0de34) | [Graph](graphs/v0.0.2.2/graph.json) · [Receipt](graphs/v0.0.2.2/receipt.json) | [Manifest](manifests/v0.0.2.2.json) |
| v0.0.2.3 | [5e1a60b](https://github.com/vixttha/Provenistem/tree/5e1a60b99dc64b8618dff1de3acb25a89490fc7d) | [Graph](graphs/v0.0.2.3/graph.json) · [Receipt](graphs/v0.0.2.3/receipt.json) | [Manifest](manifests/v0.0.2.3.json) |
| v0.0.2.4 | [9f321b6](https://github.com/vixttha/Provenistem/tree/9f321b6142d77112f3f32b9d0d31e748a47a1915) | [Graph](graphs/v0.0.2.4/graph.json) · [Receipt](graphs/v0.0.2.4/receipt.json) | [Manifest](manifests/v0.0.2.4.json) |

The [public GitHub workflow](.github/workflows/veraphify.yml) builds each map
twice, verifies it with Graphify MCP, imports it into Veraphify, and checks the
exact source and digest. It looks up the index generator in each version to
prove that each archive resolves its own implementation line. The run artifact
includes the graphs, receipts, archives, lookup results, and SHA-256 sums.

## Public runner evidence

[GitHub Actions run 44975292608, attempt 1](https://github.com/vixttha/Provenistem/actions/runs/44975292608/attempts/1)
built the two graphs on public Ubuntu at workspace commit
`82df517172d1a8b05e4b3f16dbefd346f7f25934`. The four checked-in graph and
receipt files match the SHA-256 values recorded by that job.

[Archive artifact 14735525837](https://github.com/vixttha/Provenistem/actions/runs/44975292608/artifacts/14735525837)
includes the two Veraphify archives and lookup results. GitHub recorded ZIP
SHA-256 `1e1d49666859282dfcced58e4ad98f249a4754435e506d7aea3669a24a6b108d`.
The repeatable workflow can recreate those archive entries from their source pins.

## Sources

- [Veraphify v0.0.9 preview](https://github.com/vixttha/Veraphify/tree/ed5650085e33cf142a37de695757a4df999a7cf3)
  and the [tested standalone CLI bundle](https://github.com/vixttha/Version-Issues-Hub/tree/6c5d22c1f11a4952d4a79d800b946f4f8d76d778).
  The preview CLI and its runtime files are copied from that bundle.
- [Pinned Graphify producer](https://github.com/vixttha/Blender-Agent-Refinement-Toolkit/tree/6af3c2025be3f51e02dca4e4502088c526aae6d1/versions/v0.0.8)
  with its hash-locked dependencies. Graph edges to tests identify test definitions.
- [Branch-local Provenistem starter](provenistem/INSTALLATION.md) and the
  [project's own catalog](https://github.com/vixttha/Provenistem/blob/Provenistem/catalog/README.md).

Veraphify's [MIT license](LICENSE) and the imported Lydite [license](lib/LYDITE-LICENSE)
apply to their respective files.

## Issue #22 — canonical workspace migration

The lowercase `veraphify` branch is preserved at its historical commit
`574baa77833e00ef1b23b7b768c7abdbfece8a2e`. This migration targets the
canonical `Veraphify` branch; it never merges into product main. Use the exact
branch name, especially on case-insensitive filesystems: check out a single
ref rather than fetching both case variants into a local ref namespace.

Forward checkpoint manifests: [v0.0.2.1](manifests/v0.0.2.1.json),
[v0.0.2.2](manifests/v0.0.2.2.json), [v0.0.2.3](manifests/v0.0.2.3.json),
[v0.0.2.4](manifests/v0.0.2.4.json). These are selected source-evidence maps,
not exhaustive code graphs or proof that every mapped test ran; changed-in
anchors locate source, not a chronological diff.

The [durable pins](archive-pins.json) preserve graph, receipt, archive SHA-256,
source revision and index implementation location. Original historical pins
come from [run 44975416836](https://github.com/vixttha/Provenistem/actions/runs/44975416836/attempts/1),
not from the new replay. The producer runs on pinned Linux dependencies; fresh
Ubuntu and Windows jobs replay the generated archive without installing Graphify
or cloning product source. Temporary CI artifact bytes can be reconstructed
from the pinned inputs; replay does not imply indefinite artifact retention.

[Runtime verification](scripts/verify-runtime.py) compares all five local
runtime/license files against the approved upstream and the exact VIB bundle.
The only adaptations are the CLI's relocated inspect-evidence import and
the relocated handoff-profile import. No upstream upgrade or runtime logic
change is included.

Forward map and pin collection: [run 46005296719, attempt 1](https://github.com/vixttha/Provenistem/actions/runs/46005296719/attempts/1), workspace head `604aed43107752fc1a9d96f75a5ddc1824b08038`. All new graph/receipt bytes are checked in; the strict workflow re-derives and compares them, and verifies archive pins in separate Ubuntu and Windows replay jobs. Archive payloads remain regenerable CI outputs, not permanent Git blobs.
