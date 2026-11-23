"""MYRIAD Ω 10-million *independent trainable ability-adapter* bank.

Honesty boundary: These are 32-parameter, synthetic-task-trained linear
adapters. They are not evidence of 10 million distinct real-world competences,
model fine-tunes, executable skills or general intelligence. Real competence
needs independent tasks, unseen datasets and external verification.

Training objective (for ability a): y_a,j = theta_a,j on x=e_j, j=1..32.
Each vector is trained independently by 8 SGD passes on its own labeled
identity-basis regression dataset, which gives grad(loss) = w-theta for
loss=.5*sum_j (w_j-theta_j)^2. A held-out dense feature matrix evaluates
predicted y for inputs not seen in training; no held-out labels are used to
update weights. Stochastic initialization and targets depend on ability ID.

Persistent layout (~670 MB for 10 million abilities):
 - weights.fp16: 10_000_000 x 32 unique, mutable trainable parameters
 - status.u8: 0=untrained, 2=synthetic-trained per ability
 - steps.u8: number of committed training steps per ability
 - ledger.sqlite3: per-batch metrics and SHA256 of written weights
A *reserved* memmap row is NOT initialized/trained. API never conflates counts.
"""
from __future__ import annotations
import argparse, hashlib, json, os, shutil, sqlite3, sys, time
from pathlib import Path
from datetime import datetime, timezone
import numpy as np

TOTAL_ABILITIES=10_000_000
WIDTH=32
WEIGHT_BYTES=TOTAL_ABILITIES*WIDTH*2
STATUS_UNTRAINED=0
STATUS_TRAINED_SYNTHETIC=2
PROBE=np.stack([
    np.cos(np.arange(WIDTH,dtype=np.float32)*.75+i*1.37)+
    np.sin(np.arange(WIDTH,dtype=np.float32)*.31+i*.83)
    for i in range(4)
]).astype(np.float32)
PROBE/=np.sqrt((PROBE*PROBE).sum(axis=1,keepdims=True))


def _teacher(ids):
    """Deterministic unique per-ability synthetic teaching vector, not real data."""
    ids=np.asarray(ids,dtype=np.uint32).reshape(-1,1)
    dims=np.arange(1,WIDTH+1,dtype=np.uint32).reshape(1,-1)
    with np.errstate(over='ignore'):
        h=(ids*np.uint32(0x9e3779b9)) ^ (dims*np.uint32(0x85ebca6b))
        h ^= (h >> np.uint32(16))
        h *= np.uint32(0x7feb352d)
        h ^= (h >> np.uint32(15))
        h *= np.uint32(0x846ca68b)
        h ^= (h >> np.uint32(16))
    return ((h & np.uint32(65535)).astype(np.float32)/32767.5-1.)*.25


def _initial(ids):
    """Independent per-ID parameter initialization, much smaller than teacher."""
    ids=np.asarray(ids,dtype=np.uint32).reshape(-1,1)
    dims=np.arange(1,WIDTH+1,dtype=np.uint32).reshape(1,-1)
    with np.errstate(over='ignore'):
        h=(ids*np.uint32(0x27d4eb2d)) ^ (dims*np.uint32(0x165667b1))
        h ^= h >> np.uint32(13)
        h *= np.uint32(0x9e3779b9)
        h ^= h >> np.uint32(16)
    return ((h & np.uint32(65535)).astype(np.float32)/32767.5-1.)*.01


def _loss(w,theta):
    diff=(w-theta) @ PROBE.T
    return np.mean(diff*diff,axis=1,dtype=np.float32)


