> **v1.0 hardware note:** The full 411k-per-agent weight bank requires 8.22 GB of persistent disk. Training is sequential on CPU; a 16 GB RAM laptop cannot simultaneously execute 10,000 LLM inference streams. Use `training/train_full_10000_windows.ps1`, then `training/verify_local_training_windows.ps1`. See `BUILD_STATUS_v1.md` for caveats. Source ZIP does not contain checkpoint bytes.

# MYRIAD Ω — 10,000-worker deployment guide

The project operates as one Python service running 10,000 separately scheduled asyncio **worker coroutines**, divided into 100 workflows of 100 actors. Its five shared model routes provide on-demand intelligence. This is **not** 10,000 model processes, physical servers, or GPU reservations. All 10,000 can receive work independently, but only 2 mission pipelines may infer concurrently by default. In production, external actions are disabled.

## 1. Windows PC — recommended

1. Extract the ZIP into an ordinary directory and install Python 3.10 or newer.
2. Open PowerShell in that directory and execute:

   ```powershell
   .\deploy_10000_windows.ps1 -ProvisionModels
   ```

   This checks hardware, selects `lite` / `balanced` / `pro`, explicitly installs Ollama if absent via winget, downloads one Qwen3.5 model, certifies that all 10,000 separate actors execute tasks, starts the Ollama server when required and runs MYRIAD. Installing model weights can download multiple GB. Verify available disk and be aware that running models consumes CPU/GPU/RAM.
3. Open **http://127.0.0.1:8788** in the same PC's browser.
4. Look for **10,000 / 10,000 DEPLOYED ACTOR WORKERS** and **3 / 3 MODEL ROUTES READY**. These are independent checks. If 3/3 is not ready, verify the Ollama app and model tag with `ollama list`, and check `http://127.0.0.1:11434/api/tags`.

For workers **without model downloads**, run:

```powershell
.\deploy_10000_windows.ps1
```

For certification only, run `./deploy_10000_windows.ps1 -CertifyOnly`. The script is not remotely executed by ChatGPT; run it on the target Windows computer.

## 2. Docker Compose — local-only, isolated Ollama

Prerequisites: Docker Engine / Docker Desktop, adequate disk/RAM, supported architecture.

```bash
docker compose up -d --build
docker compose exec ollama ollama pull qwen3.5:4b
```

The first command starts an isolated Ollama model server and the 10,000-actor MYRIAD service. The second explicitly downloads the model (multiple GB). Check:

```bash
curl -s http://127.0.0.1:8788/api/health
curl -s http://127.0.0.1:8788/api/fleet
```

The MYRIAD HTTP port is published **only on the host's loopback interface**, and the Ollama port is **not published**. MYRIAD trusts HTTP to the literal Docker service hostname `ollama` only when explicitly configured. Do not make the UI accessible on the Internet without TLS, authentication, authorization, CSRF protections and a hardened reverse proxy. Container images must be reviewed and pinned by digest for production supply-chain controls.

**Note:** Docker itself and the model weights were not installed in the sandbox used to generate this package; the Compose configuration is provided but a real Docker image build has not been verified here.

## 3. Fleet certification

```bash
python certify_fleet.py
python -m pytest -q tests
```

`certify_fleet.py` creates 10,000 actors, sends one **local non-LLM task to each**, and verifies 10,000 distinct acknowledgements. It records a roster hash, per-workflow counts, elapsed time, and truthful `llm_calls: 0`. The test does not require Ollama or an API key.

## 4. Model routes and resource limits

Each submitted mission invokes NOESIS -> PRAXIS -> AEGIS in sequence. All three can share Qwen3.5 (different instructions) or use separate providers configured with OS environment variables. Model provider keys must not be committed. **Do not** increase model concurrency until RAM/VRAM, throughput, rates, and spending are measured.

The initial default **2** simultaneous five-brain mission pipelines, not 10,000. The separate actor fleet costs little idle CPU; intelligent inference incurs model-serving resource consumption and may incur paid API fees. The 40,000 pupil slots are metadata and have not been fine-tuned or deployed as active agents.

## 5. GitHub and remote deployment

The `fleet-ci.yml` workflow can re-run the 10,000-actor test and preserve a certification artifact whenever this **standalone** repository is pushed to GitHub. It does not authorize GitHub to execute external trading or write to the user's other projects.

A persistent cloud fleet **has not been provisioned**. This package contains the complete local single-host runtime; durable remote deployment requires an independently identified repository and authorized hosting credentials/cost controls. The user's other repositories and Railway projects are left untouched.
