# MYRIAD Ω v1.0 — Verification and release-blocker ledger

**2026-11-23. Research-only; integration refused.** The checked status of the full training host is **3/13 release gates passed, 10 blocked**. The source ZIP **does not contain** the training host's 8.22 GB agent or 640 MB ability banks; a clean extraction must reconstruct them before repeating full weight checks.

## Testable engineering results

| Check | Observed evidence | Scope / limits |
|---|---|---|
| 10 tiers, 5 brain roles and 100 workflow definitions | Registry assertions, fabric tests | Roles not distinct deployed foundation LLMs |
| Local actor startup and task dispatch | `FLEET_CERTIFICATION.json`: **10,000/10,000**, 100 workflow groups × 100, no errors | Coroutine task acknowledgement, not language-model execution |
| 100 workflow demonstrations | All W01–W100 implemented and tested | Bounded, deterministic local samples |
| 1,000 pipeline demonstrations | All pipeline IDs exercised, deterministic receipts | Integrity-only receipts, no external actions |
| 411,000-parameter agent policies | `TRAINING_FULL_FLEET_AUDIT.json`: 10,000 independently trained rows, 2 AdamW gradient steps per agent, 10,000 SHA256 row matches and unique hashes, zero corrupted | PyTorch synthetic teacher, no real-world validated mastery |
| Full agent weight-bank size | 8,220,000,000 FP16 bytes, 4.11 billion agent-owned parameters | Stored disk weights, not simultaneously loaded models |
| 10M ability micro-adapters | 10,000,000 independently addressable 32-weight adapters, all 200 SHA256 batch checks matching | Synthetic 32-param linear heads, no real-world certified abilities |
| Saved individual policy forward pass | Hash-verified PyTorch forward prediction returned via API; **10-agent portable trained-weight ZIP** tested and tamper refusal verified | Narrow eight-action synthetic policy |
| Quarantined adaptation | 100 synthetic candidate trainings, 100/100 receipt hashes, 0 promotions | No production self-learning loop |
| UI desktop and mobile | `BROWSER_VERIFICATION.json`, desktop/mobile preview images, 0 console exceptions | Chromium was blocked from direct localhost; API snapshots came from actual local HTTP server; browser used captured response fixtures |
| Host header safety | localhost-only validation and rejected foreign Host tests | No public TLS, remote auth, CSRF or tenant isolation |
| GitHub and production destinations | UMBRA/ICARUS unchanged | No target PR merge, CI deployment or broker permission |

## External gates still blocked

Actual live five-brain model inference; 1,000-track independent real-skill testing; general intelligence; trading proof via time-safe historical then forward paper evidence; real-world task completion; secure public deployment; recovery and scheduling; cross-repository source-pinned replay; current-HEAD multi-platform GitHub CI; independent scientific/security review and owner approval. Review [CURRENT_READINESS.json](CURRENT_READINESS.json) for exact gate identifiers.

Use `python integration_guard.py --require-ready --out CURRENT_READINESS.json`. The expected current exit code is **2**, indicating **BLOCKED**. Never weaken this failure code to get green CI.

## Package reproducibility

Run `python -m pytest -q tests training/test_training.py training/test_ability_weight_bank.py`. For the full source package extract into a new directory, run the same suite, and **do not** count full bank integrity checks as passed when checkpoint bytes are absent. The training host was separately scanned byte-by-byte and its full ledger hashes matched. The source archive carries proofs and scripts to regenerate; it is **not** a self-contained pretrained image or a standalone host deployment.


## v1.5 control-plane addition

Five-brain model calls are disabled by default and require an explicit persisted request quota. Three-head ownership checker rejects cross-head file edits. Exact clean extraction tests and source SHA are in `coordination/STATUS_LEDGER.md` and GitHub issue #1. Both improvements remain engineering controls, not externally certified intelligence or authority to merge.
