# Veraphify for Provenistem

This branch holds Provenistem's Veraphify workspace. Its Graphify manifests
link selected capabilities to documentation, implementation, and test
definitions at the exact version commits.

| Provenistem version | Source commit | Manifest |
| --- | --- | --- |
| v0.0.1 | [5a689fb](https://github.com/vixttha/Provenistem/tree/5a689fbe3d6a6b26d77709889e28e1e02de363fc) | [Historical starter](manifests/v0.0.1.json) |
| v0.0.2 | [e36fcd6](https://github.com/vixttha/Provenistem/tree/e36fcd6d12633395e9b573228c0797ade9e775b0) | [Portable tracker](manifests/v0.0.2.json) |

The [public GitHub workflow](.github/workflows/veraphify.yml) builds each map
twice, verifies it with Graphify MCP, imports it into Veraphify, and checks the
exact source and digest. It looks up the index generator in both versions to
prove that each archive resolves its own implementation line. The run artifact
includes the graphs, receipts, archives, lookup results, and SHA-256 sums.

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
