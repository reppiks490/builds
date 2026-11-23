"""Read-only, batch-by-batch verification of a trained independent ability bank."""
from __future__ import annotations
import argparse, hashlib, json, time
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
from .ability_weight_bank import AbilityBank,WIDTH,TOTAL_ABILITIES

def verify(root, count=TOTAL_ABILITIES):
    b=AbilityBank(root,count)
    try:
        entries=b.db.execute('SELECT start_id,end_id,abilities,improved_count,sha256 FROM batches ORDER BY start_id,end_id').fetchall()
        ok=0;bad=[];covered=0;training_samples=0;last_end=0;sha=hashlib.sha256()
        for lo,hi,n,improved,digest in entries:
            verified=b.verify_batch(lo,hi)['verified']
            if not verified:bad.append([lo,hi])
            else:ok+=1
            if lo!=last_end+1:bad.append(['gap',last_end+1,lo])
            covered+=n;training_samples+=improved;last_end=hi
        # Full-file digest detects corruption between documented snapshots.
        with b.path.open('rb') as f:
            for block in iter(lambda:f.read(4*1024*1024),b''):
                sha.update(block)
        st=b.status()
        samples=np.linspace(1,count,num=min(10000,count),dtype=np.int64)
        weights=np.asarray(b.weights[samples-1],dtype=np.float16)
        unique=int(np.unique(weights,axis=0).shape[0])
        success=(not bad and covered==count and last_end==count and
                 st['trained_synthetic']==count and training_samples==count and unique==len(samples))
        out={'certification_version':'v0.7-synthetic-training','verified_utc':datetime.now(timezone.utc).isoformat(timespec='seconds'),
             'all_checks_pass':bool(success),'ability_rows':count,'parameters_per_ability':WIDTH,
             'individual_weight_vectors_trained_synthetic':st['trained_synthetic'],
             'all_ledger_batches_verified':ok,'total_ledger_batches':len(entries),
             'synthetic_holdout_improvement_count':training_samples,
             'sampled_unique_weight_vectors':unique,'sample_size':len(samples),
             'weight_file_sha256':sha.hexdigest(),'bad_batches':bad[:8],
             'general_intelligence_certified':False,'trading_performance_certified':False,
             'real_world_mastery_certified':False,
             'interpretation':'Independently trained 32-weight linear adapters on synthetic tasks, not 10 million validated semantic skills'}
        return out
    finally:b.close()

def main():
    p=argparse.ArgumentParser();p.add_argument('--dir',default=str(Path(__file__).parent/'abilitybank'))
    p.add_argument('--count-total',type=int,default=TOTAL_ABILITIES)
    p.add_argument('--output',default=str(Path(__file__).parent/'FULL_BANK_VERIFICATION.json'))
    a=p.parse_args();cert=verify(a.dir,a.count_total)
    Path(a.output).write_text(json.dumps(cert,indent=2)+'\n')
    print(json.dumps(cert,indent=2))
    if not cert['all_checks_pass']:raise SystemExit(1)
if __name__=='__main__':main()
