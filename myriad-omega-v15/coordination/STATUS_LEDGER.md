# MYRIAD Ω v1.5 — factual engineering readiness and blocked release ledger

**2026-11-23; pre-publication build. GitHub branch/ZIP checksums must be entered after verification.**

## Verified local baseline

- Recovered v1.4 snapshot and reran: **77 passed, 3 skipped**.
- v1.5: provider quota and three-chat ownership checks added; full regression count to be recorded after final clean extracted package test.
- Five model-brain roles: NOESIS, MNEMOSYNE, PRAXIS, AEGIS, METIS. Configurable via Ollama, OpenAI-compatible APIs, Anthropic, Gemini. **Actual model routes on test host: unverified/offline**; scripted loopback responses are not real model inference.
- Core registry and 10k actor task loops exist; 100 workflows have bounded deterministic demonstrations, 1000 pipelines have deterministic local operations; not 100 production-grade integrations.
- Older separately measured training host: 10k distinct 411,000-parameter policy neural weights trained with two synthetic gradient steps and individually hashed, total 8.22GB; 10M independent 32-weight synthetic micro-adapters (~640MB), trained on synthetic targets. Source archive does **not** contain these banks. A separate source-only install cannot verify their availability.
- No certified general intelligence, real market profitability, ten-million real expert capabilities, all-1000-track mastery, or user-laptop/24h hosting evidence.
- Release blocker is absolute: incomplete gate means **no UMBRA or OMNIGENESIS mutation**.

## New control plane

- `provider_budget.py` reserves quota BEFORE model request, is SQLite-durable across process crashes, blocks by default and never refunds unknown-charge attempts. Operator must intentionally set `MYRIAD_PROVIDER_APPROVED=1`, `MYRIAD_DAILY_REQUEST_LIMIT` in 1..1000, and `MYRIAD_REQUEST_MAX_OUTPUT_TOKENS` in 1..1024. No estimate of actual USD cost without vendor billing metadata. UI/server `/api/provider-budget` read-only.
- `coordination/ownership.json` and `coordination/check_ownership.py` enforce mutually exclusive edit paths for 3 chat heads. This is a local verification script, not GitHub server-side protection; HEAD A must enforce in reviews.
- `coordination/MASTER_PROMPT_HEAD_{A,B,C}.md` gives each head an independent, source-backed handoff and explicit boundaries.

## Remaining 13 release gates (NO synthetic shortcut)

See `integration_guard.py` and `docs/VERIFICATION_MATRIX.md` for exact gate meanings and tests. Important blockers: real five-brain inference; independent general intelligence/coding/real-world evaluation; independently qualified market research and forward paper tests; 1000 track curricula; production security; genuine deployment and disaster recovery on target hardware; current SHA CI; separate security/scientific review; actual owner approval; cross-repo schema/replay qualification. `research_only`, `execution_authorized=false`, `production_decision_authorized=false`, `auto_promote=false` always remain.

## Cross-head recovery protocol

1. Pin `reppiks490/builds@agent/myriad-omega-independent-handoff/myriad-omega-v15/`, verify 9+ archive segments and `SOURCE_BUNDLE_INFO.json` exact hashes. Fall back to v1.4 if v1.5 is not yet published; never guess missing files.
2. Run `python -m pytest -q` and `python integration_guard.py --require-ready` (must exit 2 blocked), then inspect `GET /api/provider-budget` and `GET /api/models` without initiating external calls.
3. Start HEAD A/B/C from distinct prompts, each on a distinct GitHub branch; cross-head transfers through issue #1 comments only.
4. Update GitHub versioned handoff and master issue each session with exact SHA/test evidence, not unverified narrative.

## Live loopback verification (2026-11-23)

Started `python server.py --port 8898` with provider-approval variables UNSET. Actual HTTP GET returned `registered_agents=10000`, `live_actor_coroutines=10000`, `healthy=true`; `GET /api/provider-budget` showed `approved=false`, `reserved_today=0`; and `GET /api/models` returned all five `status=budget_blocked`. The server was terminated after inspection. This is NOT evidence of paid model inference, NIMO laptop performance, persistent hosting, or production readiness.