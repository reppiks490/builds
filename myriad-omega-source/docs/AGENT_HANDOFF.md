> **2026-11-23 v1.5 correction:** The latest recovery path is `myriad-omega-v15/` and exact HEAD A/B/C roles are in `coordination/`. Historical references to a single `SOURCE_BUNDLE.tar.gz.b64` are descriptive; actual repository snapshot is split across `SOURCE_BUNDLE.tar.gz.b64.partNN`, verified by `SOURCE_BUNDLE_INFO.json`. Full trained weight banks are NOT included. Read `docs/PHASE_V15.md` for the new hard provider-call quota. Keep this older handoff as historical context; check v1.5 test/source hashes before using its counts.

# MYRIAD Ω PENTARCH — Authoritative cross-session engineering handoff

**Checkpoint:** 2026-11-23, local development branch `agent/myriad-omega-independent-handoff` in `reppiks490/builds`, directory `myriad-omega/`. **Standalone source; never merge to UMBRA or ICARUS until release gates pass.**

## 0. The user's precise directives and nonnegotiable constraints

- Create an unusually ambitious, visual, evolving multi-harness platform with **10 tiers, 5 model-brain roles, 100 workflows, 1,000 pipelines, 10,000 equally capable core agents, 40,000 pupil slots, 1,500 skill definitions, 500 classes and 1,000 curriculum tracks**.
- Every core agent must own **at least 400,000 independently trainable parameters**, not one global 400,000-parameter model. Implemented synthetic-policy architecture uses **411,000 parameters per agent**, total **4.11 billion agent-owned parameters**.
- Provide **10,000,000 independently addressable and gradient-trained lightweight ability adapters**. Implemented with **32 parameters/adapter**, **320 million parameters**, synthetic regression learning only. No ability has been independently certified as a distinct useful real-world skill.
- Support general intelligence, trading/financial research, and practical real-world mastery as evaluable development targets, NOT presumed accomplishments.
- 16 GB NIMO laptop: keep 10,000 logical agent identities and queues manageable, use shared inference endpoints with bounded concurrency and disk-backed weights. Do not promise 10,000 simultaneous LLM generations or perpetual uptime.
- **ONLY AFTER THE ENTIRE MYRIAD SYSTEM IS COMPLETE** integrate into `reppiks490/umbra-sovereign-worlds` and the OMNIGENESIS development branch of `reppiks490/Icarus` PR #503, and later consider reviewed integration into `main`. NO pre-completion cross-repo changes or merge. No live trading/production authority.
- Preserve progress accurately in GitHub so the next chat takes over WITHOUT guessing details or redoing earlier work.
- The user prohibited OpenAI Codex for scheduled automations across projects. Any automation proposed for MYRIAD must use permitted non-Codex mechanisms, not silently switch back to Codex.

## 1. Definitive source/recovery path

1. GitHub repo: `https://github.com/reppiks490/builds`.
2. Branch: `agent/myriad-omega-independent-handoff`. `main` is separate and must remain untouched.
3. GitHub folder: `myriad-omega/`. See `myriad-omega/README_NEXT_CHAT.md` and `myriad-omega/SOURCE_MANIFEST.json`.
4. The complete **text source+tests+docs** is archived as `myriad-omega/SOURCE_BUNDLE.tar.gz.b64` (base64 text envelope) for exact regeneration. Its decoded SHA-256 is recorded in `SOURCE_MANIFEST.json`. It deliberately **excludes weights, secrets, sqlite live databases, generated screenshots, and megabyte-sized experiment checkpoints**. Check before relying on complete portable training.
5. The user also has a persistent ChatGPT Library snapshot `/MYRIAD-OMEGA/MYRIAD_OMEGA_v1.3_SOURCE_AND_HANDOFF.zip` and download link in the originating chat (if the upload succeeded). The SHA-256 in the same manifest controls identity.
6. If GitHub source or Library snapshot is unavailable, do not invent file contents or claim continuity; report missing artifact and consult the existing current chat or previous source ZIPs.

