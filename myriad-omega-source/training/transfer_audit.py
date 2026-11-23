"""Evidence-only distribution-shift audit for independently saved neural policies.

Uses frozen agent-specific weights. No gradient updates, synthetic teacher only.
No results qualify general intelligence, market mastery or agent promotion.
"""
from __future__ import annotations
import argparse, hashlib, json, math, time
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import torch
from torch.nn import functional as F
from .individual_weight_bank import WeightBank
from .policy_inference import PolicyInference

TEACHER=torch.tensor([
 [.9,-.7,.4,.0,.3,-.1,.2,.5],[-.4,.7,.5,.3,-.2,.4,0.,.1],
 [.3,.1,-.4,.8,.2,.1,.5,-.3],[.5,-.1,.2,.4,.1,.8,-.2,.6],
 [-.2,.3,.1,.1,.7,-.4,.5,.2],[.4,-.1,.8,-.2,.2,.3,.1,.5],
 [.1,.5,.2,-.3,.6,.2,.3,-.2],[-.4,.2,-.1,.5,.2,.4,.8,.1]],dtype=torch.float32)


def teacher(x:torch.Tensor,agent:int):
    return x[:,:8]@TEACHER + ((agent%97)/97.0-.5)*torch.sin(x[:,8:9]*torch.arange(1,9,dtype=torch.float32))


def audit(bank_dir,*,sample=100,seed=23871,batch=48,shift=2.0):
    if not 1<=sample<=10000 or not 8<=batch<=256 or not 0.5<=shift<=4:
        raise ValueError('Invalid bounded audit budget')
    torch.set_num_threads(1)
    engine=PolicyInference(Path(bank_dir),fleet=10000,cache_size=1)
    # Stratified across all 100 workflow groups for a sample of 100.
    ids=[(i*10000)//sample+1 for i in range(sample)]
    rows=[];start=time.monotonic()
    for agent in ids:
        sha,steps=engine._sha(agent)
        g=torch.Generator().manual_seed(seed + agent*117)
        x=torch.randn((batch,32),generator=g)
        target=teacher(x,agent)
        x_shift=x+shift
        target_shift=teacher(x_shift,agent)
        # Model loader verifies stored weights against the ledger SHA.
        with engine.lock:
            model=engine._model(agent,sha)
            with torch.inference_mode():
                p=model(x); q=model(x_shift)
                id_loss=float(F.mse_loss(p,target))
                ood_loss=float(F.mse_loss(q,target_shift))
                zero_loss=float(F.mse_loss(torch.zeros_like(target),target))
                ood_zero_loss=float(F.mse_loss(torch.zeros_like(target_shift),target_shift))
        rows.append({'agent':f'AG-{agent:05d}','sha256':sha,'steps':steps,
                     'in_distribution_mse':id_loss,'shifted_mse':ood_loss,
                     'in_distribution_zero_baseline_mse':zero_loss,
                     'shifted_zero_baseline_mse':ood_zero_loss,
                     'shifted_better_than_zero_baseline':ood_loss<ood_zero_loss})
    def mean(name):return round(sum(r[name] for r in rows)/len(rows),6)
    evidence={'schema':'myriad.synthetic_transfer_audit.v1',
       'generated_utc':datetime.now(timezone.utc).isoformat(timespec='seconds'),
       'trained_models_sampled':sample,'sampled_workflows':len({int(r['agent'][3:])//100 for r in rows}),
       'examples_per_distribution_per_agent':batch,'heldout_seed':seed,'covariate_shift':shift,
       'source_checkpoint_type':'411k independently owned trained FP16 policy networks',
       'weights_modified':False,'distribution_type':'synthetic Gaussian x and shifted Gaussian x+shift',
       'teacher_type':'known synthetic regression teacher; NOT independent real-world ground truth',
       'mean_id_mse':mean('in_distribution_mse'),'mean_shifted_mse':mean('shifted_mse'),
       'mean_id_zero_baseline_mse':mean('in_distribution_zero_baseline_mse'),
       'mean_shifted_zero_baseline_mse':mean('shifted_zero_baseline_mse'),
       'shifted_beats_zero_baseline_count':sum(int(r['shifted_better_than_zero_baseline']) for r in rows),
       'real_world_skills_certified':0,'trading_edge_certified':False,'weights_sha256_rows':rows,
       'elapsed_seconds':round(time.monotonic()-start,2)}
    digest=hashlib.sha256(json.dumps(evidence,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    evidence['evidence_sha256']=digest
    return evidence


def main():
    p=argparse.ArgumentParser();p.add_argument('--bank-dir',type=Path,default=Path(__file__).parent/'agentbank')
    p.add_argument('--sample',type=int,default=100);p.add_argument('--seed',type=int,default=23871)
    p.add_argument('--out',type=Path);a=p.parse_args()
    result=audit(a.bank_dir,sample=a.sample,seed=a.seed)
    if a.out:a.out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in result.items() if k!='weights_sha256_rows'},indent=2))
if __name__=='__main__':main()
