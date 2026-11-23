# MYRIAD Ω — 10,000 Actor Runtime Resource Baseline (2026-11-23)

**Execution:** Linux x86_64 container in this ChatGPT test host, Python 3.13.5. This was **NOT the user's Windows/NIMO 16GB laptop**, nor a paid/cloud GPU inference session.

**Command:** `cd myriad-omega-source && /usr/bin/time -v python certify_fleet.py`

**Measured results:**

| Observable | Value |
|---|---:|
| In-process event-loop actors started | 10,000/10,000 |
| Unique actor mailbox acknowledgement callbacks | 10,000/10,000 |
| Workflows represented | 100, 100 callbacks each |
| Actor certification internal duration | 0.987 sec |
| End-to-end process elapsed wall clock | 2.39 sec |
| Maximum resident process memory | 153,360 kB (~150 MiB) |
| Reported callback handler errors | 0 |
| LLM inference requests performed | **0** |
| Full 8.22GB weight bank loaded | **No** |
| Model weights separately loaded per actor | **No** |

**Meaning:** This measures the overhead of 10,000 lightweight in-process asyncio actor coroutines and one local callback per worker. It demonstrates that such scheduling is memory-feasible in this specific container. It does **not** demonstrate 10,000 independent large models, powerful simultaneous thought, 10k real model inference sessions, sustained 24/7 uptime, or satisfactory performance on the actual $600 NIMO hardware.

**Limitations:** A single short certification run; no genuine token generation or failure injection under sustained power/thermal throttling; no Windows memory/cpu measurements; no network or disk throughput results; no real-world training or trading evidence. The event-loop actors share a process, a bounded task semaphore and model providers.

**Merge / production restriction:** MYRIAD is standalone, research-only, release BLOCKED 1/13 on source-only snapshot. This proof cannot unlock any release gate that requires external model competence or production-grade recovery. UMBRA and ICARUS OMNIGENESIS PR #503 remain untouched.