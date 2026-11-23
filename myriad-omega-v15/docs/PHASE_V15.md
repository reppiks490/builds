# MYRIAD Ω v1.5 — PENTARCH provider budget and three-head continuity

**Date:** 2026-11-23. **Release:** research-only, integration blocked; no live model/server deployment or paid provider use has been authorized or observed.

## What was actually changed

### 1. Persisted inference-request budget, deny-by-default

- `provider_budget.py` contains `ProviderBudget` and `BudgetedGateway`. The real local command-center server now wraps its Ollama/OpenAI-compatible/Anthropic/Gemini gateway with a SQLite preflight quota; requests must reserve capacity *before* HTTP. The same ledger is also used by the optional independent-evaluation CLI, which additionally requires its `--allow-provider-calls` flag.
- Operator must **explicitly** configure `MYRIAD_PROVIDER_APPROVED=1`, `MYRIAD_DAILY_REQUEST_LIMIT` in `[1,1000]`, and `MYRIAD_REQUEST_MAX_OUTPUT_TOKENS` in `[1,1024]`. Absent or malformed settings block paid OR local inference (model listing remains blocked before approval (no provider GET requests)), and `/api/models` will report `budget_blocked` for a reachable provider rather than promising an executable route.
- `GET /api/provider-budget` summarizes allowed/day, reserved/day, remaining/day, and outcome categories. It contains no API keys or prompts. SQLite retains only request, model and response **hashes**; no raw prompts, full URLs, secret-bearing headers, or response content are written to the budget ledger.
- Reservations are **never refunded automatically**, even if an external service times out, raises an exception, process dies, or local network fails. This prevents a retry storm from silently exceeding a nominal request limit. The ledger is SQLite serializable via `BEGIN IMMEDIATE` and tested with concurrent calls.
- **It is NOT a monetary meter**, a reliable upper bound on total input tokens, billed USD, vendor compute usage, or downstream billing. Actual charges require provider reports. It also does not by itself prevent the server from receiving malicious requests; remote deployment still requires real auth, TLS, rate-limits, and review.

### 2. Three-chat-head master succession

- `coordination/MASTER_PROMPT_HEAD_A.md`: coordinating architect, UI, registry, release guard, docs, parent integration (but no UMBRA/ICARUS changes before MYRIAD completion).
- `coordination/MASTER_PROMPT_HEAD_B.md`: actual neural learning, dataset provenance and unbiased general-intelligence, trading, real-world qualification.
- `coordination/MASTER_PROMPT_HEAD_C.md`: five-brain inference, 10k actor runtime, resource/cost budgets, security and recovery.
- `coordination/THREE_HEAD_PROTOCOL.md`: exact communication and review protocol via `reppiks490/builds` issue #1. Three heads represent **three independent ChatGPT conversations**, not additional model brains or background jobs.
- `coordination/ownership.json` plus `coordination/check_ownership.py`: nonoverlapping code ownership checks and explicit branches. This is a local governance tool; it does not install branch protection or authorize any merge. Every head must work in its own branch and use PRs/issues for cross-head interface requests.

### 3. Completion truth and retention

- v1.4 source-only regression baseline: **77 passed, 3 skipped**. v1.5 clean reconstructed source passes **87 passed, 3 skipped**, release guard exits **2 BLOCKED, 1/13**. Exact source checksum and archive segment count are recorded in the adjacent `SOURCE_BUNDLE_INFO.json`, not copied into the package recursively.
- Prior 10k×411k full agent weight bank and 10M×32 independent micro-adapter bank exist only as **earlier local checkpoint claims and audits**; they are not in the portable GitHub source. No 10M real mastery certificate, independent general intelligence, empirical trading profit, or reliable all-day 16GB laptop deployment has been certified.
- Five actual model routes were offline/unconfigured on the previous source-only host. **No new real-model inference or provider spending** is performed as part of this release.
- Integration remains **0 authorized merges**: do not modify `reppiks490/umbra-sovereign-worlds` or `reppiks490/Icarus` OMNIGENESIS PR #503 until independent MYRIAD 13/13 gate certification, reviewed compatibility and explicit owner permission.

## Startup on an authorized development host

```bash
python -m pip install -r training/requirements.txt pytest
python -m pytest -q
python integration_guard.py --require-ready       # must return BLOCKED (exit 2)
python server.py                                  # local-only; 127.0.0.1:8788
```

Real model execution **is disabled by default** even after a model server becomes reachable. For an operator-controlled local nonpaid Ollama endpoint or reviewed paid provider, set a short, conservative budget BEFORE launching the server:

```bash
export MYRIAD_PROVIDER_APPROVED=1
export MYRIAD_DAILY_REQUEST_LIMIT=10
export MYRIAD_REQUEST_MAX_OUTPUT_TOKENS=650
python server.py
```

On Windows PowerShell use `$env:MYRIAD_PROVIDER_APPROVED='1'` etc. The model name, URL, keys and pricing still need independent configuration, validation and authorization. Never put API keys in GitHub or commit a model provider secret. This example is not permission to incur costs.

## Fail-closed release rationale

A request budget improves loss containment but does not certify deployment reliability, independent intelligence, a real trading edge, real market data rights, or production security. The independent 13 gate `integration_guard.py` retains final authority, requires externally witnessed evidence for non-structural gates, and **must stay blocked** until independent reviews and owner approval.

## Additional runtime gate check

The server was started locally with the provider budget unset. All 10,000 actor coroutines reported ready and all FIVE model roles reported `budget_blocked` without external discovery. No paid provider calls were made. The server was terminated after inspection.