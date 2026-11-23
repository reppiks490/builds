# MYRIAD Ω — Exact engineering verification and takeover state

**Date:** 2026-11-23, America/Chicago. **Scope:** v1.3 standalone recovery snapshot; no production merge or live deployment.

## What was actually changed this session

- Continued the isolated source from locally mounted `myriad_omega_v12` to `myriad_omega_v13`.
- Hardened `evidence_vault.py`: reject nonexistent workflows and mismatched agent ownership (100 core agents per workflow), preventing cross-workflow identity misattribution.
- Hardened `training/transfer_adaptation.py`: measure synthetic holdout loss using the *exact FP16 quantized candidate weights* that were written to disk; reject orphan `.fp16` files, stalled `.pending` files, mismatched report filenames/IDs, nonfinite metrics, forged `synthetic_gate_passed`, unauthorized automatic promotion; atomic JSON metadata write with fsync and rename.
- Added `tests/test_v13_hardening.py`, `tests/test_source_snapshot.py`, `tools/snapshot_source.py`, and detailed standalone takeover documentation.
- Repaired `tools/package_source.py`'s legacy assumption that every compact snapshot contains the separately excluded 736 KB forensic row-digest ledger. It now requires an explicit verified snapshot manifest declaring that omission. This fix was prompted by a **real clean-room test failure**; it was not hidden.
- Added a self-contained `RESTORE_MYRIAD.py` utility for GitHub source reconstruction and byte-level manifest verification, including tar path validation. It does not execute recovered source or include model weights.

## Tests and evidence, exactly

| Test | Result | Interpretation |
| --- | --- | --- |
| `python -m pytest -q` in v1.3 workspace | 70 passed | Includes tests that can use local candidate artifacts |
| Extract published source ZIP into clean directory, `pytest -q` | 67 passed, 3 skipped | The 3 omitted-bank tests skipped because full weights were **not included** |
| Recover bundle from eight original staged parts and rerun tests | 67 passed, 3 skipped | SHA-256 manifests and safe tar traversal verified |
| Clean archive `integration_guard.py --require-ready` | Exit 2; 1/13 gates | Correct: no full weight banks in source ZIP |
| Full local host `integration_guard.py --agent-bank-dir /mnt/data/myriad_omega_v10/training/agentbank --ability-bank-dir /mnt/data/myriad_omega_v10/training/abilitybank --require-ready` | Exit 2; **3/13 gates** | 10,000/10,000 agent-weight row hashes and 200/200 ability group hashes checked; no real-world mastery |
| Synthetic candidate auditor (`training/transfer_candidates`) | 109 valid/109, 0 auto-promoted | Separate synthetic candidates, **not** proof of intelligence |
| GitHub 8-part source upload | All eight parts compared equal to staged base64 text after whitespace normalization | Bundle can be reconstructed from actual GitHub files |

## Snapshot hashes (SHA-256)

- Compressed tar source: `ad0156605cecc734f233dd90456c92afff2cd7ab746a94eb8a95410e130e3e82` (179,888 bytes, 239,852 base64 characters).
- Portable source ZIP: `39f6b86bc89e03211e19068388c50de3ae4c53f4f4c03eab9b3663f35334b96f` (231,687 bytes).
- SHA256 of canonical source-file manifest: `6adc1cfc00509b4d675c608e12cb7215f8ab3971e9c732d6a754c693d0700476`.
- Source archive contains **107** files including the canonical manifest.
- The archive excludes 8.22 GB individual-agent weight bank, 640 MB synthetic ability bank, and 736 KB forensic individual-row digest ledger; their **independent** existence cannot be assumed in the new chat.

## GitHub source of truth

- `reppiks490/builds`, branch `agent/myriad-omega-independent-handoff`.
- `myriad-omega/README_NEXT_CHAT.md` is entry point.
- `myriad-omega/docs/AGENT_HANDOFF.md`, `VERIFICATION_MATRIX.md`, `REPRODUCE_AND_OPERATE.md`, `KNOWN_GAPS.md`, `NEXT_CHAT_PROMPT.md` provide the full operational context.
- `myriad-omega/SOURCE_BUNDLE_INFO.json` and eight numbered `SOURCE_BUNDLE.tar.gz.b64.partNN` files recover full exact text source. `myriad-omega/RESTORE_MYRIAD.py` can perform the verification/extraction. Do not confuse GitHub's archived source with a production deployment.

## Checked live GitHub targets — unchanged

- **UMBRA Ω**: `reppiks490/umbra-sovereign-worlds`, `main` commit `fb5d532785056331174d616820fe19856e331a03` when checked. No changes by this session.
- **OMNIGENESIS**: `reppiks490/Icarus` draft PR #503, branch `agent/omnigenesis-phase-01-foundation`, target `main`; observed head commit `bdf8481ec7de45a6ab4b35f246662febfc24b1b7`, open/draft/unmerged when checked. No changes by this session.
- These are observations at a point in time, not permanent pinned states; ALWAYS refresh before touching any integration branch.

## Remaining blocking gaps

1. Five actual connected inference model endpoints not independently authenticated or evaluated on the user's machine.
2. Original 10k x 411k synthetic policies show high distribution shift error; 109 quarantine candidates improve a synthetic objective but do not certify general intelligence.
3. No independently certified 10M real skills, 1,000-track examinations, profitable trading strategies, or real-world mastery.
4. No production-grade auth, trust boundaries, all-platform load tests, data licenses, cost model, and incident runbook certification.
5. No continuous authorized autonomous execution; no background work should be implied by saving GitHub files.
6. Source and large neural checkpoints are separate. Plan a private, encrypted artifact location for the banks if cross-session portability is required.
7. **Release lock remains BLOCKED — 3/13 gates even with local training bank evidence.** No UMBRA/OMNIGENESIS merging, no live broker orders and no autonomous model promotions.

## Mandatory next-chat start

1. Open GitHub `README_NEXT_CHAT.md` and `docs/NEXT_CHAT_PROMPT.md`, then fetch the complete source archive and verify SHA. Do not ask the user to paste prior context unless actual data is missing.
2. Rerun tests and gate, record fresh exact results.
3. Work on real model connection and independently sourced benchmark tasks—not increasing unsubstantiated counts.
4. Update this GitHub handoff at session end. If proposed changes become ready, prepare a **separate draft review**; do not merge any target repo until the 13 gates plus explicit owner approval.