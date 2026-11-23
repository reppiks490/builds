# MYRIAD Ω — Agent + Ability Weight Bank Integration (HEAD B)

## Exact engineering status

This module integrates **existing** independent FP16 411,000-weight neural agent vectors and **existing** independent FP16 32-weight ability adapter vectors in an auditable, disk-backed training route. It also allows limited *new* synthetic training when the original full checkpoints are unavailable.

**IMPORTANT:** The historic full agent weight bank (~8.22 GB), full 10M adapter bank (~640 MB + bitmaps), and their SQLite ledgers were **not available in this execution session or the persistent project file library**. Only the previously exported ten-agent sample `MYRIAD_OMEGA_v1.0_TRAINED_10_AGENT_POLICY_DEMO.zip` (7,427,499 bytes) was present. The full bank must be supplied from the original training host or explicitly regenerated. A directory's declared/virtual size is **not proof** of training.

## Existing full-bank file contracts

**Agent bank** (`--agent-bank-dir`):
- `agent_weights.fp16`: EXACTLY 10,000 x 411,000 x 2 = **8,220,000,000 bytes** in row-major little-endian FP16.
- `weight_ledger.sqlite3`: per-agent status, steps, sha256, training and holdout metrics. This bank is **10,000 small decision policies, not LLMs**.

**Ability bank** (`--ability-bank-dir`):
- `weights.fp16`: EXACTLY 10,000,000 x 32 x 2 = **640,000,000 bytes** in row-major little-endian FP16.
- `status.u8`, `steps.u8`: 10,000,000 bytes each.
- `ability_ledger.sqlite3`: hash ledger of synthetic training batches. Historic full checkpoints use 200 batches x 50,000 abilities; `verify_ability_span` can validate 1,000-ability slices while honoring the original 50,000-row evidence.

**Target agent-to-ability mapping:** AG-00001 => CAP-00000001..CAP-00001000; AG-00002 => CAP-00001001..CAP-00002000; AG-10000 => CAP-09999001..CAP-10000000. Every agent has 1,000 exclusive primary ability adapters under this simple deterministic mapping. This does **not** exhaust MYRIAD's separate 1,500 skill definitions or certify all 10M adapters as functional real-world skills.

## Integration commands — Windows PowerShell, in the MYRIAD source root

Install from `training/requirements.txt` in an isolated environment. Verify CPU storage; memory budget does NOT include 10,000 model instances simultaneously.

1. Attach already-existing FULL checkpoints non-destructively, if you have their exact original files:

```powershell
python -m training.bank_bridge inspect --agent-bank-dir D:\MYRIAD\agentbank --ability-bank-dir D:\MYRIAD\abilitybank --full-audit
```

`--full-audit` streams all reported rows and SHA-256 receipts; it may take time. A missing bank is reported as missing, **not recreated**.

2. If you only have the ten-agent portable sample, explicitly import it. It reserves 8.22 GB of *logical* space but writes ten rows. Ensure your real disk has room for eventual full allocation:

```powershell
python -m training.bank_bridge import-sample --sample .\MYRIAD_OMEGA_v1.0_TRAINED_10_AGENT_POLICY_DEMO.zip --agent-bank-dir D:\MYRIAD\agentbank --approve-write
```

Imported rows are labeled `imported_unverified` because the portable archive lacks original loss-history attestation. Their SHA-256 hashes are verified and weights can be used for fresh learning.

3. Train selected 411k-policy rows with ACTUAL autograd; only fresh local updates can mark them `trained`:

```powershell
python -m training.fleet_trainer --bank-dir D:\MYRIAD\agentbank --start 1 --end 10 --steps 2 --samples 24
```

4. Train/use up to 1,000 ability adapters per agent and generate a **quarantined** joint candidate (at most 100 agents per invocation, for controllable CPU/RAM work):

```powershell
python -m training.run_coupled_fleet --agent-bank-dir D:\MYRIAD\agentbank --ability-bank-dir D:\MYRIAD\abilitybank --out-dir D:\MYRIAD\coupled_candidates --start 1 --end 10 --slots 1000 --steps 3 --approve-training
```

Each agent's 411,000 weights are updated by backprop on a synthetic target conditioned on its **actual 32-dimension ability vectors**. The original agent bank remains intact. The adapter bank is separately updated if selected rows are untrained. All resulting neural candidates are disk-backed and SHA-verified; **none is auto-promoted**. Replay resumes only when existing candidate receipts and source bank hashes still match.

