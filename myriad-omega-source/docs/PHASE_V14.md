# MYRIAD Ω v1.4 — Verified hardening, sealed-model evaluation and continuity

## Scope and engineering truth

This checkpoint extends the standalone v1.3 system. It **does not** modify UMBRA, ICARUS or OMNIGENESIS PR #503. No auto-promotions, broker orders, trading recommendations or unapproved provider calls. A 10,000-coroutine worker fleet is not 10,000 simultaneous LLM reasoning processes.

### Changes in v1.4

1. `fabric.py / ModelGateway._http`: disallow HTTP(S) redirects, including local redirects, before a bearer token/API key can be forwarded; limit response size to 3,000,000 bytes with an extra-byte check; validate JSON content-type and top-level object. Local two-server test proves the redirected target receives **zero** requests.
2. `fabric.py / _restore_history`: every `queued` or `running` persisted mission is changed to `interrupted` before bounded history loads. No provider requests are automatically replayed. Restore round-robin cursor and completed mission counts from the full persisted jobs table. New `recovered_interrupted_jobs` telemetry.
3. `http_security.py` and `server.py`: enforce `application/json` for all mutation endpoints; when Origin is present require exact same scheme/host/port origin and no credential/path/query fragments. Browser UI uses JSON already; not production authentication/TLS.
4. `training/independent_eval.py`: optional, bounded **manually authorized** external model benchmark for one to five model-brain routes. Five synthetic domains: arithmetic, algebra, synthetic trading-cost accounting, as-of chronology/future exclusion, resource planning. Fresh random private holdout seed created only when evaluation starts. The provider sees prompts but no answer keys. Results are recorded with private input/output transcripts, SHA-256 commitments and separate public scores; offline `verify_run()` recomputes all grades and tampering checks. This is a *synthetic reasoning check*, not an external independent certification or proof of market profitability.
5. `server.py`, `assets/console.js`, `index.html`: read-only `/api/evaluations/holdout` UI panel. It cannot trigger paid model calls, training, promotions or brokerage actions.
6. Packaging denylist excludes the full `evaluation_runs/` directory because it contains **private answer keys and model responses**. All large training checkpoint banks remain excluded as before.
7. Regression coverage adds tests for unauthorized model calls, DNS/HTTP redirect credential forwarding, response limits, crash recovery beyond 100 jobs, sealed key and independent grade recomputation, tampered answers, malformed model output, and cross-origin mutations.

## How to evaluate a connected model manually

```bash
# Safe: no model requests, expected BLOCKED exit code 2
python -m training.independent_eval --brain NOESIS --cases 10

# OPERATOR ACTION: only when a real provider is installed, credentials (if required)
# are configured, and provider pricing/request counts are reviewed.
# One brain / 10 cases = at most 10 calls. Choose up to 5 roles, max 100 total.
python -m training.independent_eval --brain NOESIS --cases 10 \
  --out evaluation_runs --allow-provider-calls
```

`evaluation_runs/EVAL-*/PUBLIC_RESULTS.json` contains score receipt and claims no certification. `PRIVATE_HOLDOUT_KEY.json` and `PRIVATE_TRANSCRIPTS.json` are local private 0600 files and **must not be committed or published**. Call `training.independent_eval.verify_run(directory)` to check each exact answer and every grade. The UI exposes only coarse aggregate synthetic scores, never private keys or raw provider responses.

No provider credentials were found on this test host and no real model benchmark was invoked. On the source-only snapshot, all five model-brain routes are OFFLINE.

## Verification matrix (v1.4)

- Baseline source v1.3 clean extraction: **67 passed, 3 skipped**.
- v1.4 in-place Python suite: **77 passed, 3 skipped**.
- JavaScript: `node --check assets/console.js` passed.
- Manual evaluator without opt-in: exit 2 (BLOCKED), no model calls.
- Manual evaluator with opt-in but no model server: exit 2 (BLOCKED), no model calls.
- Actual loopback server GET `/api/health`: 10,000 actor coroutines acknowledged; `/api/models`: 5/5 offline; `/api/evaluations/holdout`: 0 verified runs. This tests source runtime, not the operator's laptop.
- Local release gate without external weights: exit 2 (BLOCKED), **1/13** gates. Earlier separate full-host checkpoint audit recorded **3/13** when 8.22GB and 640MB banks existed; those are absent from the GitHub/ZIP snapshot and must not be assumed on a new host.
- Real external LLM calls, real trading alpha, 1,000-track qualification, 10 million externally meaningful mastery certificates: **not verified**.

## Release authority and integration

`research_only=true`, `execution_authorized=false`, `production_decision_authorized=false`, `auto_promote=false`. Do not modify `reppiks490/umbra-sovereign-worlds` or `reppiks490/Icarus` draft PR #503 until all 13 gates pass, owner authorizes a staged review, and current SHAs are refreshed. No `main` branch merges in this phase. Historical v1.3 evidence remains archived separately; do not overwrite or erase it.

## Next high-leverage work

- Real authenticated five-brain model inference under explicit resource/cost ceiling; record actual tested models and their outputs.
- Independent curated benchmark suites with unseen code, multi-step reasoning, real data provenance and supervised action tasks; synthetic arithmetic alone is inadequate.
- Cost control and provider quotas, kill-switch and audit for API requests, durable request idempotency and power-loss testing.
- Real operating system + GPU/CPU measurement on the 16 GB NIMO laptop; thermal and battery behavior.
- Full threat model, authentication before any public deployment, third-party prompt-injection testing.
- Reproducible training and review of individual adaptive weights against a genuinely separate holdout, not synthetic teacher leakage.
