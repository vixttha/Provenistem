# CI lifecycle integrity (v0.0.2.8 candidate)

Owner-approved design: historical licensing verification is independently reproducible and runs only on explicit request. No license terms, portable package files, historical evidence or adopter state change here. The original acceptance is [issue #8](https://github.com/vixttha/Provenistem/issues/8#issuecomment-7229567373).

## Historical lane

From Actions on the default branch, select **Historical licensing replay v0.0.2.7**, then **Run workflow**. The workflow must be on the default branch to expose its manual entry point. Alternatively, a user with suitable repository permissions may run:
`gh workflow run licensing-candidate-review.yml --ref main`.

The dispatched workflow checks out only `ce5f2d77c3f553d702718e27de82cd9e3ea3a178` (tree `b3631b8cade61a802d0c0d8c9180b141e5a07c11`). It executes the original verifier, temporary dirty-baseline rejection, 97 historical tests and 97 copied-package tests per platform. It records the dispatch SHA separately from the replay SHA. No push, PR, schedule or chained workflow triggers historical replay. A manually requested qualification of this migration may use an isolated temporary proof workflow, not an enduring automatic trigger.

For independent replay on a compatible authorized Git/Python 3.12 environment, clone the public repository into a disposable directory and checkout the full historical SHA. Set PYTHONDONTWRITEBYTECODE=1 and PYTHONUTF8=1. Run from that checkout:

```sh
git rev-parse HEAD
python licensing/v0.0.2.7/verify_operative.py
cd packages/provenistem
python -m unittest discover -s tests -v
python ../../audit/verify_adoption_copy.py
```

The original workflow at the frozen SHA also contains the dirty-baseline negative test; reproduce it only in a disposable checkout, and restore the bytes before checking cleanliness. The frozen verifier fetches exact recorded Git commits; missing objects or unavailable tools fail replay. Hosted runner images and Python patch versions may change; record the actual runtime, runner, source SHA, run and attempt. This is source-reproducible evidence, not proof of a bit-identical execution environment or legal title.

## Active lane

`validate.yml` runs on pushes to main, pull requests to main and manual current validation. Before portable imports it runs `python audit/verify_current_licensing.py` and the independent lifecycle tests, then the existing blank, regression and copied/populated package checks. The current verifier checks Git modes/blob identity and working-tree bytes for the two MIT notices, Strict text, portable notice and restricted module, plus the frozen archive tree and working inventory. It does not invoke the historical verifier or fix the ordinary package file count. Changes to ordinary files are validated by the current product tests.

The protected inventory is `ci-lifecycle-policy.json`, anchored to v0.0.2.7. Any modification of this policy, verifier, workflow, protected notice/module or historical material requires independent comparison with the last accepted policy and explicit owner review; do not simply repin to make CI green. A candidate can modify its own checks, so CI alone is not an authorization mechanism. No release, distribution, commercial clearance or new restricted scope follows from passing CI. New ordinary files are not automatically restricted. Preserve historical MIT rights and all previous receipts.

## Qualification

Issue [#32](https://github.com/vixttha/Provenistem/issues/32) records regression-first proof and exact candidate evidence. Before merge verify the byte-identical portable tree and historical archive, unchanged main/catalog/VIB and snapshots, and exact candidate checks and independent review. After separately authorized merge, check actual main public CI, ensure the historical lane did not automatically run, explicitly dispatch the manual workflow, verify its historical source and both runner results, then create the version snapshot. No v0.0.3 or release authorization.
