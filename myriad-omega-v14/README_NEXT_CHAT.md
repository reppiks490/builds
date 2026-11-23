# MYRIAD Ω — START HERE (v1.4 isolated handoff)

**Release status: BLOCKED. DO NOT MERGE UMBRA OR ICARUS.** This is the exact MYRIAD recovery index requested for future chats.

Read these in order:
1. `docs/PHASE_V14.md` — latest changes, exact tests, private evaluation controls and current release locks.
2. `docs/AGENT_HANDOFF.md` — user directives, source locations, actual status, target PR, exact continuation instructions.
3. `docs/VERIFICATION_MATRIX.md` — 13 release gates (only 3 previously passed).
4. `docs/REPRODUCE_AND_OPERATE.md` — safe source unpack, tests, model setup and repair.
5. `docs/KNOWN_GAPS.md` — what remains blocked and why.
6. `docs/NEXT_CHAT_PROMPT.md` — copy-ready new-chat context.
7. `SOURCE_MANIFEST.json` — file-level SHA256 of source snapshot.
8. GitHub `SOURCE_BUNDLE.tar.gz.b64.partNN` and `SOURCE_BUNDLE_INFO.json` — concatenated base64 source archive, includes complete readable source, tests, docs but intentionally NO heavy model weights or credentials.

**Core constraints:** 10k agents with independently owned 411k tiny neural policy weights; 10M 32-parameter synthetic ability micro-adapters; 5 brains/100 workflows/1000 pipelines/10 tiers, etc. No demonstrated AGI, trading edge or persistent live deployment. All candidates quarantined and no auto-promotion. See hard constraints in the detailed handoff.

**Current reference GitHub branch:** `reppiks490/builds@agent/myriad-omega-independent-handoff`; path `myriad-omega`. No modifications to the UMBRA or ICARUS repositories have been authorized before completion.

**Latest v1.4:** 77 passing unit tests, 3 expected skips in source-only copy; sealed holdout benchmark and no-redirect provider transport added. No real model calls recorded; gate remains blocked. GitHub `myriad-omega-v14/` carries the v1.4 archive; the original `myriad-omega/` folder preserves v1.3.