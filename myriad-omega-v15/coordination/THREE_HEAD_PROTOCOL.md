# MYRIAD Ω — Three-chat-head collaboration, ownership, release authority

**Status: design and test infrastructure; no chat heads are automatically spawned or kept running.** The user must open three separate conversations and paste their prompts. These are independent engineering sessions, not additional MYRIAD model brains.

## Roles and branches

| Chat | Role | Branch | Authorized owned paths |
| --- | --- | --- | --- |
| HEAD A | Coordinator, design, UI, 13-gate release, source publication | `agent/myriad-head-a-coordination` | `coordination/**`, `docs/**`, `assets/**`, `index.html`, registries, release guards, packaging, CI |
| HEAD B | Neural weight training, 1,000 curriculum tracks, external ability evaluation | `agent/myriad-head-b-training` | `training/**`, `mastery.py`, `assessment.py`, owned tests |
| HEAD C | Five-brain model runtime, 10k worker scheduling, security, deployment | `agent/myriad-head-c-runtime` | `fabric.py`, `server.py`, `provider_budget.py`, `agent_mesh.py`, evidence vault, owned tests |

Exact matching patterns, including edge cases, are in `coordination/ownership.json`. Validate with `python coordination/check_ownership.py --head HEAD_B --files training/independent_eval.py` or `--git-base <pinned_base_commit>`. **Do not interpret a passed ownership test as a security audit.**

## Single source of truth, no cross-chat implicit memory

- Repository `reppiks490/builds`; working **source branch** `agent/myriad-omega-independent-handoff` stores immutable historical directories `myriad-omega/` (v1.3), `myriad-omega-v14/` (v1.4), and `myriad-omega-v15/` (v1.5). They are NOT merged into `main`.
- Master coordination issue: https://github.com/reppiks490/builds/issues/1. Every head posts status updates as comments and links to code commits/PRs.
- Three heads must independently retrieve exactly the same SHA from the same archive; copy SHA and archive hash into each issue update. Never assume another chat sees your work until posted.
- Do not edit another head's source path. For cross-head interface changes, write an exact request (signature/schema and expected test) on the issue; owning head implements.
- HEAD A alone composes the integration candidate in the ISOLATED MYRIAD branch after reviews/tests. HEAD A does **not** overrule independent safety/scientific review or owner approval.
- If a branch head advances while another head is reading it, pin review by SHA and ask owner of that branch for updated diffs. No force-push.

## Checkpoints and acceptance protocol

For every change provide (1) task/issue, (2) source and base SHAs, (3) own branch, (4) modified paths, (5) exact commands and stdout/exit code, (6) external API/network calls and costs, (7) material claims labeled with evidence tier, (8) regressions and security risks, (9) proposed follow-ups.

Development quality gates: syntax and unit tests; non-regression against baseline; recovery from source SHA; bounded resource profiles; consent before spending; no secrets in logs/artifacts; independent review by a head that did not author the code. None of these alone constitutes 13/13 release approval.

Merge protocol inside MYRIAD: HEAD B or C propose changes on their own branch, HEAD A retrieves exact commits, verifies ownership and tests, performs reviewed fast-forward/cherry-pick or manually reconciles into new development branch **without rewriting their branch**, reruns clean CI, and updates the source bundle. Never merge another head's development branch blindly. If unable to safely bring commits together, leave independent branches and issue comments intact.

**Only after all 13 independently witnessed MYRIAD gates pass**: prepare UMBRA and OMNIGENESIS read-only adapter proposals on *new review branches*, pin external SHAs, run their complete cross-project regression and security gates; request explicit owner approval before merging into either `main`. Never bypass OMNIGENESIS research-only controls, federated peer freshness, or independently reviewed scientific qualification.

## Mandatory truth labels

`defined` → `implemented` → `local_tested` → `neural_weight_updated_synthetic` → `real_model_inference_tested` → `independent_task_qualified` → `production_approved`. An earlier label is never evidence of a later one. Ten million 32-parameter synthetic adapters are not ten million expertly mastered real-world abilities. Ten thousand actor coroutines are not ten thousand concurrent LLM generations. A source ZIP without weight banks is not a fully deployed model fleet.

## No ongoing invisible execution

These chats cannot perform indefinite unsupervised work merely by being named worker heads. Use GitHub issue receipts as durable communications, and explicit user-approved non-Codex schedules only if concrete infrastructure and cost ceilings exist. Preserve all failures and unfinished tasks for the next session.