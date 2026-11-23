"""Predeclared distribution-shift gauntlet for frozen synthetic agent policies.

The benchmark evaluates the already-trained 411k networks on synthetic tasks
without weight updates. It is not a general-intelligence/trading certification.
"""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
import argparse, hashlib, json, math, statistics, time
import torch
from torch.nn import functional as F
from .policy_inference import PolicyInference
from .transfer_audit import teacher

SCENARIOS=('in_distribution','covariate_shift','feature_dropout','measurement_noise')


def gauntlet(bank_dir,*,sample=100,seed=29413,batch=40):
    if not isinstance(sample,int) or not 1<=sample<=1000 or not isinstance(batch,int) or not 16<=batch<=128:
        raise ValueError('Bounded evaluation requires sample 1..1000 and batch 16..128')
    torch.set_num_threads(1)
    engine=PolicyInference(Path(bank_dir),fleet=10000,cache_size=1)
    ids=[(i*10000)//sample+1 for i in range(sample)]
    results=[];start=time.monotonic()
    for agent in ids:
        digest,steps=engine._sha(agent)
        g=torch.Generator().manual_seed(seed+agent*31)
        inputs=torch.randn(batch,32,generator=g)
        shifted=inputs+2.0
        dropped=inputs.clone();dropped[:,::4]=0
        noisy=inputs+.45*torch.randn(batch,32,generator=g)
        scenarios={'in_distribution':inputs,'covariate_shift':shifted,
                   'feature_dropout':dropped,'measurement_noise':noisy}
        row={'agent_id':f'AG-{agent:05d}','workflow_id':f'W{(agent-1)//100+1:02d}',
             'weight_sha256':digest,'recorded_steps':steps,'metrics':{}}
        with engine.lock:
            model=engine._model(agent,digest)  # Full byte SHA checked on every load.
            with torch.inference_mode():
                for name,x in scenarios.items():
                    target=teacher(x,agent)
                    mse=float(F.mse_loss(model(x),target))
                    baseline=float(F.mse_loss(torch.zeros_like(target),target))
                    if not math.isfinite(mse) or not math.isfinite(baseline):
                        raise ValueError('Invalid model/evaluation numerical result')
                    row['metrics'][name]={'mse':round(mse,6),'zero_baseline_mse':round(baseline,6),
                                          'beats_zero_baseline':mse<baseline}
        results.append(row)
    stats={}
    for scenario in SCENARIOS:
        losses=[r['metrics'][scenario]['mse'] for r in results]
        sorted_losses=sorted(losses)
        stats[scenario]={'mean_mse':round(statistics.mean(losses),6),
                         'p95_mse':round(sorted_losses[max(0,math.ceil(len(losses)*.95)-1)],6),
                         'beats_zero_baseline':sum(r['metrics'][scenario]['beats_zero_baseline'] for r in results),
                         'models_evaluated':len(results)}
    outcome={'schema':'myriad.robustness_gauntlet.v1','generated_utc':datetime.now(timezone.utc).isoformat(timespec='seconds'),
       'sampled_agent_count':len(results),'covered_workflows':len({r['workflow_id'] for r in results}),
       'samples_per_scenario':batch,'seed':seed,'predeclared_scenarios':list(SCENARIOS),
       'model_weights_modified':False,'provenance':'frozen locally stored policy weights; synthetic teacher',
       'measurements':stats,'results':results,
       'independent_real_world_certifications':0,'profitable_trading_claims':False,
       'general_intelligence_claims':False,'auto_promotion_authorized':False,
       'elapsed_seconds':round(time.monotonic()-start,2)}
    serial=json.dumps(outcome,sort_keys=True,separators=(',',':'),allow_nan=False)
    outcome['content_sha256']=hashlib.sha256(serial.encode()).hexdigest()
    return outcome


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bank-dir',type=Path,default=Path(__file__).parent/'agentbank')
    p.add_argument('--sample',type=int,default=100)
    p.add_argument('--batch',type=int,default=40)
    p.add_argument('--seed',type=int,default=29413)
    p.add_argument('--out',type=Path)
    a=p.parse_args()
    r=gauntlet(a.bank_dir,sample=a.sample,batch=a.batch,seed=a.seed)
    if a.out:a.out.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in r.items() if k!='results'},indent=2))
if __name__=='__main__':main()
