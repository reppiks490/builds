# MYRIAD Ω PENTARCH v1.4 — Verified Research Harness

**Status: RELEASE-LOCKED / RESEARCH-ONLY.** Latest phase: [v1.4 verified engineering and offline benchmark](docs/PHASE_V14.md). As of 2026-11-23, three of thirteen completion gates passed. Do not merge into UMBRA Ω or ICARUS OMNIGENESIS, authorize real trading, or claim deployed general intelligence. The complete results and limitations are in [BUILD_STATUS_v1.md](BUILD_STATUS_v1.md), [VERIFICATION.md](VERIFICATION.md) and [CURRENT_READINESS.json](CURRENT_READINESS.json).

## Actual architecture and checks

| Component | Observed in this execution environment | Boundary |
|---|---|---|
| 10 tiers, 5 brain roles, 100 workflow definitions | Registry consistent | Five real model endpoints are not connected |
| 10,000 agent identities | 10,000/10,000 in-process coroutine task acknowledgements (100 per workflow) | At most two concurrent shared language-model missions by default; **not** 10,000 simultaneous LLM generations |
| 100 workflow examples | 100 distinct bounded deterministic examples tested | Not 100 certified professional products |
| 1,000 pipeline examples | 1,000/1,000 reproducible offline operation receipts | Not independently qualified production pipelines |
| 10,000 agent-owned policy networks | 411,000 neural parameters **each**, real PyTorch AdamW/autograd synthetic training, all 10,000 FP16 row hashes rechecked | Small MLP synthetic decision models, **not** fine-tuned foundation LLMs |
| 10,000,000 ability adapters | 32 trainable parameters each, synthetic teacher, all 200 bank batch hashes rechecked | **Zero** independently proven real-world abilities |
| 1,500 skills, 500 classes, 1,000 mastery tracks | Registries and curriculum definitions | Not independently trained or evaluated mastery across 1,000 tracks |
| Adaptive learning | 100 candidate updates independently trained and kept quarantined; 0 auto-promoted | Not perpetual or authorized autonomous self-improvement |
| Local command center | Desktop/mobile browser fixture checks from recorded real HTTP responses, no JS errors | No hosted public iPhone access or auth/TLS |

**Weights:** the 10,000 individually owned 411,000-parameter neural networks total 4.11 billion parameters and **8,220,000,000 FP16 bytes on disk**. The separate 10-million small-adapter bank stores **640 MB** of weights. These large checkpoints were created and integrity-checked on the training host. **They are intentionally excluded from the portable source ZIP**, which is not a pre-trained deployment. Checkpoint hashes and auditable summaries are included; recreating weights locally is optional and consumes disk, RAM, and CPU time.

## Run locally on Windows (review scripts before execution)

