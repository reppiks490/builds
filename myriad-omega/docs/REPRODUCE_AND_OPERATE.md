# Reproduction, rollback and continuity playbook

## Step 1 — Verify source identity

- Use exact branch `reppiks490/builds@agent/myriad-omega-independent-handoff`, folder `myriad-omega`.
- Download `SOURCE_BUNDLE.tar.gz.b64` and decode with Python: `base64.b64decode(Path('SOURCE_BUNDLE.tar.gz.b64').read_text())` then verify `sha256` against `SOURCE_MANIFEST.json` before opening. Extract only under a clean empty directory, inspect member paths before extraction, and refuse absolute or `..` member paths.
- Or use persistent Library file `/MYRIAD-OMEGA/MYRIAD_OMEGA_v1.3_SOURCE_AND_HANDOFF.zip` with matching SHA, if available.
- Keep source and large checkpoints separate. Never reconstruct claimed training from JSON-only ledgers.

## Step 2 — Dependencies and tests

- Python >= 3.10; `python -m pip install -r training/requirements.txt pytest` (ideally new virtual environment and pinned hashes for real deployments).
- Run `python -m pytest -q` and record stdout, exit code, Python/PyTorch versions and source checksum.
- In the known v1.3 environment, 69 automated tests passed. Re-test on any new host. No external CI or model connectivity evidence from this local result.
- `python integration_guard.py --require-ready` must return exit code 2 while incomplete. Exit 0 without `--require-ready` only means a report was generated, not approval.

## Step 3 — Validate training artifacts (if host contains them)

- `training/agentbank/agent_weights.fp16`: exact 8,220,000,000 bytes for 10,000 x 411,000 FP16. `weight_ledger.sqlite3` row digests, train step counts and per-agent byte checks are mandatory. Hashing whole bank may be time consuming.
- `training/abilitybank`: 10 million 32-weight vectors, 200 stored training batches and ledger; it is a synthetic teacher, not a library of mastered skills.
- Source ZIP deliberately excludes these. Need to train or restore known-good separately; do not copy from speculative paths, and do not regenerate claims without rerunning.
- `training/transfer_candidates` is quarantined. It contains local candidate checkpoints only; the final source bundle intentionally excludes these candidate weight files, but retains summary audit.

## Step 4 — Model gateway (not enabled by default)

- `model_connections.env.example`: review. No credentials committed. Configure per brain NOESIS, MNEMOSYNE, PRAXIS, AEGIS, METIS.
- Use one compact Ollama model on 16 GB laptop, model sharing and low concurrency. Never expose `server.py` unauthenticated on public Internet.
- Run read-only test mission first, check model identity, receipts, cost, error handling and lifecycle. `tests/test_http_model_mission.py` uses scripted fixture only, not a real LLM.

## Step 5 — Failure recovery

- On interrupted job: status `interrupted`, no silent rerun; manual resume after inspection.
- Evidence vault: restart fails closed on damaged or missing anchor; preserve damaged DB and anchor for forensic inspection, never rewrite receipts to appear valid.
- Trained weight mismatch: refuse inference and retrain from a clean checkpoint in separate directory, do not patch the hash ledger.
- Candidate training incomplete: orphan/pending files now detected and flagged; archive for investigation, never silently count them as valid.
- Git conflicts: never force-push or rewrite other agents' branch histories. Update via a new branch or reviewed pull request.

## Step 6 — Laptop resource limits

10,000 agent identities are small in-memory records; 10,000 independent 411k models take 8.22 GB *on disk* in FP16. Each gradient step temporarily needs fp32 weights, optimizer state, gradients, activations, process overhead. Train one/few agent(s) at a time; never allocate 4.11B fp32+Adam state in 16GB RAM. CPU and thermal throttling must be measured. 10k live LLM inference sessions are not realistic.

## Step 7 — Release and integration

Do not touch UMBRA or ICARUS PR #503 until all 13 gates pass at exact source/target SHAs and the user confirms reviewed merge. Preserve no-broker/no-production/no-auto-promote boundaries. All integration adapters must initially be read-only.