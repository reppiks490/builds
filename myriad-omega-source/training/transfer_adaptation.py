"""Quarantined domain-shift curriculum for independently trained policy agents.

REAL autograd applies only to separate candidate copies; the immutable baseline
fleet is never modified here. The synthetic teacher is not real-world truth.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, math, os, time
from pathlib import Path
import numpy as np
import torch
from torch import nn
from torch.nn.utils import parameters_to_vector, vector_to_parameters
from .individual_weight_bank import PARAMETERS
from .policy_inference import PolicyInference
from .transfer_audit import teacher


def examples(agent,seed,n=32):
    g=torch.Generator().manual_seed(seed+agent*17011)
    x=torch.randn((n,32),generator=g)
    xs=x+2
    xn=x+.45*torch.randn((n,32),generator=g)
    return {'normal':(x,teacher(x,agent)),'shifted':(xs,teacher(xs,agent)),
            'noisy':(xn,teacher(xn,agent))}


def mse(model,points):
    model.eval()
    with torch.inference_mode():return {k:float(nn.functional.mse_loss(model(x),y)) for k,(x,y) in points.items()}


def train_candidate(agent,bank_dir,out_dir,*,steps=12,batch=32,lr=.0005,seed=8921):
    if type(agent) is not int or not 1<=agent<=10000:raise ValueError('Agent must be 1..10000')
    if not 1<=steps<=60 or not 16<=batch<=96 or not 0<lr<=.002:raise ValueError('Unsafe candidate training budget')
    torch.set_num_threads(1)
    out_dir=Path(out_dir);out_dir.mkdir(parents=True,exist_ok=True)
    # Never re-write a finished candidate implicitly. Explicitly version by ID/seed.
    filename=f'AG-{agent:05d}-S{seed}-E{steps}.fp16'
    final=out_dir/filename
    if final.exists():raise FileExistsError('Candidate already exists; no silent overwrite')
    engine=PolicyInference(Path(bank_dir),fleet=10000,cache_size=1)
    source_sha,_=engine._sha(agent)
    with engine.lock:base=copy.deepcopy(engine._model(agent,source_sha))
    candidate=copy.deepcopy(base)
    train=examples(agent,seed,batch)
    holdout=examples(agent,seed+109991,max(24,batch))
    before=mse(base,holdout)
    opt=torch.optim.AdamW(candidate.parameters(),lr=lr,weight_decay=0.)
    for _ in range(steps):
        candidate.train();opt.zero_grad(set_to_none=True)
        # Weighted curriculum: general competence is explicitly retained.
        loss=sum(w*nn.functional.mse_loss(candidate(train[k][0]),train[k][1])
                 for k,w in [('normal',.3),('shifted',.5),('noisy',.2)])
        loss.backward();torch.nn.utils.clip_grad_norm_(candidate.parameters(),1.);opt.step()
    # Evaluate the exact quantized FP16 weights that are persisted, never a
    # higher-precision pre-serialization model. This avoids false promotions.
    flat=parameters_to_vector(candidate.parameters()).detach().numpy().astype('<f2')
    persisted=copy.deepcopy(base)
    vector_to_parameters(torch.from_numpy(flat.astype(np.float32).copy()),persisted.parameters())
    after=mse(persisted,holdout)
    if not all(math.isfinite(v) for v in (*before.values(),*after.values())):
        raise RuntimeError('Non-finite validation refused')
    digest=hashlib.sha256(flat.tobytes()).hexdigest()
    if flat.size!=PARAMETERS or digest==source_sha:raise RuntimeError('No new independent model weights')
    # No model promotion. The status only describes synthetic holdout outcomes.
    passing=after['shifted']<before['shifted'] and after['normal']<=before['normal']*1.20 and after['noisy']<=before['noisy']*1.20
    tmp=final.with_suffix('.pending')
    with tmp.open('wb') as f:f.write(flat.tobytes());f.flush();os.fsync(f.fileno())
    os.replace(tmp,final)
    # Keep the baseline checkpoint unchanged; verified before each candidate load.
    info={'agent':f'AG-{agent:05d}','source_sha256':source_sha,'candidate_sha256':digest,
          'steps':steps,'training_seed':seed,'scenario_holdout_loss_before':before,
          'scenario_holdout_loss_after':after,'synthetic_gate_passed':bool(passing),
          'checkpoint':filename,'parameters_per_candidate':PARAMETERS,
          'evaluation_type':'known synthetic teacher, independent holdout seed',
          'real_world_qualified':False,'auto_promote':False,'bank_overwritten':False}
    receipt=out_dir/f'{filename}.json'
    staged=receipt.with_suffix('.pending')
    with staged.open('w',encoding='utf8') as f:
        f.write(json.dumps(info,indent=2,sort_keys=True)+'\n')
        f.flush();os.fsync(f.fileno())
    os.replace(staged,receipt)
    return info


def audit_candidates(folder):
    """Fail closed for orphan weights, forged certificates or invalid reports."""
    folder=Path(folder)
    reports=sorted(folder.glob('AG-*.fp16.json'))
    weights={p.name for p in folder.glob('AG-*.fp16')}
    pending={p.name for p in folder.glob('AG-*.pending')}
    bad=list(sorted(pending));results=[];referenced=set();seen=set()
    for report in reports:
        try:
            doc=json.loads(report.read_text(encoding='utf8'))
            name=doc['checkpoint']
            agent=doc['agent']
            if (not isinstance(name,str) or name!=report.name.removesuffix('.json')
                or not isinstance(agent,str) or not agent.startswith('AG-')
                or len(agent)!=8 or not agent[3:].isdigit() or not 1<=int(agent[3:])<=10000
                or not name.startswith(agent+'-S') or name in seen):
                raise ValueError('Unbound or duplicate candidate identity')
            seen.add(name);referenced.add(name)
            path=folder/name
            if (not path.is_file() or path.stat().st_size!=PARAMETERS*2
                or hashlib.sha256(path.read_bytes()).hexdigest()!=doc['candidate_sha256']):
                raise ValueError('Candidate bytes absent or tampered')
            if doc['auto_promote'] is not False or doc['real_world_qualified'] is not False:
                raise ValueError('Unauthorized qualification or promotion')
            if type(doc['steps']) is not int or not 1<=doc['steps']<=60:
                raise ValueError('Invalid training step count')
            before=doc['scenario_holdout_loss_before'];after=doc['scenario_holdout_loss_after']
            if not all(type(z) in (float,int) and math.isfinite(z) and z>=0
                       for k in ('normal','shifted','noisy') for z in (before[k],after[k])):
                raise ValueError('Non-finite loss in report')
            computed=(after['shifted']<before['shifted'] and
                      after['normal']<=before['normal']*1.20 and
                      after['noisy']<=before['noisy']*1.20)
            if doc['synthetic_gate_passed'] is not computed:
                raise ValueError('Forged synthetic pass flag')
            results.append(doc)
        except (OSError,KeyError,TypeError,ValueError,json.JSONDecodeError) as exc:
            bad.append(report.name)
    bad.extend(sorted(weights-referenced))
    pass_count=sum(bool(x['synthetic_gate_passed']) for x in results)
    def mean(key,period):
        return round(sum(r[f'scenario_holdout_loss_{period}'][key] for r in results)/len(results),6) if results else None
    return {'candidates_checked':len(reports),'valid':len(results),'invalid':bad,
           'untracked_weight_files':len(weights-referenced),'all_valid':not bad,
           'synthetic_gate_passed':pass_count,
           'mean_shifted_mse_before':mean('shifted','before'),
           'mean_shifted_mse_after':mean('shifted','after'),
           'mean_normal_mse_before':mean('normal','before'),
           'mean_normal_mse_after':mean('normal','after'),
           'authority':'quarantined_only','real_world_certifications':0,'live_weight_promotions':0}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bank-dir',type=Path,default=Path(__file__).parent/'agentbank')
    p.add_argument('--out-dir',type=Path,default=Path(__file__).parent/'transfer_candidates')
    p.add_argument('--start',type=int,default=1)
    p.add_argument('--count',type=int,default=1)
    p.add_argument('--steps',type=int,default=12)
    p.add_argument('--seed',type=int,default=8921)
    args=p.parse_args()
    if args.start<1 or args.count<1 or args.start+args.count-1>10000:raise SystemExit('Invalid candidate range')
    start=time.monotonic()
    for a in range(args.start,args.start+args.count):
        result=train_candidate(a,args.bank_dir,args.out_dir,steps=args.steps,seed=args.seed)
        if (a-args.start+1)%10==0 or a==args.start+args.count-1:
            print(json.dumps({'processed':a-args.start+1,'last':a,'synthetic_gate_passed':result['synthetic_gate_passed'],'seconds':round(time.monotonic()-start,2)}),flush=True)
    print(json.dumps(audit_candidates(args.out_dir),indent=2))
if __name__=='__main__':main()