## 2. Observed local engineering status (not invented deployment)

- Backend: Python modules `fabric.py`, `mission_graph.py`, `agent_mesh.py`, `operations.py`, `operations_extended.py`, `pipeline_runtime.py`, `hyper_registry.py`, `mastery.py` and `server.py`. Local dashboard: `index.html`, `assets/console.js`, `assets/theme.css`.
- Model gateway: configurable Ollama, OpenAI-compatible, Anthropic and Gemini protocols. **Real models not connected on user's Windows laptop; no 5-brain authenticated live endpoint certification**. Loopback HTTP integration with a scripted fixture passed, which tests protocol wiring, not intelligence.
- Actor fleet: **10,000 coroutine task mailboxes**, full-fleet synthetic dispatch acknowledged; workers are lightweight and model generations are bounded to shared scheduler concurrency. `AgentMesh` status distinguishes registered from model-active.
- Definitions: 10 tiers, 5 brains, 100 bounded workflow demonstrations, 1,000 deterministic pipeline demonstrations, 1,500 skill registry entries, 500 classes, 1,000 planned curriculum tracks. Registry counts do **not** measure mastered abilities.
- Individual weight bank: 10,000 small MLPs of 411,000 parameters each, 8,220,000,000 FP16 bytes plus SQLite evidence, stored in earlier local training host at `/mnt/data/myriad_omega_v10/training/agentbank` when checked; **NOT in GitHub or source ZIP**. Per-agent hashes verified in the earlier local run; reverify source fingerprints and real bank availability in a new session. Each network had **two synthetic AdamW gradient steps**, not extensive fine-tuning.
- Ability bank: 10,000,000 independent 32-weight synthetic micro-adapters, approx 640,000,000 bytes, earlier at `/mnt/data/myriad_omega_v10/training/abilitybank`; **NOT** portable source. All 200 groups passed hash checks during earlier audit. Not general intelligence or real skills.
- Synthetic robustness: `ROBUSTNESS_GAUNTLET_100_AGENTS.json` evaluated 100 sampled trained agents on normal, shifted, feature-dropout and noise environments. Shifted generalization remains weak.
- Transfer candidates: **109 quarantined updates** in `/mnt/data/myriad_omega_v13/training/transfer_candidates` (local session), not promoted to live weights. Stronger shifted synthetic validation but still synthetic teacher. New auditor rejects orphan weights, stale pending files, identity mismatches, and false gate statuses.
- Evidence memory: `evidence_vault.py` append-only SQLite observation chain with sidecar anchor, result qualification `untrusted_model_output`, no self-certified truth or auto-promotion. New check enforces 100-workflow membership of each agent.
- Existing release gate `integration_guard.py --require-ready`: deliberately returns exit code 2 for incomplete MYRIAD. Previously 3/13 gates passed; rerun with exact checkpoint paths. No cross-project changes permitted now.
- The dashboard and local API are **localhost-only** and NOT evidence of public hosting, iPhone 5G reachability, authorized live brokerage or 24/7 cloud service.

## 3. Exact commands on a fresh extracted source checkout

```bash
python -m pip install -r training/requirements.txt pytest
python -m pytest -q
python certify_fleet.py
python integration_guard.py --require-ready  # expected exit 2 on a standalone source checkout
python server.py                          # listens on http://127.0.0.1:8788 locally
```

For a host with verified, exact full checkpoint folders:

```bash
python integration_guard.py --agent-bank-dir /path/to/training/agentbank --ability-bank-dir /path/to/training/abilitybank --out readiness.json --require-ready
python -m training.robustness_gauntlet --bank-dir /path/to/training/agentbank --sample 100
python -m training.transfer_adaptation --bank-dir /path/to/training/agentbank --out-dir /separate/quarantine --start 1 --count 10 --steps 12
```

These are limited/synthetic tests only. Review CPU/disk/thermal budget on the actual 16 GB laptop before executing full-fleet training scripts.

## 4. Actual next development priorities in order

