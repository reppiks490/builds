# MYRIAD Ω — Capability certification / 13 release gates

**No fabricated competence.** A deployment certificate requires evidence at target host, exact source SHA and independently sourced data.

| Gate | State in initial v1.3 checkpoint | Required evidence to promote |
|---|---|---|
| 1 Structural registry | PASS (local) | Counts from exact source, tests |
| 2 10,000 independent 411k synthetic policies | PASS (earlier local host evidence) | All row bytes, ledger steps and checkpoint SHA |
| 3 10M independent 32-weight synthetic adapters | PASS (earlier local host evidence) | 200/200 stored batch checks + format audit |
| 4 Meaningful skill benchmarks | BLOCKED | Independent real-data/general reasoning, coding, task completion evals |
| 5 Real model inference | BLOCKED | Authenticated five-brain provider execution, outputs, costs, isolation |
| 6 1,000-track mastery qualification | BLOCKED | All tracks have unseen independent tasks & exam evidence |
| 7 Production security | BLOCKED | Adversarial audit, network policy, auth, secrets protection, kill switches |
| 8 Deployment/recovery | BLOCKED | Long-running on real host, failure injection, restart, disaster recovery |
| 9 Cross-system replay | BLOCKED | Pinned UMBRA/ICARUS read-only compatibility, deterministic hashes |
| 10 Trading research quality | BLOCKED | Time-safe real market as-of data, fees, tests, forward shadow |
| 11 Current-HEAD CI | BLOCKED | All required checks on the *same* pinned final revision |
| 12 Independent review | BLOCKED | Human/security/scientific review with signed findings |
| 13 Owner-approved integration | BLOCKED | Explicit approval after other gates; no autonomous promotion |

In particular, **69 unit tests passing is not evidence that gates 4–13 passed**.

## Individual adaptation and memory safeguards (v1.3)

1. `transfer_adaptation.py` now evaluates candidate **reloaded FP16** weights on an unseen synthetic holdout, not only pre-quantization in-RAM parameters.
2. Candidate auditor fails on orphan `.fp16` files, stalled `.pending` files, forged pass flags, inconsistent agent IDs, invalid or nonfinite loss, bad parameter counts or SHA mismatch.
3. `evidence_vault.py` refuses records where workflow ID does not own the agent ID (100 agents/workflow), as well as invalid workflow numbers.
4. Only research/quarantine outputs may be stored; adaptation cannot promote, execute orders, or override existing research-only authority.

## v1.4 incremental engineering (does NOT qualify additional release gates)

- Provider redirects forbidden; response JSON bounds enforced; exact Origin and application/json for mutations.
- 100+ historical job crash case verified: all incomplete records interrupted, no auto replay; scheduling cursor restored.
- Newly generated synthetic held-out questions now have private answer-key, transcript and offline independent grade recomputation. No model benchmark was run against a real model or verified on the user's PC.
- 77 pass / 3 expected skip for local source-only pytest. Without neural checkpoints this clone is **1/13 gates**, not the earlier full-host 3/13.
- Next priority is actual provider-backed tasks and independently sourced real-world evaluations; keep the gate BLOCKED.