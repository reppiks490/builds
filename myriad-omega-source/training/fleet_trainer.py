"""Resumable, conservative training of the 10,000 independent 411k-param agent policies.

All updates are real PyTorch autograd/AdamW updates on a disclosed SYNTHETIC
regression teacher. Does NOT train base LLMs, produce executable new skills, or
certify general intelligence/trading profitability. Sequential CPU design.

A successful trainer run is not a release authorization. Integration stays
fail-closed until external validation and separate owner approval.
"""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import json, os, shutil, sys, time
from pathlib import Path
import numpy as np
import torch
try:
    from .individual_weight_bank import WeightBank, PARAMETERS, FLEET, TOTAL_STORAGE
except ImportError:
    from individual_weight_bank import WeightBank, PARAMETERS, FLEET, TOTAL_STORAGE


def train_fleet(root: Path, *, start=1, end=FLEET, steps=2, samples=24,
                threads=1, report_every=100, progress_path=None, minimum_free_bytes=1_000_000_000):
    """Complete sequential row-level training; skip verified completed rows on resume.

    A partially written/corrupt row must be manually repaired, not silently
    reinitialized; no optimizer state is reused after restart.
    """
    if not 1 <= start <= end <= FLEET:
        raise ValueError('Invalid agent range')
    if not 1 <= steps <= 2000 or not 4 <= samples <= 8192:
        raise ValueError('Unsafe training configuration')
    if not 1 <= threads <= 8 or not 1 <= report_every <= 10000:
        raise ValueError('Invalid runtime limits')
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    if not (root / 'agent_weights.fp16').is_file():
        free = shutil.disk_usage(root).free
        if free < TOTAL_STORAGE + minimum_free_bytes:
            raise RuntimeError(f'Insufficient free disk for 8.22 GB fleet weights: {free}')
    torch.set_num_threads(threads)
    bank = WeightBank(root)
    stats = {'schema':'myriad.fleet_training_progress.v1',
             'scope':'real autograd updates, synthetic exercises only',
             'start_agent': start,'end_agent':end,'gradient_steps_per_new_agent':steps,
             'agents_trained_this_run':0,'previously_trained_and_verified':0,
             'agents_withheld_due_to_bad_integrity':0,'heldout_improvements':0,
             'trained_weight_parameters_per_agent':PARAMETERS,
             'updated_at_utc':'','durable_ledger':str(root/'weight_ledger.sqlite3'),
             'status':'in_progress'}
    progress_path = Path(progress_path) if progress_path else root/'FLEET_TRAINING_PROGRESS.json'
    start_monotonic = time.monotonic()
    def persist():
        stats['seconds_elapsed']=round(time.monotonic()-start_monotonic,3)
        stats['updated_at_utc']=datetime.now(timezone.utc).isoformat(timespec='seconds')
        stats['bank_summary']=bank.summary()
        temporary=progress_path.with_suffix('.tmp')
        temporary.write_text(json.dumps(stats,indent=2,sort_keys=True)+'\n',encoding='utf8')
        os.replace(temporary,progress_path)
    try:
        for aid in range(start,end+1):
            state=bank.status(aid)
            if state['status'] == 'trained':
                if not bank.verify(aid):
                    stats['agents_withheld_due_to_bad_integrity']+=1
                    raise RuntimeError(f'AG-{aid:05d} has stored checkpoint corruption')
                stats['previously_trained_and_verified']+=1
            else:
                if state['status']!='reserved_not_initialized' and not bank.verify(aid):
                    stats['agents_withheld_due_to_bad_integrity']+=1
                    raise RuntimeError(f'AG-{aid:05d} has stored checkpoint corruption')
                result=bank.train_one(aid,steps=steps,samples=samples)
                if not result['verified'] or not result['weight_vector_changed']:
                    raise RuntimeError(f'AG-{aid:05d} gradient checkpoint verification failed')
                stats['agents_trained_this_run']+=1
                stats['heldout_improvements']+=int(result['heldout_loss_after'] < result['heldout_loss_before'])
            if (aid-start+1)%report_every==0 or aid==end:
                stats['last_agent_processed']=aid
                persist()
                print(json.dumps({'processed':aid-start+1,'range':end-start+1,
                    'last':aid,'new':stats['agents_trained_this_run'],
                    'skipped_verified':stats['previously_trained_and_verified'],
                    'seconds_elapsed':stats['seconds_elapsed']}),flush=True)
        stats['status']='completed_training_range_not_mastery_certified'
        persist()
        return stats
    except BaseException as exc:
        stats['status']='interrupted_or_blocked'
        stats['error_type']=type(exc).__name__
        stats['error']=str(exc)[:280]
        persist()
        raise
    finally:
        bank.close()


def main():
    p=argparse.ArgumentParser(description='Real gradient training of separate synthetic agent neural policies')
    p.add_argument('--bank-dir',type=Path,default=Path(__file__).resolve().parent/'agentbank')
    p.add_argument('--start',type=int,default=1)
    p.add_argument('--end',type=int,default=FLEET)
    p.add_argument('--steps',type=int,default=2)
    p.add_argument('--samples',type=int,default=24)
    p.add_argument('--threads',type=int,default=1)
    p.add_argument('--report-every',type=int,default=100)
    args=p.parse_args()
    result=train_fleet(args.bank_dir,start=args.start,end=args.end,steps=args.steps,
                       samples=args.samples,threads=args.threads,report_every=args.report_every)
    print(json.dumps({'status':result['status'],'summary':result['bank_summary']},indent=2),flush=True)
if __name__=='__main__':main()
