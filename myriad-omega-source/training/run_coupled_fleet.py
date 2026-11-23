"""Bounded, restartable AGENT + ABILITY weight-bank curriculum runner.

This trains ability micro-adapters and produces *quarantined* conditioned
411k-param neural candidate checkpoints for individual agents, sequentially.
No asynchronous persistence is promised and no production promotion occurs.
"""
from __future__ import annotations

import argparse
from datetime import datetime,timezone
import json
import os
from pathlib import Path

from .coupled_bank_training import train_coupled_candidate, verify_candidate,ability_range
from .individual_weight_bank import FLEET
from .ability_weight_bank import TOTAL_ABILITIES


def run_range(agent_dir: Path, ability_dir: Path, output: Path,*,
              start: int, end: int, slots: int=1000, steps: int=3,
              samples: int=40, seed: int=2077,
              ability_count: int=TOTAL_ABILITIES,
              approve_training: bool=False) -> dict:
    if not approve_training:
        raise PermissionError('Explicit approval is required for any weight training')
    if type(start) is not int or type(end) is not int or not 1<=start<=end<=FLEET:
        raise ValueError('Invalid agent interval')
    if end-start+1>100:
        raise ValueError('Limit one execution to at most 100 agents; resume in additional batches')
    ability_range(end,slots,available=ability_count)
    agent_dir,ability_dir,output=Path(agent_dir),Path(ability_dir),Path(output)
    if not (agent_dir/'agent_weights.fp16').is_file() or not (agent_dir/'weight_ledger.sqlite3').is_file():
        raise RuntimeError('Missing source agent bank; import/attach first')
    output.mkdir(parents=True,exist_ok=True)
    state={'schema':'myriad.coupled_fleet_progress.v1','start':start,'end':end,
           'slots_per_agent':slots,'new_agent_candidates':0,'existing_verified_candidates':0,
           'new_ability_rows_trained_synthetic':0,'synthetic_holdout_improvement_count':0,
           'last_agent':None,'status':'running','automatic_promotion':False,
           'real_world_skills_certified':0}
    progress=output/'COUPLED_FLEET_PROGRESS.json'
    def save():
        state['updated_utc']=datetime.now(timezone.utc).isoformat(timespec='seconds')
        tmp=progress.with_suffix('.tmp')
        tmp.write_text(json.dumps(state,sort_keys=True,indent=2)+'\n')
        os.replace(tmp,progress)
    save()
    try:
        for agent in range(start,end+1):
            first,last=ability_range(agent,slots,available=ability_count)
            name=f'AG-{agent:05d}-CAP-{first:08d}-{last:08d}-S{seed+agent}-E{steps}.fp16'
            if (output/name).exists() or (output/(name+'.json')).exists():
                # Never skip an orphan or corrupted previously produced candidate.
                verified=verify_candidate(output,name+'.json',agent_dir,ability_dir,ability_count=ability_count)
                if not verified['valid']:raise RuntimeError('Stored candidate is invalid')
                state['existing_verified_candidates']+=1
            else:
                receipt=train_coupled_candidate(agent,agent_dir,ability_dir,output,
                         slots=slots,steps=steps,samples=samples,seed=seed+agent,
                         ability_count=ability_count,approve_ability_training=True)
                verified=verify_candidate(output,name+'.json',agent_dir,ability_dir,ability_count=ability_count)
                if not verified['valid']:raise RuntimeError('New candidate audit failed')
                state['new_agent_candidates']+=1
                state['new_ability_rows_trained_synthetic']+=receipt['new_ability_rows_trained_synthetic']
                state['synthetic_holdout_improvement_count']+=int(receipt['synthetic_holdout_improved'])
            state['last_agent']=agent
            save()
        state['status']='completed_quarantined_training_only'
        save()
        return state
    except BaseException as exc:
        state['status']='interrupted_or_blocked'
        state['error_type']=type(exc).__name__
        state['error']=str(exc)[:300]
        save()
        raise


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--agent-bank-dir',type=Path,default=Path('training/agentbank'))
    p.add_argument('--ability-bank-dir',type=Path,default=Path('training/abilitybank'))
    p.add_argument('--out-dir',type=Path,default=Path('training/coupled_candidates'))
    p.add_argument('--start',type=int,default=1)
    p.add_argument('--end',type=int,default=1)
    p.add_argument('--slots',type=int,default=1000)
    p.add_argument('--steps',type=int,default=3)
    p.add_argument('--samples',type=int,default=40)
    p.add_argument('--seed',type=int,default=2077)
    p.add_argument('--approve-training',action='store_true')
    args=p.parse_args()
    result=run_range(args.agent_bank_dir,args.ability_bank_dir,args.out_dir,
            start=args.start,end=args.end,slots=args.slots,steps=args.steps,
            samples=args.samples,seed=args.seed,approve_training=args.approve_training)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()