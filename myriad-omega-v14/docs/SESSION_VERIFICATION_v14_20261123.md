# MYRIAD Ω v1.4 — Engineering continuation and source-certification receipt

**Date:** 2026-11-23. **Authority:** standalone research-only. **Repositories UMBRA and ICARUS not modified.** Do not merge or auto-promote.

## Source and restoration

- Repository: `reppiks490/builds`; branch `agent/myriad-omega-independent-handoff`; latest v1.4 folder `myriad-omega-v14/`; legacy v1.3 folder `myriad-omega/` must be preserved.
- Source ZIP: `MYRIAD_OMEGA_v1.4_SOURCE_AND_HANDOFF.zip`, **248,914 bytes**; SHA256 `549ef23061b334e1ab2f1004a09aa2c7df89b4691d87fa4c101f3ee167cf0d1a`.
- Deterministic tar.gz source bundle: **193,897 bytes**; SHA256 `b09ce2a5942f34ab37147a8cae12ea911b96940df66dd44f74a5399da9b42b20`; 258,532 base64 chars in 9 numbered text parts.
- Source count: **112 files** including the source-file manifest. Manifest SHA256 `c4f19117eddc736e916fb19e573a6b0288973389875f03ee3e0a453d14465668`.
- Verify decompressed tar and every file against `SOURCE_MANIFEST.json`. Decode base64 in part order without interpreting whitespace; reject unsafe tar paths; restore into clean directory. Do not run unverified source.
- Public GitHub source archive deliberately EXCLUDES original ~8.22GB synthetic-trained individual-agent bank, ~640MB 10M synthetic ability adapter bank, 736KB forensic row-digest report, all model credentials, private benchmark answer keys, SQLite databases, trained candidate checkpoints and screenshots. Do not claim those weights are in GitHub.

## Actual engineering changes

1. Model HTTP redirects blocked; provider size cap and strict JSON shape. Tests verify second redirect target receives NO requests even when supplied a fake Authorization header.
2. Restart replay barrier sweeps ALL persisted queued/running jobs, marks them `interrupted`, restores per-workflow round-robin cursor and per-agent completed mission counts; no automatic paid-model replays.
3. Exact-Origin JSON-only local mutations, cross-port Origin rejection.
4. Manual-only independent **synthetic** benchmark: fresh private holdout generation, withheld answer keys, exact integer grading, privately stored transcripts and offline recomputation/tampering tests. It does NOT certify real-world mastery, trading profitability, AGI or production security.
5. Read-only dashboard summary `/api/evaluations/holdout`. No browser button for paid benchmark calls.
6. Packaging excludes all `evaluation_runs/` private model responses and answer keys. Full source release remains source-only.

## Observed test evidence

- Extracted v1.3 source baseline: `python -m pytest -q` => 67 passed, 3 skipped.
- v1.4 source worktree: `python -m pytest -q` => **77 passed, 3 skipped**.
- Extracted v1.4 ZIP in clean directory: `python -m pytest -q` => **77 passed, 3 skipped**.
- `node --check assets/console.js`: success.
- `python -m training.independent_eval --brain NOESIS --cases 5` => exit **2 BLOCKED** (no permission); with `--allow-provider-calls` => exit **2 BLOCKED** (model unavailable). No real provider requests made.
- Five brain model routes on this execution host: 0/5 connected. Startup HTTP `/api/health`: 10,000 coroutine workers reported live locally; no model inference supported by that statistic. `/api/evaluations/holdout`: 0 verified actual external-model runs.
- Desktop 1440x900 and phone 390x844 Chromium render of exact HTML/CSS/JS with recorded LIVE HTTP response fixtures: **100 workflow buttons**, 0 JavaScript errors, 0 horizontal overflow; benchmark panel correctly labels 0 verified runs. Direct browser navigation to localhost blocked by environment, so **not** a true browser-to-server end-to-end test or a real iPhone test.
- `python integration_guard.py --require-ready`: exit **2 BLOCKED**, **1/13** release gates from the source-only archive. The older **3/13** figure was from a different full-weight training host. Do not copy it to this source-only release.

## Limitations and next work

- No connected actual LLM inference and no audited real model-spend/compute throughput on the operator's 16GB NIMO laptop.
- No qualified 10M practical skills, no 1,000 independent track exams, and no verified live trading performance. Synthetic MLP policies and tiny adapters are not frontier LLMs.
- No permanent cloud-hosted 10,000-agent job fleet, external checkpoints, production auth/TLS, disaster recovery or independent security review.
- Benchmarks are local synthetic tasks, not independent external competency certification; origin and host headers aren't substitutes for production security.
- Continue with real provider/authenticated inference evidence under approved cost ceiling, independent benchmark suites, security/load testing, checkpoint portability, human-reviewed release gates. Preserve 13-gate lock.

## Target integration lock

- **UMBRA:** `reppiks490/umbra-sovereign-worlds`, main. **Never write before release complete.**
- **OMNIGENESIS:** `reppiks490/Icarus` draft PR #503 into main; branch `agent/omnigenesis-phase-01-foundation`. Do not force merge or bypass original scientific CI and peer freshness.
- On any next turn, refresh the exact target HEAD SHAs and all CI, but do not touch them while MYRIAD is blocked.
- Scheduled workflows cannot use Codex. Do not infer continuous execution from a saved handoff.