"""Quarantined on-demand adaptation of 411k-param neural agent policies.

This is sandbox-only continual learning from deterministic SYNTHETIC regression.
Each candidate receives REAL PyTorch backprop. It is written as an isolated
FP16 checkpoint, NOT loaded into production or promoted to the live weight bank.
SQLite evidence chains and per-agent rollback roots permit later review.
"""
from __future__ import annotations
from datetime import datetime,timezone
from pathlib import Path
import argparse,hashlib,json,os,sqlite3,time,uuid
import numpy as np
import torch
from torch.nn import functional as F
from torch.nn.utils import parameters_to_vector
from .individual_weight_bank import WeightBank,PARAMETERS
from .policy_inference import PolicyInference


def canonical(d):return json.dumps(d,sort_keys=True,separators=(',',':'),allow_nan=False)
def utc():return datetime.now(timezone.utc).isoformat(timespec='seconds')

class AdaptiveSandbox:
    def __init__(self,bank_dir,output_dir=None,*,fleet=10000):
        self.bank=Path(bank_dir).resolve()
        self.out=Path(output_dir or self.bank.parent/'adaptive_candidates').resolve()
        self.out.mkdir(parents=True,exist_ok=True)
        self.db=sqlite3.connect(self.out/'adaptive_memory.sqlite3')
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('''CREATE TABLE IF NOT EXISTS proposals(
            id TEXT PRIMARY KEY, agent INTEGER NOT NULL, source_sha256 TEXT NOT NULL,
            candidate_sha256 TEXT NOT NULL, checkpoint TEXT NOT NULL, status TEXT NOT NULL,
            training_loss_before REAL NOT NULL, training_loss_after REAL NOT NULL,
            validation_loss_before REAL NOT NULL, validation_loss_after REAL NOT NULL,
            unseen_loss_before REAL NOT NULL, unseen_loss_after REAL NOT NULL,
            steps INTEGER NOT NULL, seed INTEGER NOT NULL, prior_receipt TEXT NOT NULL,
            receipt_sha256 TEXT NOT NULL, created TEXT NOT NULL)''')
        self.db.commit()
        self.models=PolicyInference(self.bank,fleet=fleet,cache_size=1)

    def propose(self,agent,*,steps=2,samples=64,seed=5061,lr=.0008):
        if not 1<=agent<=self.models.fleet:raise ValueError('Invalid agent')
        if not 1<=steps<=40 or not 16<=samples<=512:raise ValueError('Invalid training budget')
        if not 1e-6<=lr<=.01:raise ValueError('Invalid learning rate')
        # The regular policy-inference path re-hashes on-disk bytes, even if a
        # model has already been cached. Refuse stale or corrupted baselines.
        self.models.infer(agent)
        source_sha,_=self.models._sha(agent)
        # Read base model from independently owned checkpoint. Deep-copy it so
        # trained weights are never overwritten through an alias or cache.
        import copy
        base=copy.deepcopy(self.models._model(agent,source_sha))
        candidate=copy.deepcopy(base)
        train_x,train_y=WeightBank._exercise(agent,samples,seed)
        val_x,val_y=WeightBank._exercise(agent,max(32,samples//2),seed+771)
        unseen_x,unseen_y=WeightBank._exercise(agent,max(32,samples//2),seed+9917)
        def mse(net,x,y):
            net.eval()
            with torch.inference_mode():return float(F.mse_loss(net(x),y).item())
        before=mse(base,train_x,train_y)
        val_before=mse(base,val_x,val_y)
        unseen_before=mse(base,unseen_x,unseen_y)
        opt=torch.optim.AdamW(candidate.parameters(),lr=lr,weight_decay=0)
        for _ in range(steps):
            candidate.train();opt.zero_grad(set_to_none=True)
            loss=F.mse_loss(candidate(train_x),train_y)
            loss.backward();torch.nn.utils.clip_grad_norm_(candidate.parameters(),1.);opt.step()
        after=mse(candidate,train_x,train_y)
        val_after=mse(candidate,val_x,val_y)
        unseen_after=mse(candidate,unseen_x,unseen_y)
        if not all(np.isfinite(n) for n in (before,after,val_before,val_after,unseen_before,unseen_after)):
            raise RuntimeError('Nonfinite training results; candidate discarded')
        if after>=before:raise RuntimeError('No improvement on synthetic training set; candidate discarded')
        raw=parameters_to_vector(candidate.parameters()).detach().numpy().astype('<f2').tobytes()
        assert len(raw)==PARAMETERS*2
        digest=hashlib.sha256(raw).hexdigest()
        proposal='A-'+uuid.uuid4().hex[:16]
        final=self.out/f'{proposal}.fp16'
        temp=final.with_suffix('.pending')
        with temp.open('wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
        os.replace(temp,final)
        accepted=val_after<val_before and unseen_after<unseen_before
        prior=self.db.execute('SELECT receipt_sha256 FROM proposals WHERE agent=? ORDER BY rowid DESC LIMIT 1',(agent,)).fetchone()
        previous=prior[0] if prior else '0'*64
        evidence={'id':proposal,'agent':agent,'source_sha256':source_sha,'candidate_sha256':digest,
            'steps':steps,'seed':seed,'loss_before':before,'loss_after':after,
            'validation_before':val_before,'validation_after':val_after,
            'unseen_before':unseen_before,'unseen_after':unseen_after,
            'prior_receipt':previous,'candidate_status':'quarantined_improved' if accepted else 'quarantined_regression',
            'authority':'research_only','production_promotion':False}
        receipt=hashlib.sha256(canonical(evidence).encode('utf8')).hexdigest()
        self.db.execute('''INSERT INTO proposals(id,agent,source_sha256,candidate_sha256,checkpoint,status,
            training_loss_before,training_loss_after,validation_loss_before,validation_loss_after,
            unseen_loss_before,unseen_loss_after,steps,seed,prior_receipt,receipt_sha256,created)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (proposal,agent,source_sha,digest,final.name,evidence['candidate_status'],before,after,
             val_before,val_after,unseen_before,unseen_after,steps,seed,previous,receipt,utc()))
        self.db.commit()
        return {**evidence,'receipt_sha256':receipt,'checkpoint_path':str(final),
                'agent_baseline_untouched':True,'qualified_real_world_improvement':False}

    def audit(self,agent=None):
        rows=self.db.execute('''SELECT id,agent,source_sha256,candidate_sha256,checkpoint,status,
                training_loss_before,training_loss_after,validation_loss_before,validation_loss_after,
                unseen_loss_before,unseen_loss_after,steps,seed,prior_receipt,receipt_sha256
                FROM proposals ORDER BY agent,rowid''').fetchall()
        previous_by_agent={};accepted=0;bad=[]
        for row in rows:
            (pid,aid,source,digest,name,status,before,after,vbefore,vafter,ubefore,uafter,steps,seed,prior,receipt)=row
            if agent is not None and aid!=agent:continue
            p=self.out/name
            valid=p.is_file() and p.stat().st_size==PARAMETERS*2
            if valid:valid=hashlib.sha256(p.read_bytes()).hexdigest()==digest
            if valid:valid=previous_by_agent.get(aid,'0'*64)==prior
            evidence={'id':pid,'agent':aid,'source_sha256':source,'candidate_sha256':digest,
                'steps':steps,'seed':seed,'loss_before':before,'loss_after':after,
                'validation_before':vbefore,'validation_after':vafter,
                'unseen_before':ubefore,'unseen_after':uafter,'prior_receipt':prior,
                'candidate_status':status,'authority':'research_only','production_promotion':False}
            if valid:valid=hashlib.sha256(canonical(evidence).encode()).hexdigest()==receipt
            if valid:accepted+=1;previous_by_agent[aid]=receipt
            else:bad.append(pid)
        return {'checked_proposals':accepted+len(bad),'verified_proposals':accepted,'bad_receipts':bad,
                'all_valid':not bad,'authority':'research_only','auto_promotions':0,
                'competency_certified':0}

    def summary(self):
        row=self.db.execute('SELECT COUNT(*),COUNT(DISTINCT agent),SUM(status=\'quarantined_improved\') FROM proposals').fetchone()
        return {'proposals':row[0],'agents_with_candidate_experience':row[1],
                'synthetic_heldout_improved_candidates':row[2] or 0,
                'auto_promotions':0,'status':'advisory_memory_only'}
    def close(self):self.db.close()


def main():
    p=argparse.ArgumentParser()
    p.add_argument('command',choices=['propose','audit','status'])
    p.add_argument('--bank-dir',type=Path,default=Path(__file__).resolve().parent/'agentbank')
    p.add_argument('--out-dir',type=Path)
    p.add_argument('--start',type=int,default=1)
    p.add_argument('--count',type=int,default=1)
    p.add_argument('--steps',type=int,default=2)
    a=p.parse_args()
    if not 1<=a.start<=10000 or not 1<=a.count<=10000 or a.start+a.count-1>10000:raise SystemExit('Invalid agent range')
    torch.set_num_threads(1)
    engine=AdaptiveSandbox(a.bank_dir,a.out_dir)
    try:
        if a.command=='propose':
            t=time.monotonic();result=[]
            for i in range(a.start,a.start+a.count):result.append(engine.propose(i,steps=a.steps))
            print(json.dumps({'new_proposals':len(result),'accepted_to_quarantine':sum(x['candidate_status']=='quarantined_improved' for x in result),
                'elapsed_seconds':round(time.monotonic()-t,2),'summary':engine.summary(),'audit':engine.audit()},indent=2))
        elif a.command=='audit':print(json.dumps(engine.audit(),indent=2))
        else:print(json.dumps(engine.summary(),indent=2))
    finally:engine.close()
if __name__=='__main__':main()