1. Extract the **source** ZIP to a normal folder. Open PowerShell inside it. Install Python 3.10+.
2. Install reviewed dependencies: `python -m pip install -r training/requirements.txt`.
3. Optional: run full resumable synthetic weight training with `./training/train_full_10000_windows.ps1`, reserving about **8.22 GB** for agent checkpoints alone. This can be slow on a 16 GB RAM laptop. To begin with 10 agents, use `./training/train_full_10000_windows.ps1 -Start 1 -End 10` and resume later.
4. Optional: run `./training/train_all_abilities_windows.ps1` to recreate the separate 10-million synthetic micro-adapter bank. Both steps are independent and do **not** establish general intelligence or trading ability.
5. Verify local files using `./training/verify_local_training_windows.ps1` and `python integration_guard.py --require-ready` (expected exit **2** while the release is blocked).
6. Start `python server.py`, and open `http://127.0.0.1:8788` **on that same PC**. The UI reports absent checkpoints and offline models distinctly rather than inventing trained agents.
7. To attempt actual language-model reasoning, install Ollama from the [official site](https://ollama.com/download/windows), review `bootstrap_windows.ps1`, explicitly pull a model (e.g., a small supported Qwen model) and configure role-specific `MYRIAD_MODEL_*` variables. External/provider model inference has not been verified on your computer.

### Portable proof: inspect 10 trained agents without an 8.22 GB download

A **separate** `MYRIAD_OMEGA_v1.0_TRAINED_10_AGENT_POLICY_DEMO.zip` contains 10 real trained 411,000-parameter small synthetic-policy checkpoints with a SHA-256 manifest. Keep this demo ZIP alongside the extracted source folder and run:

```powershell
python -m training.portable_policy_demo infer --sample ..\MYRIAD_OMEGA_v1.0_TRAINED_10_AGENT_POLICY_DEMO.zip --agent 10
```

Adjust `--sample` to the correct relative or absolute location. This is a genuine read-only PyTorch forward pass using verified individual weights. The demo is **not** 10,000 trained weights, not a language model, not a trading tool, and not a real-world mastery certificate. To create another sample from a fully trained local bank, run `python -m training.portable_policy_demo build --sample sample.zip --bank-dir training/agentbank`.

### Model backends

The backend supports local Ollama / OpenAI-compatible endpoints and configurable Anthropic/Gemini API adapters with explicit credentials and permissions. **No model, API subscription, or provider account was installed, charged, or authenticated as part of this package.** A 16 GB laptop should use a single compact shared model, disk-backed agent weights and heavily capped inference throughput. Never put API keys in public repositories. Do not publish the unauthenticated localhost service onto the open Internet.

## v1.4 — verified new operational safeguards

The local harness now rejects HTTP model redirects, oversized provider responses and cross-port Origin mutations. Cold restart marks **all** incomplete jobs interrupted without model-call replay and preserves round-robin assignment. A **manual-only synthetic holdout** can grade actual model responses against withheld independent arithmetic/accounting/chronology answers, verify private transcripts and expose coarse read-only results in the dashboard. No provider requests run merely because the UI is opened.

**Launch gate:** `python -m training.independent_eval --brain NOESIS --cases 10` fails CLOSED without `--allow-provider-calls`; supplying it still fails closed when the model is offline. Model calls may incur charges; review the backend configuration first. See [PHASE_V14.md](docs/PHASE_V14.md) for commands, audit scheme and limitations. `evaluation_runs/` contains secret answer keys and is excluded from source archives.

## Developer verification

```bash
python -m pip install -r training/requirements.txt pytest
python -m pytest -q tests training/test_training.py training/test_ability_weight_bank.py
python certify_fleet.py
python integration_guard.py --agent-bank-dir training/agentbank --ability-bank-dir training/abilitybank --require-ready
```

For **synthetic** agent-weight predictions from an actual verified saved row, see `/api/training/policy/AG-00001`. Training and adaptive summaries are at `/api/training/fleet` and `/api/adaptation/summary`. The `/api/fleet`, `/api/state`, `/api/models` endpoints distinguish worker registrations and live provider connectivity. See [DEPLOYMENT.md](DEPLOYMENT.md) for Windows and Docker notes; [RELEASE_MANIFEST.json](RELEASE_MANIFEST.json) holds source/checkpoint hashes. All SHA-256 checks establish local integrity only, not third-party provenance or scientific validity.

## Integration lock

The targets are **`reppiks490/umbra-sovereign-worlds`** and **`reppiks490/Icarus` draft OMNIGENESIS PR [#503](https://github.com/reppiks490/Icarus/pull/503)**, with `main` as the eventual reviewed target. **Neither target has been modified by this build.** Only after all thirteen gates pass, external reviews succeed and the owner explicitly approves may a staged, reviewed integration proceed. Preserve research-only flags, upstream scientific governance, fork histories and trading-execution prohibitions. See [INTEGRATION_PLAN.md](INTEGRATION_PLAN.md).

## Technical limits and evidence

The network's orbital motion is visual topology, **not** telemetry that 10,000 models are thinking. In-process worker acknowledgements, synthetic policy weights, and synthetic ability adapters are distinct from meaningful expertise. No independent AGI benchmark, real historical trading performance, forward paper record, real-world task-completion certificate, 24/7 host uptime, iPhone public access, or autonomous safe model self-modification was demonstrated. The 10 million capability figure refers to separately trainable 32-parameter micro-adapters, not 10 million sophisticated skills.

Evidence: [TRAINING_FULL_FLEET_AUDIT.json](TRAINING_FULL_FLEET_AUDIT.json), [TRAINED_AGENT_WEIGHT_DIGESTS.jsonl.gz](TRAINED_AGENT_WEIGHT_DIGESTS.jsonl.gz), [ADAPTIVE_PILOT_CERTIFICATION.json](ADAPTIVE_PILOT_CERTIFICATION.json), [FLEET_CERTIFICATION.json](FLEET_CERTIFICATION.json), [BROWSER_VERIFICATION.json](BROWSER_VERIFICATION.json), [ENGINEERING_CAPABILITY_REEVALUATION.json](ENGINEERING_CAPABILITY_REEVALUATION.json).

## v1.5 secure model budget and three-chat takeover

See `docs/PHASE_V15.md`, `coordination/THREE_HEAD_PROTOCOL.md` and `README_NEXT_CHAT.md`. The local server's default gateway denies model inference until the user explicitly sets three safety environment variables and a reachable provider. The read-only `GET /api/provider-budget` endpoint reports daily REQUEST quotas; it does **not** monitor real invoice amounts. The three separate chat-head prompts coordinate by GitHub branches/issues; they do not imply 3 concurrently running conversations until the user starts them. Research-only/no live broker/no unapproved cross-project merge remains nonnegotiable.
