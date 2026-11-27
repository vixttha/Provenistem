# Six architectural laws

**Decision ID: ENGINEERING-ECOSYSTEM-LAWS-001 — owner approved 2026-11-24.**

Mission: Build a toolkit that gives compatible LLM agents a structured engineering environment, rather than building another AI model.

<!-- engineering-laws:start -->
1. **Independence:** Every tool must remain independently installable, usable, versioned and maintained.
2. **Composability:** Installing additional tools expands the agent's capabilities without creating mandatory dependencies.
3. **Portability:** No mandatory AI provider, model, agent harness or paid execution service.
4. **Persistence:** Project knowledge, decisions, progress and evidence survive the termination of an AI session.
5. **Verification:** Development claims must be supported by reproducible, revision-bound evidence.
6. **Owner authority:** The human retains control over scope, architectural decisions, integration and releases.
<!-- engineering-laws:end -->

Each product keeps its existing responsibility, canonical records, release history and standalone installation. Optional references may cross product boundaries; references confer no write or release authority. No seventh mandatory coordination tool, shared backend, registration service or runtime dependency is permitted. A compatible agent may discover installed tools through repository navigation or an owner-supplied branch reference; missing tools must not prevent standalone operation. No automatic installation, synchronization or merge of template branches. Existing adopter data and immutable evidence must be preserved. No paid execution is required; use standard GitHub public runners for this project's hosted validation. This contract does not enable branch protection or hard enforcement.

For each candidate, check standalone usage with other ecosystem tools absent, optional coexistence without authority transfer, provider-neutral instructions, exact-revision recovery, reproducible evidence and explicit owner decisions. A documentation check establishes wording parity only; product behavior requires its own tests. Report unsupported capabilities and unverified claims. Change these laws only by explicit owner approval. No release or cross-repository installation is authorized by this decision alone.

## Decision reconciliation — v0.0.2.6 candidate

The six laws above are the unchanged owner-approved decision in [issue #5](https://github.com/vixttha/Provenistem/issues/5), first integrated by [PR #6](https://github.com/vixttha/Provenistem/pull/6) at `44d7a51a0138db6b54cc30a496c331363f0306f9`. This crosswalk clarifies their application; it is not a new law, release, or scope approval.

| Law | Existing authority and application | Verification boundary |
| --- | --- | --- |
| Independence | [Scope lock](packages/provenistem/docs/PRODUCT-SCOPE-LOCK.md) (PROVENISTEM-SCOPE-2026-11-12) and [optional integration contract](packages/provenistem/docs/PORTABILITY-AND-MODULE-CONTRACT.md) (GB-PROVENISTEM-OPTIONAL-RELATIONSHIP-2026-11-12). Core remains a standalone Ideas & Features tracker; adapter remains NOT_IMPLEMENTED. | Standalone source and copied starter tests, not qualification of a real host adapter. |
| Composability | [One-way boundary](packages/provenistem/docs/ONE-WAY-BOUNDARY.md) and [capability discovery](README.md#agent-capability-discovery--v1) ([issue #7](https://github.com/vixttha/Provenistem/issues/7)). Optional discovery and references do not install, synchronize, grant authority or create duplicate masters. | Read-only preflight and non-interference regressions, not proof of every host configuration. |
| Portability | [Adoption guide](packages/provenistem/docs/ADOPTION.md): manual record use needs no Python, runner, AI provider or companion tool; optional helpers use the standard library. | Free public Ubuntu/Windows validation; no claim about all agent harnesses or offline networks. |
| Persistence | Canonical records are project-local JSON, indexes are derived, and version snapshots and evidence retain exact revisions. The project catalog is separate from the blank portable source. | Copied starter and populated byte preservation, not automatic backups or multi-file atomic recovery. |
| Verification | [Lifecycle](packages/provenistem/docs/LIFECYCLE.md) separates implementation, testing and release status; [provenance](packages/provenistem/docs/PROVENANCE.md) separates source and host evidence. [Veraphify reconciliation #22](https://github.com/vixttha/Provenistem/issues/22) provides optional, pinned maps and replay receipts. | Exact commit tests and independent replay are scoped evidence; references, policy parity and graph edges do not themselves authenticate claims. |
| Owner authority | [Agent guide](packages/provenistem/LIBRARY-AGENT-GUIDE.md) and scope lock require explicit owner decisions for authorized writes, integration and releases. | Documentation and tests do not install branch protection, an authorization service or a governance engine. |

### Precedence and retained decisions

- The November 12 scope lock controls product purpose. Its narrower mission supersedes earlier broader descriptions. The optional relationship and one-way safeguards remain in force where compatible; a host-owned adapter is a future option, not a shipped dependency. The November 24 six laws apply to how the product is built and used, without granting extra product powers.
- Capability discovery is read-only. Repository presence, an idea-direction decision, a passing test or a feature marked verified is not permission to implement, merge or publish. Unknown access stays unverified. Changes to any locked scope or law require explicit owner approval, not inference from this crosswalk.
- [Project catalog at 8c9647d](https://github.com/vixttha/Provenistem/tree/8c9647d1cd168642ba4dd3b2b5ec3045634d1bcb/catalog): IDEA-000001, IDEA-000003 and IDEA-000007 record separate catalog/adoption/output ideas; IDEA-000010 keeps external technique catalogs separate. FEAT-000006 and FEAT-000007 record version snapshots and scoped evidence; FEAT-000015 remains proposed. These are historical catalog records, not new decisions or acceptance. Their IDs, status and source receipts are preserved. Historical audit wording, including the old incomplete-copy report, is not a claim about current main.
- Product source baseline for this checkpoint is [v0.0.2.4](https://github.com/vixttha/Provenistem/tree/9f321b6142d77112f3f32b9d0d31e748a47a1915); [v0.0.2](https://github.com/vixttha/Provenistem/tree/e36fcd6d12633395e9b573228c0797ade9e775b0) is a historical branch snapshot, distinct from the historical private tag. The v0.0.2.5 checkpoint was workspace-only at [Veraphify merge](https://github.com/vixttha/Provenistem/tree/45d0d7a7bf55650d8f71cbfbf1fec656c99c319e), not a product release. No release is inferred from version numbers or a Git branch.
- The installed VIB workspace at [962aa226](https://github.com/vixttha/Provenistem/tree/962aa2260c97adebfe9d8a5921390ff89779c29a) has an unreconciled version baseline. Existing cooperative receipts remain evidence; do not fabricate transactions or reuse a historical version number. VIB remains optional, and formal numbering reconciliation is separate from #5.
- [Licensing decision #8](https://github.com/vixttha/Provenistem/issues/8) remains separate and deferred. This change neither changes licenses nor authorizes redistribution beyond existing terms.

### Qualification

The public engineering-law check compares the exact six-law block in the source and portable entry points on Ubuntu and Windows. Portable tests also check the explicit links to earlier decisions, unchanged authority limits and existing standalone behavior; the copied-starter and populated-adopter suites exercise the isolated portable package. These checks establish wording parity, documentation consistency and the behaviors tested, not universal enforcement, independent external attestation or release authority. Final acceptance still requires exact-revision review, owner integration authorization and post-merge evidence.
