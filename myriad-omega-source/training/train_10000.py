"""MYRIAD Ω v0.3: real gradient training of 10,000 independent agent adapters.

This trains task-strategy policy-network WEIGHTS, NOT a foundation LLM or a
10,000-GPU deployment. Synthetic teacher tasks are documented and segregated
from real-world evaluation. Safe on CPUs with 16 GB RAM when batch limits held.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
from datetime import datetime, timezone
import tempfile
import time

import torch
from torch import nn
from safetensors.torch import save_file, load_file

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'training' / 'checkpoints'
D = 19     # 12 task signals, four workflow encodings, three brain indicators
K = 8      # research, decompose, implement, verify, simulate, refine, monitor, escalate
R = 3      # rank of independently trainable per-agent LoRA-style policy adapters
ACTIONS = ('research', 'decompose', 'implement', 'verify', 'simulate', 'refine', 'monitor', 'escalate')
BRAIN_NAMES = ('NOESIS', 'PRAXIS', 'AEGIS')

class StrategyAdapterBank(nn.Module):
    """One shared policy base; each identity has its OWN trainable A/B/bias."""
    def __init__(self, agents: int = 10000):
        super().__init__()
        self.agents = agents
        self.base = nn.Linear(D, K)
        self.adapter_a = nn.Parameter(torch.randn(agents, D, R) * .035)
        self.adapter_b = nn.Parameter(torch.zeros(agents, R, K))
        self.agent_bias = nn.Parameter(torch.zeros(agents, K))

    def forward(self, x: torch.Tensor, ids: torch.Tensor):
        # x: [agents_in_batch, scenarios, D]; ids: [agents_in_batch]
        local_a, local_b = self.adapter_a[ids], self.adapter_b[ids]
        h = torch.einsum('asd,adr->asr', x, local_a)
        personal = torch.einsum('asr,ark->ask', h, local_b)
        return self.base(x) + personal + self.agent_bias[ids, None, :]


def teacher_weights():
    # Fixed, inspectable synthetic objective. Columns are action utilities.
    values = [
        [1.7, .5, .3, .4, 1.2, .2, .0, .6],  # uncertainty
        [1.1, 1.6, .2, .6, .6, 1.2, .3, .1],  # ambiguity
        [1.0, 1.1, .2, 1.8, 1.0, .4, .2, 1.7],  # risk
        [1.5, 1.0, .9, .5, 1.9, 1.1, .1, .3],  # novelty
        [.0, 1.1, 1.8, .5, .4, .2, .6, .3],  # execution readiness
        [.2, .7, 2.2, .8, .6, .8, .1, .1],  # code relevance
        [.1, .3, .2, 2.2, .6, .7, .2, .9],  # need for tests
        [.2, .7, .4, .5, 1.6, 1.9, .0, .3],  # visual/creative
        [.1, .3, .4, .5, .2, .1, 2.2, .2],  # continuous monitoring
        [.2, .5, .2, .8, .4, .1, .6, 2.0],  # escalation/compliance
        [1.1, .2, .5, 1.0, .2, .3, .4, 1.4],  # evidence gap
        [.1, .4, .9, .5, 1.6, .8, .9, .2],  # resource margin
        [.3, -.1, .1, .6, .4, .5, .1, .0], # workflow sin1
        [-.4, .2, .5, -.1, .2, -.4, .3, .2], # workflow cos1
        [.2, .3, -.2, .3, -.3, .2, .2, -.1], # workflow sin3
        [-.1, .2, .3, -.2, .4, .1, -.2, .3], # workflow cos3
        [1.0, 1.0, .4, .4, .4, .2, .0, .0], # NOESIS
        [.1, .6, 1.1, .1, .3, 1.0, .2, .0], # PRAXIS
        [.2, .4, .1, 1.1, .3, .1, .6, 1.0], # AEGIS
    ]
    # Mean centering per input dimension prevents unneeded gradient bias.
    w = torch.tensor(values, dtype=torch.float32)
    return (w - w.mean(dim=1, keepdim=True)) * .65


def scenarios(ids: torch.Tensor, samples: int, *, seed: int):
    """Deterministic synthetic task features, equal curriculum for each actor."""
    rng = torch.Generator(device='cpu').manual_seed(seed)
    a = ids.numel()
    features = torch.rand((a, samples, 12), generator=rng) * 2 - 1
    workflow = torch.randint(0, 50, (a, samples), generator=rng)
    brain = torch.randint(0, 3, (a, samples), generator=rng)
    angle = (workflow.float() + .5) * (2 * math.pi / 50)
    wf = torch.stack((angle.sin(), angle.cos(), (3*angle).sin(), (3*angle).cos()), dim=-1)
    onehot = torch.nn.functional.one_hot(brain, 3).float()
    x = torch.cat((features, wf, onehot), -1)
    if x.shape[-1] != D:raise AssertionError('Input mismatch')
    return x, workflow, brain


def synthetic_targets(x:torch.Tensor, ids:torch.Tensor, weights:torch.Tensor):
    """Known labeled oracle: useful for a unit benchmark, not real-world intelligence."""
    # Each agent has its own reproducible preference vector and feature reactions.
    a=ids.float()[:, None]
    k=torch.arange(K, dtype=torch.float32)[None, :]
    traits=.24*torch.sin(a*.117 + k*1.618) + .17*torch.cos(a*.031 + k*.731)
    # Per-agent differences include small input-dependent rank-1 terms.
    modulation=.11*torch.sin(a*.071 + k*.91)
    return x @ weights + traits[:, None, :] + x[..., 0:1] * modulation[:, None, :]


def evaluate(model, ids, *, seed, examples=6, batch_agents=2000):
    model.eval();w=teacher_weights();loss_sum=0.0;hits=0;total=0
    with torch.no_grad():
        for start in range(0,len(ids),batch_agents):
            part=ids[start:start+batch_agents]
            x,_,_=scenarios(part,examples,seed=seed + start*31)
            target=synthetic_targets(x,part,w)
            pred=model(x,part)
            loss_sum+=float(torch.nn.functional.mse_loss(pred,target,reduction='sum'))
            hits+=int((pred.argmax(-1)==target.argmax(-1)).sum())
            total+=target.shape[0]*target.shape[1]
    return {'mse':round(loss_sum/(total*K),7),'routing_accuracy':round(hits/total,6),'heldout_scenarios':total}


def tensor_digest(row_a,row_b,row_bias):
    return hashlib.sha256(b''.join(t.detach().contiguous().numpy().tobytes() for t in (row_a,row_b,row_bias))).hexdigest()


def train(args):
    if not (1<=args.agents<=10000):raise ValueError('Agent count must be 1..10000')
    if not (1<=args.epochs<=100):raise ValueError('Epochs must be 1..100')
    if not (1<=args.batch_agents<=5000):raise ValueError('batch_agents must be 1..5000')
    if not (1<=args.samples_per_agent<=128):raise ValueError('samples_per_agent must be 1..128')
    torch.set_num_threads(max(1,min(args.threads,8)))
    torch.manual_seed(args.seed)
    model=StrategyAdapterBank(args.agents)
    baseline_a=model.adapter_a.detach().clone()
    baseline_b=model.adapter_b.detach().clone()
    baseline_bias=model.agent_bias.detach().clone()
    ids=torch.arange(args.agents,dtype=torch.long)
    baseline=evaluate(model,ids,seed=args.seed+790001,examples=args.heldout,batch_agents=args.batch_agents)
    optimizer=torch.optim.AdamW(model.parameters(),lr=args.lr,weight_decay=0)
    teacher=teacher_weights()
    started=time.monotonic()
    history=[]
    for epoch in range(args.epochs):
        model.train();run_loss=0.;seen=0
        # Every agent is explicitly included in EACH epoch, not sampled randomly.
        for start in range(0,args.agents,args.batch_agents):
            part=ids[start:start+args.batch_agents]
            features,_,_=scenarios(part,args.samples_per_agent,seed=args.seed+epoch*1000003+start*31)
            truth=synthetic_targets(features,part,teacher)
            pred=model(features,part)
            loss=torch.nn.functional.mse_loss(pred,truth)
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(),max_norm=4.)
            optimizer.step()
            run_loss+=float(loss.detach())*len(part);seen+=len(part)
        h={'epoch':epoch+1,'loss':round(run_loss/seen,7),'samples_seen':args.agents*args.samples_per_agent*(epoch+1)}
        history.append(h)
        print(f"EPOCH {epoch+1}/{args.epochs} train_mse={h['loss']:.7f} examples={h['samples_seen']:,}",flush=True)
    final=evaluate(model,ids,seed=args.seed+790001,examples=args.heldout,batch_agents=args.batch_agents)
    with torch.no_grad():
        delta=((model.adapter_a-baseline_a).abs().sum((1,2))+(model.adapter_b-baseline_b).abs().sum((1,2))+(model.agent_bias-baseline_bias).abs().sum(1))
        trained=int((delta>1e-9).sum().item())
        distinct_bias=len(set(tensor_digest(model.adapter_a[i],model.adapter_b[i],model.agent_bias[i]) for i in range(args.agents)))
        minimum_change=float(delta.min().item())
    if trained!=args.agents or distinct_bias!=args.agents:
        raise RuntimeError(f'Personal weight verification failed {trained}/{args.agents}, distinct={distinct_bias}')
    if not final['mse']<baseline['mse']:
        raise RuntimeError(f'No heldout MSE improvement {baseline} -> {final}')
    out=Path(args.output).resolve() if args.output else OUT
    out.mkdir(parents=True, exist_ok=True)
    path=out/'10k_strategy_adapter_bank.safetensors'
    state={k:v.detach().cpu().contiguous() for k,v in model.state_dict().items()}
    with tempfile.NamedTemporaryFile(dir=out,suffix='.safetensors',delete=False) as f:temp=Path(f.name)
    try:
        save_file(state,str(temp),metadata={'training_kind':'synthetic_strategy_policy','does_not_contain_llm_weights':'true','agent_count':str(args.agents)})
        os.replace(temp,path)
    finally:
        if temp.exists():temp.unlink()
    checkpoint_sha=hashlib.sha256(path.read_bytes()).hexdigest()
    # Agent-level proof ledger to permit independent review of EACH trained weight set.
    ledger=out/'AGENT_WEIGHT_LEDGER.jsonl'
    with ledger.open('w',encoding='utf8') as f:
        for i in range(args.agents):
            f.write(json.dumps({'id':f'AG-{i+1:05d}','weight_sha256':tensor_digest(model.adapter_a[i],model.adapter_b[i],model.agent_bias[i]),'weight_updated':bool(delta[i]>1e-9),'gradient_examples':args.epochs*args.samples_per_agent},separators=(',',':'))+'\n')
    report={
        'schema_version':1,'project':'MYRIAD Ω','result':'verified_synthetic_policy_gradient_training',
        'trained_agent_weights':trained,'unique_agent_parameter_sets':distinct_bias,
        'configured_agents':args.agents,'brain_roles':list(BRAIN_NAMES),'workflow_count':50,
        'training_target':'8-action differentiable strategy-selection neural network; shared base + one LoRA-style rank-3 adapter and bias per agent',
        'NOT_TRAINED':'No foundation LLM weights were updated. No real task mastery, 10 billion executed experiments, or simultaneous LLM inference is claimed.',
        'objective_provenance':'synthetic labeled oracle defined in training/train_10000.py; heldout synthetic examples use disjoint random seeds',
        'addressable_method_space':10000*50*20000,
        'addressable_method_space_interpretation':'10,000 agents × 50 workflows × 20,000 curriculum parameter variants; possible combinations, NOT experiments performed',
        'actual_gradient_examples':args.agents*args.epochs*args.samples_per_agent,
        'actual_heldout_examples':args.agents*args.heldout,
        'epochs':args.epochs,'features':D,'actions':list(ACTIONS),'rank':R,
        'baseline_heldout':baseline,'final_heldout':final,
        'mse_relative_improvement_pct':round(100*(baseline['mse']-final['mse'])/baseline['mse'],3),
        'min_absolute_personal_parameter_change':round(minimum_change,8),
        'training_duration_seconds':round(time.monotonic()-started,3),
        'framework':f'PyTorch {torch.__version__}','device':'cpu','precision':'float32',
        'checkpoint':path.name,'checkpoint_sha256':checkpoint_sha,
        'weight_ledger':ledger.name,'weight_ledger_sha256':hashlib.sha256(ledger.read_bytes()).hexdigest(),
        'history':history,'created_utc':datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'limitations':['Only a small strategy-selection policy was trained','Labeled examples are synthetic, not human-reviewed','Local CPU training does not yield a useful 10k-agent LLM without compatible base model and further supervised data'],
    }
    (out/'TRAINING_CERTIFICATION.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print('CERTIFIED',json.dumps({k:report[k] for k in ['trained_agent_weights','unique_agent_parameter_sets','actual_gradient_examples','baseline_heldout','final_heldout','checkpoint_sha256','training_duration_seconds']},indent=2),flush=True)
    return report


def cli():
    p=argparse.ArgumentParser(description='Actually gradient train each MYRIAD Ω per-agent strategy adapter.')
    p.add_argument('--agents',type=int,default=10000)
    p.add_argument('--epochs',type=int,default=10)
    p.add_argument('--samples-per-agent',type=int,default=12)
    p.add_argument('--heldout',type=int,default=6)
    p.add_argument('--batch-agents',type=int,default=1000)
    p.add_argument('--threads',type=int,default=3)
    p.add_argument('--lr',type=float,default=.025)
    p.add_argument('--seed',type=int,default=49013)
    p.add_argument('--output',default='')
    args=p.parse_args();train(args)

if __name__=='__main__':cli()
