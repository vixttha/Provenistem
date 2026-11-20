# One-way Boundary — Idea + Feature Library v0.0.1

**Authority scope:** This is a rule for *this optional side template and its adopters*. It does **not** amend, register with, send instructions to, or impose a new requirement on Governance-Branch.

## One-way rule

```
Side template  --may understand the concept of-->  Governance-Branch
Governance-Branch  --must not depend on-->  side template
```

Governance-Branch must remain **agnostic** to the existence, identity, version, location, build process, catalog, and life cycle of this little side template. The dependency direction must never reverse.

1. **No upstream registration:** Do not add this template to Governance's catalog, adoption registry, default discovery, release manifest, bootstrap, CLI, dependencies, or test requirements.
2. **No upstream modification:** Installing or editing this template must never write to, open a PR against, bump a version in, or auto-sync with Governance-Branch's source or Bible.
3. **No runtime dependency:** This template must work without Governance; Governance must work when the template does not exist. No API calls, callbacks, environment requirements, imports, workflow triggers, or monitoring hooks connecting either product.
4. **No shared authority:** The side template cannot grant permissions, approve a mission, verify independent evidence, advance Governance gates, or claim release membership.
5. **No imported project records:** Every adopter owns its own identities and records. Start with an empty catalog and keep each project's decisions with that project.
6. **No path collisions:** Refuse to replace existing `ideas/`, `features/`, `tools/`, `AGENTS.md`, or Governance-managed files. A repository with Governance installed must choose a separately isolated optional location, with an explicit host-owned migration plan, rather than automatically merging two canonical libraries.
7. **Names are not contracts:** `IDEA-xxxxxx` and `FEAT-xxxxxx` are project-local identifiers, not proof of a shared schema or a global ID registry. Governance's YAML/UUIDv7 idea records and this JSON template are **not** automatically compatible.
8. **No inferred upstream state:** The template may cite Governance as design inspiration, but it must not track Governance's current version, progress, policy, release, or active missions as a prerequisite.
9. **No automatic synchronization:** Two template branches or project copies may evolve independently. Any schema change requires explicit local review, opt-in transfer and field-by-field verification. No cross-repo mirroring.
10. **Optional removal:** Deleting the entire side template must leave the host product and Governance operational, except for user-authored links explicitly referencing removed records.

### What the little piece *may* do

It may be copied into a project, help a person or LLM review that project's own Ideas and Features, and document that it is a **small optional piece of a larger developer ecosystem**. Awareness is explanatory, not executable or authoritative.

### Conflict response

When Governance and the side template occupy the same candidate directory, **STOP** and report `NAMESPACE_COLLISION`. Do not replace or merge their catalogs. When a source revision or compatibility contract is unknown, report `UNVERIFIED` rather than guessing.

### Verification limit

Static checks in `tests/test_one_way_boundary.py` detect obvious forbidden imports, activation files and non-blank template records. They are useful regression guards, not immutable GitHub branch protections, continuous monitoring, full code security analysis or a promise about all future commits. Production-wide enforcement requires independent reviews and write-authority restrictions.