1. Recover source snapshot and run tests. Compare GitHub `SOURCE_MANIFEST.json` / SHA to local bytes; check current repository HEAD and recent commits first.
2. Install and audit a small **real local model** only on an authorized host; test genuine five-brain connected inference on a bounded, non-sensitive, offline task. Never claim connected credentials or model installation absent evidence.
3. Build an independently curated benchmark suite: unseen general reasoning/coding/data tasks; trading with chronology, realistic fees, multiple testing, train/test embargo, out-of-sample and forward shadow; practical real-world execution via safely permissioned tools. Record baseline vs candidates and failures.
4. Scale training quality rather than just more counts: longer curricula, adapter versioning, holdout and OOD evaluation, anti-forgetting tests, simulator-to-real gap checks, manual review before promotion.
5. Full security evaluation: authentication, RBAC, outbound network policies, prompt-injection, data-scope boundaries, tenant separation, cost ceilings, kill switches, key rotation, and disaster recovery. Existing localhost UI is not production-secured.
6. Operator environment: laptop deployment, endpoint health, resumability under restart, queue fairness, persistent event log, resource/backpressure accounting; real iPhone view only after secure remote access.
7. Only after 13/13 verified, author research-only UMBRA and OMNIGENESIS adapters pinned to current SHAs on **separate review branches**; preserve authoritative scientific controls, no live trading; rerun all target CI and independent review before owner-authorized `main` merges.

## 5. Integration targets (read-only until release)

- `reppiks490/umbra-sovereign-worlds`, default `main`: v5 civilization simulation with synthetic ecology/social dynamics. Existing draft PRs are not equivalent to deployed production. Do not modify the live chatgpt.site site.
- `reppiks490/Icarus`, OMNIGENESIS [PR #503](https://github.com/reppiks490/Icarus/pull/503), head `agent/omnigenesis-phase-01-foundation`, target `main`: **draft, open, unmerged** when last checked. Scientific evidence, replay, Constellation 12-worker CI, with research-only authority `execution_authorized=false`, `production_decision_authorized=false`, `auto_promote=false`.
- Keep federation freshness blocker and canonical UI/Windows/engine checks as strict independent gates. No re-enabling broker execution, no claims of real profit, no bypass.

## 6. Safety/truth taxonomy used in every status report

- `registered`: logical identity/definition exists.
- `scheduled`: independent task mailbox exists.
- `executed`: code path ran locally with documented inputs.
- `gradient_trained`: neural weights changed under an explicit objective.
- `synthetic_validated`: held-out test used synthetic teacher/world.
- `real_model_connected`: authenticated endpoint actually returned output on target host.
- `externally_validated`: independently curated benchmark and evidence.
- `production_approved`: release gates and owner approval, with scope-specific authority.

Never upgrade a lower status by inference. Stored row hashes establish only **local integrity**, not that the models are intelligent, authentic, autonomous, or useful. No agent can self-authorize a release.

## 7. No invisible work / continuation guarantee

Only work actually executed in a session may be reported as executed. This transcript does not establish continuous background training. Finish each future development session by updating GitHub branch documentation with source hashes, exact tested command outputs, blocked gates, new evidence, and a handoff. Do not create a standing automation without a separate bounded, authorized scheduling design and cost review.


## Continuation after v1.3: v1.4 (2026-11-23)

**Latest GitHub recovery folder is `myriad-omega-v14/` on the same standalone branch**; historical `myriad-omega/` v1.3 is preserved and must not be confused with the latest state. Read `docs/PHASE_V14.md`, `docs/NEXT_CHAT_PROMPT.md`, the 13-gate matrix, and the new SOURCE_BUNDLE_INFO and manifest before editing. Version v1.4 adds refusal of model HTTP redirects, durable all-jobs crash recovery, JSON/Origin mutation validation, a manual-only synthetic holdout benchmark with private per-run transcripts and independent grade recomputation, and read-only observatory telemetry. It does not add actual provider credentials, scientific proof of mastery, full checkpoints, production permissions, or any UMBRA/ICARUS merge. Do not carry historical v1.3 SHA claims forward as v1.4's SHA.