5. To export/recover a bounded subset (1..100 agents per ZIP), use:

```powershell
python -m training.portable_bank_bundle export --agent-bank-dir D:\MYRIAD\agentbank --ability-bank-dir D:\MYRIAD\abilitybank --bundle D:\MYRIAD\myriad_joint_1_to_10.zip --start 1 --end 10
python -m training.portable_bank_bundle restore --bundle D:\MYRIAD\myriad_joint_1_to_10.zip --agent-bank-dir D:\MYRIAD_RESTORED\agentbank --ability-bank-dir D:\MYRIAD_RESTORED\abilitybank --approve-write
```

Restored agent rows are `imported_unverified` until independently updated with fresh gradient-training evidence. Ability rows remain explicitly **synthetic-trained**. This backup is not the missing full 10,000-agent/10M-ability original checkpoint.

## Reproduced test-host evidence (2026-11-23)

- Validated the actual 10-agent portable source, checked all ten individual hashes and strict archive metadata.
- Imported 10 rows into an otherwise empty full-size (sparse reserved) agent bank; no fabricated agent-training rows for the remaining 9,990 agents.
- Ran PyTorch autograd to update all 10 imported agent policy networks. Each row is individually SHA-256 verified in the ledger.
- Trained **10,000 synthetic ability adapters** (1,000 per test agent), bound them to the 10 agent models and generated ten quarantined neural candidates through 30 additional gradient steps (3 steps each).
- Ten of ten paired candidates improved on the synthetic holdout; all ten paired candidate checkpoints have verified hashes and unchanged source agent bank rows.
- Exported the 10-agent + 10,000-adapter joint archive and restored it to a cold, separate bank. Restore verified all agent hashes and synthetic ability batch hashes. Restored agent status is conservatively `imported_unverified`.
- All project tests including new negative-path coverage: **96 passed, 3 skipped** (measured on the integrated source in this execution environment).
- Integration readiness is **BLOCKED 1/13**, since current environment has only 10/10,000 trained agent rows and 10,000/10,000,000 ability rows. The historic full banks were not recovered.

## Prohibited conclusions and operations

No current evidence establishes general intelligence, real-world skill mastery, trading alpha, profitability, perpetual 10,000-LLM inference, or live model-server deployment. Maintain `execution_authorized=false`, `production_decision_authorized=false`, `auto_promote=false` and `automatic_merge_allowed=false`.

Neither UMBRA nor ICARUS OMNIGENESIS PR #503 may be modified, combined or merged until all 13 release gates have independent evidence and the owner explicitly approves a reviewed integration. This work belongs to **HEAD B** (`agent/myriad-head-b-training`), not the owner/coordination HEAD A or runtime HEAD C paths.

### Next head's priorities

1. Obtain the original large physical bank **bytes and ledgers** through a user-authorized mount or download. Compare exact dimensions, row integrity and ledger completeness before saying they are attached.
2. Verify the original 50k synthetic ability batches, then run the coupled trainer against real original 1k-ID slices. The new span verifier supports that exact layout.
3. Extend curricula beyond toy synthetic regression: instruction-following/coding, source-grounded decisions, causal transfer, anti-leakage, independent market holdouts and supervised real tasks.
4. Make GPU/CPU budget, pause/resume, disk pressure, and corrupt-batch recovery measurable on the user's *actual* 16 GB NIMO laptop.
5. Publish exact source commit SHA, test output and checkpoint hashes to GitHub issue #3 and master issue #1. Never publish passwords/API secrets or silently invent unavailable weight files.

## Portable integrated subset identity

The separate `MYRIAD_COUPLED_10_AGENT_10000_ADAPTERS.zip` contains the ten **newly** synthetic gradient-trained agent vectors, 10,000 synthetic adapter vectors and their per-range checksums. Exact SHA-256: `6308d1a06511dfc9fff037f5a22351273c645d43020fdad8e11c6c368c14871d`, bytes: `8,033,942`. It was independently restored to a fresh on-disk full-layout sparse bank, and all ten agent hashes plus adapter ranges were verified. The restore correctly demotes agent status to `imported_unverified`; training evidence needs to be reestablished on the destination host.

The separate evidence file `training/BANK_INTEGRATION_EVIDENCE.json` contains ten paired candidate checkpoints and exact before/after numerical values, without model or adapter binary contents. The actual 10 quarantined candidate files are in the execution host only, not automatically in GitHub or the portable joint checkpoint.