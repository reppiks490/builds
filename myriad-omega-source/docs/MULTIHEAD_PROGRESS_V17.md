# MYRIAD Ω — cross-head continuation checkpoint (2026-11-23)

## Published branch and PR state (verified GitHub)

- HEAD B latest `459d50417e667403682b7913c69e499ac11803bf`, draft PR [#5](https://github.com/reppiks490/builds/pull/5).
- HEAD C latest `53487814dec90e79a77fcbc389bae30a0ada0db8`, draft PR [#6](https://github.com/reppiks490/builds/pull/6).
- HEAD A coordination review branch remains standalone; the B/C PRs have not been merged.
- HEAD B-only clean-room source: 99 passed, 3 skipped. HEAD C-only clean-room source: 92 passed, 3 skipped.
- Combined unmerged preview bundle: 103 passed, 3 skipped, source-only release check exit 2 BLOCKED.
- v1.7 combined review-only ZIP SHA256 `3562bf5a069059e5161d7a04a2408c051a7bf34ff677a7e14e17bf6d53b93e11`, 140 source items, model weights excluded.
- The original full weight banks remain missing; all ten candidates quarantined.


## Sources and branch protocol

- Repository: `reppiks490/builds`, with standalone source in `myriad-omega-source/`.
- Coordination branch: `agent/myriad-head-a-coordination`. HEAD B: `agent/myriad-head-b-training`. HEAD C: `agent/myriad-head-c-runtime`.
- Ownership is enforced by `myriad-omega-source/coordination/ownership.json` with a Git-path checker; preserve exact source SHAs and independently verify before any merge.
- Original MYRIAD v1.5 baseline HEAD is `4b4db95f67639e1306297ec32f677a2b96da80ab`, except HEAD B v1.6 bank integration advanced to `ba53dce98d516129d599bb20dd4b650c5cc751cd` as draft PR #5.

## HEAD B — new independent stress evidence

- New read-only `training/candidate_stress_eval.py` verifies original candidate receipts, original agent and ability bank digests and computes paired synthetic normal/shifted/missing/noisy scores. The offline verifier reruns the experiment and detects tampering; no keys or network.
- On *ten saved candidate weights from the actual historical archive*, improvements vs own source: 10/10 normal, 10/10 missing, 10/10 noise, 8/10 distribution shift. Thus two fail the stronger shifted test. All 10 remain quarantined.
- `training/REAL_10_CANDIDATE_STRESS_REPORT.json` stores real calculated synthetic scores and source hashes; `training/CANDIDATE_STRESS_EVIDENCE.md` records provenance and reproduction. Synthetic regression is **not** a certification of general intelligence, financial edge or 10M real-world abilities.
- HEAD B clean extracted baseline + changes: 99 pytest passes and three skips. `integration_guard.py --require-ready` exit 2 BLOCKED.

## HEAD C — provider security and crash-cost ceilings

- New request limits: maximum 128KB for canonical message list, at most 16 roles/messages, valid text content only; maximum 180KB serialized payload through the actual `ModelGateway._http` transport. Refuses malformed/binary/media payload; model adapter still supports text-only workflows.
- Non-text or blank return values consume the already durable quota and fail instead of silently recording success.
- Added concurrent process test: eight OS subprocesses targeting ONE SQLite quota with a three-call limit; exactly 3 were reserved and 5 blocked. Existing per-thread and restart tests remain green.
- HEAD C clean extracted v1.5 baseline + changes: 92 pytest passes, three skips. `integration_guard.py --require-ready` exit 2 BLOCKED. No external model called; test provider is a local fixture.

## HEAD A — review and release lock

- Both heads must publish separate commits/PRs with source SHA, files changed and exact tests. HEAD A must review and rerun tests on proposed combination before merging within standalone MYRIAD. Merge approvals do NOT imply UMBRA or ICARUS integration authority.
- Source-only gate remains BLOCKED 1/13; missing full historical 8.22GB/640MB bank ledgers, no five real model connections, no validated real-world skills/trading, no sustained user laptop deployment.
- `reppiks490/umbra-sovereign-worlds` and `reppiks490/Icarus` OMNIGENESIS draft PR #503 remain off-limits until completion, final independent 13/13 gate review and explicit owner approval.
- No automatic background work or Codex-based scheduled tasks are authorized.