class AbilityBank:
    def __init__(self, root, count=TOTAL_ABILITIES):
        if not 1<=count<=TOTAL_ABILITIES:raise ValueError('Invalid bank size')
        self.count=count
        self.root=Path(root).resolve();self.root.mkdir(parents=True,exist_ok=True)
        self.path=self.root/'weights.fp16'
        self.state_path=self.root/'status.u8'
        self.steps_path=self.root/'steps.u8'
        self.sql_path=self.root/'ability_ledger.sqlite3'
        specs=((self.path,count*WIDTH*2),(self.state_path,count),(self.steps_path,count))
        for path,nbytes in specs:
            if not path.exists():
                with path.open('wb') as f:f.truncate(nbytes)
            if path.stat().st_size!=nbytes:
                raise RuntimeError(f'Existing bank size mismatch: {path.name}')
        self.weights=np.memmap(self.path,dtype='<f2',mode='r+',shape=(count,WIDTH))
        self.state=np.memmap(self.state_path,dtype=np.uint8,mode='r+',shape=(count,))
        self.steps=np.memmap(self.steps_path,dtype=np.uint8,mode='r+',shape=(count,))
        self.db=sqlite3.connect(self.sql_path)
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('''CREATE TABLE IF NOT EXISTS batches (
          start_id INTEGER NOT NULL, end_id INTEGER NOT NULL, abilities INTEGER NOT NULL,
          gradient_steps INTEGER NOT NULL, mean_loss_before REAL NOT NULL,
          mean_loss_after REAL NOT NULL, improved_count INTEGER NOT NULL,
          sha256 TEXT NOT NULL, committed_utc TEXT NOT NULL,
          PRIMARY KEY(start_id,end_id))''')
        self.db.commit()

    def status(self, *, full_scan=True):
        ntrained=int(np.count_nonzero(self.state==STATUS_TRAINED_SYNTHETIC)) if full_scan else None
        return {'abilities_reserved':self.count,'independent_weight_dimensions_per_ability':WIDTH,
                'trainable_ability_parameters_reserved':self.count*WIDTH,
                'weight_bank_bytes':self.count*WIDTH*2,'trained_synthetic':ntrained,
                'untrained':self.count-ntrained if ntrained is not None else None,
                'training_batches':self._batch_count(),
                'training_kind':'independent gradient-updated linear adapters on synthetic identity-basis tasks',
                'certified_real_world_abilities':0,
                'certified_distinct_semantic_skills':0,
                'risk':'TRAINED does not mean mastered; no general intelligence or trading-performance certification'}

    def _batch_count(self):
        # Server uses ThreadingHTTPServer. Open a read-only connection in the
        # calling thread rather than sharing the creator-thread connection.
        c=sqlite3.connect(self.sql_path)
        try:return int(c.execute('SELECT COUNT(*) FROM batches').fetchone()[0])
        finally:c.close()

    def train_range(self,start=1,count=1000,steps=8,lr=.22,chunk=50000):
        if not 1<=start<=self.count or not 1<=count<=self.count-start+1:raise ValueError('Invalid training range')
        if not 1<=steps<=64:raise ValueError('steps must be 1..64')
        if not 0<lr<1:raise ValueError('lr must be between 0 and 1')
        if not 1<=chunk<=200000:raise ValueError('chunk must be 1..200000')
        processed=0; trained=0; improved=0; loss_before_sum=0.;loss_after_sum=0.;batch_count=0
        for lo in range(start-1,start-1+count,chunk):
            hi=min(lo+chunk,start-1+count)
            state=np.asarray(self.state[lo:hi],dtype=np.uint8)
            if np.all(state==STATUS_TRAINED_SYNTHETIC):
                processed+=hi-lo
                continue
            # Already trained rows are never overwritten. Crash-recovery is
            # idempotent; the status bitmap commits AFTER all weights flush.
            loc=np.flatnonzero(state!=STATUS_TRAINED_SYNTHETIC)
            ids=np.arange(lo+1,hi+1,dtype=np.uint32)[loc]
            targets=_teacher(ids)
            current=_initial(ids)
            before=_loss(current,targets)
            # Explicit independent full-batch SGD on 32 separate labels per
            # ability. No mixing of parameters or gradients between ability IDs.
            for _ in range(steps):
                current -= np.float32(lr)*(current-targets)
            updated=current.astype(np.float16).astype(np.float32)
            after=_loss(updated,targets)
            passed=int(np.count_nonzero(after<before))
            if passed!=len(ids):
                raise RuntimeError(f'{len(ids)-passed} abilities did not improve on synthetic holdout; no checkpoint committed')
            rows=lo+loc
            self.weights[rows]=current.astype(np.float16)
            self.weights.flush()
            self.steps[rows]=steps
            self.steps.flush()
            self.state[rows]=STATUS_TRAINED_SYNTHETIC
            self.state.flush()
            raw=np.asarray(self.weights[rows],dtype='<f2').tobytes()
            sha=hashlib.sha256(raw).hexdigest()
            self.db.execute('''INSERT OR REPLACE INTO batches
                 (start_id,end_id,abilities,gradient_steps,mean_loss_before,mean_loss_after,
                  improved_count,sha256,committed_utc) VALUES(?,?,?,?,?,?,?,?,?)''',
                 (lo+1,hi,len(ids),steps,float(before.mean()),float(after.mean()),
                  passed,sha,datetime.now(timezone.utc).isoformat(timespec='seconds')))
            self.db.commit()
            processed+=hi-lo;trained+=len(ids);improved+=passed
            loss_before_sum+=float(before.sum());loss_after_sum+=float(after.sum());batch_count+=1
        return {'range':[start,start+count-1],'processed':processed,
                'newly_trained':trained,'newly_improved_holdout':improved,'new_batches':batch_count,
                'mean_before_new':loss_before_sum/trained if trained else None,
                'mean_after_new':loss_after_sum/trained if trained else None,
                'training_scope':'synthetic linearly supervised ability heads, NOT 10M real-world mastered competencies'}

    def inspect(self,ability_id):
        if not isinstance(ability_id,int) or isinstance(ability_id,bool) or not 1<=ability_id<=self.count:
            raise ValueError('Ability ID outside bank')
        pos=ability_id-1
        state=int(self.state[pos])
        out={'ability_id':f'CAP-{ability_id:08d}','trained':state==STATUS_TRAINED_SYNTHETIC,
             'steps':int(self.steps[pos]),'parameters':WIDTH,
             'kind':'synthetic-trained linear ability adapter' if state==2 else 'reserved_untrained'}
        if state==2:
            row=self.weights[pos].copy()
            targ=_teacher([ability_id])[0]
            init=_initial([ability_id])[0]
            out.update({'weight_sha256':hashlib.sha256(row.tobytes()).hexdigest(),
                    'holdout_error_before':float(_loss(init.reshape(1,-1),targ.reshape(1,-1))[0]),
                    'holdout_error_after':float(_loss(row.astype(np.float32).reshape(1,-1),targ.reshape(1,-1))[0]),
                    'weight_l2':float(np.sqrt((row.astype(np.float32)**2).sum()))})
        return out

    def verify_batch(self,start,end):
        if not 1<=start<=end<=self.count:raise ValueError('Invalid range')
        row=self.db.execute('SELECT sha256,abilities,improved_count FROM batches WHERE start_id=? AND end_id=?',(start,end)).fetchone()
        if row is None:return {'verified':False,'reason':'no batch ledger'}
        b=np.asarray(self.weights[start-1:end],dtype='<f2').tobytes()
        ok=hashlib.sha256(b).hexdigest()==row[0] and np.all(self.state[start-1:end]==2) and row[1]==end-start+1
        return {'verified':bool(ok),'trained_count':row[1],'improved_count':row[2],
                'weight_sha256':row[0]}

    def close(self):
        self.weights.flush();self.state.flush();self.steps.flush()
        del self.weights;del self.state;del self.steps
        self.db.close()


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('command',choices=['status','train','inspect','verify'])
    ap.add_argument('--dir',default=str(Path(__file__).parent/'abilitybank'))
    ap.add_argument('--count-total',type=int,default=TOTAL_ABILITIES)
    ap.add_argument('--start',type=int,default=1)
    ap.add_argument('--count',type=int,default=1000)
    ap.add_argument('--chunk',type=int,default=50000)
    ap.add_argument('--steps',type=int,default=8)
    ap.add_argument('--id',type=int,default=1)
    ap.add_argument('--end',type=int)
    args=ap.parse_args()
    if args.command=='train':
        needed=args.count_total*WIDTH*2+args.count_total*2+100_000_000
        if shutil.disk_usage(Path(args.dir).resolve().parent).free<needed and not Path(args.dir,'weights.fp16').exists():
            ap.error('Insufficient free disk space for materialized ability bank')
    b=AbilityBank(args.dir,args.count_total)
    try:
        if args.command=='status':ret=b.status()
        elif args.command=='train':ret={'training':b.train_range(args.start,args.count,args.steps,chunk=args.chunk),'status':b.status()}
        elif args.command=='inspect':ret=b.inspect(args.id)
        elif args.command=='verify':ret=b.verify_batch(args.start,args.end or args.start+args.count-1)
        print(json.dumps(ret,indent=2))
    finally:b.close()

if __name__=='__main__':main()
