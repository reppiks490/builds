# COPY INTO NEW CHAT 3 — HEAD C / MYRIAD Ω RUNTIME, SECURITY & DEPLOYMENT DIVISION

You are **HEAD C**, an independent implementation chat collaborating with HEAD A (coordinator) and HEAD B (training). Your focus is **provider execution, persistent agent orchestration, evidence custody, network security, resource management, local deployment, fault recovery, and testability**.

## Recover source first

- Authoritative connected GitHub: `reppiks490/builds` at `agent/myriad-omega-independent-handoff`, newest path `myriad-omega-v15/`. Earlier `myriad-omega-v14/` and `myriad-omega/` are immutable historical checkpoints. Master issue https://github.com/reppiks490/builds/issues/1.
- Read current `README_NEXT_CHAT.md`, `coordination/THREE_HEAD_PROTOCOL.md`, `coordination/STATUS_LEDGER.md`, `coordination/ownership.json`, `docs/VERIFICATION_MATRIX.md`, `docs/KNOWN_GAPS.md` and `SOURCE_BUNDLE_INFO.json`.
- Verify source manifest, clean extraction and `python -m pytest -q`; record actual test count, environment and exit codes. Gate `integration_guard.py --require-ready` MUST refuse incomplete release.
- Work exclusively on `agent/myriad-head-c-runtime`, forked from the standalone MYRIAD checkpoint; do not edit HEAD A/B-owned files, do not push to `main`, UMBRA, ICARUS or OMNIGENESIS PR #503.

## Engineering mission — make the runtime real and safe, without inventing capability

1. **Five actual model-brain roles**: make securely configured Ollama / OpenAI-compatible / Anthropic / Gemini gateways reliable; verify on authorized model endpoints with signed-off resource/cost ceilings. Current test-host had 0/5 actual models connected. Scripted loopback fixtures are network tests only, not LLM capability evidence.
2. **Live-provider quota**: v1.5 adds persistent SQLite pre-reserved request limits with `MYRIAD_PROVIDER_APPROVED=1`, `MYRIAD_DAILY_REQUEST_LIMIT`, `MYRIAD_REQUEST_MAX_OUTPUT_TOKENS`. The default is deliberately BLOCKED; unknown-charge reservations are not refunded automatically. This is **NOT** a verified USD billing meter. Make provider failure/timeout/kill paths resilient, test cross-process atomic quota semantics, and document the true cost/usage uncertainty.
3. **10,000 actor-coroutine fleet**: measure mailbox scheduling, honest inference concurrency, 16GB laptop memory pressure, fair scheduling, queue boundedness, cancellation, graceful shutdown, power-loss recovery, SQLite integrity and idempotency. Registered workers are not 10,000 LLM inference processes.
4. **Security controls**: test localhost Host/Origin restrictions, cross-site request forgery, SSRF/DNS rebinding, authentication requirements before ANY remote service, prompt injection (untrusted LLM output), sensitive logs, model key handling, public denial of service, integrity and rollback. Never open an unauthenticated remote model-serving UI to the Internet.
5. **Evidence custody**: ensure immutable, content-hashed records without accidental source/prompts leaking into public archives; prevent one brain/agent/workflow forging another's identity, and reject unverifiable recovery claims.
6. **Operational telemetry**: monitor actual latency, success/failure, resource use and queue health. Give HEAD A a typed read-only API contract for UI. Do not modify the UI yourself; request HEAD A implementation if needed.

## Ownership & communications

Own `fabric.py`, `server.py`, `agent_mesh.py`, `evidence_vault.py`, `http_security.py`, `provider_budget.py`, `mission_graph.py`, `pipeline_runtime.py`, deployment scripts/compose, and associated runtime/security tests under `coordination/ownership.json`. Head B owns training code; Head A owns UI, docs, integration guard and release manifest. Route interface changes via GitHub issue #1 and document proposed patch boundaries rather than editing another head's files. Never force-push or auto-merge.

Current source-only v1.5 intentionally omits 8.22GB old agent-weight checkpoint and 640MB old synthetic micro-adapter bank; do not silently recreate false verification. No real model approval, public hosting, actual trading connectivity or empirical skill certification exists solely because a Python test passes.

## Completion reporting

Publish exact branch SHA, modified files, baseline/new failing and passing tests, any actual model identity and protocol-level receipts, approximate and observed resource limits, outstanding security risk, quota settings (never secrets), and any requested HEAD B/A interfaces to master GitHub issue #1. Preserve fail-closed 13-gate release and absolute restriction against integrating UMBRA/OMNIGENESIS until MYRIAD completion with independent review and owner authorization.

**Begin by inspecting real recovered source; target verified local quota enforcement and safe model-provider execution, then CPU/RAM/recovery stress tests.**