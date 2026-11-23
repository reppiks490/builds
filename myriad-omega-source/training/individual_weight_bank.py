"""411,000 REAL trainable independent neural parameters PER agent.

10,000 x 411,000 = 4,110,000,000 agent-owned parameters. FP16 storage:
8,220,000,000 bytes (decimal) or 7.66 GiB, excluding SQLite metadata.
Training uses a float32 transient copy + transient AdamW state for ONE agent.
This is a compact decision network, NOT 10,000 foundation language models.

Important distinctions:
 - 'reserved' means disk address space exists, NOT trained.
 - 'initialized' means a unique, inspectable full parameter vector exists on disk.
 - 'trained' means genuine gradient steps were committed and audited.
 - Synthetic classification accuracy is NOT real-world competence.
 - The system does not self-modify or place trades.
"""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import time

import numpy as np
import torch
from torch import nn
from torch.nn.utils import parameters_to_vector,vector_to_parameters

FLEET=10_000
ARCHITECTURE=((32,512),(512,544),(544,208),(208,8))
PARAMETERS=sum(i*o+o for i,o in ARCHITECTURE)
assert PARAMETERS==411_000,PARAMETERS
BYTES_PER_AGENT=PARAMETERS*2
TOTAL_STORAGE=FLEET*BYTES_PER_AGENT

class AgentPolicy(nn.Module):
    def __init__(self):
        super().__init__()
        self.layers=nn.Sequential(nn.Linear(32,512),nn.GELU(),nn.Linear(512,544),
                                  nn.GELU(),nn.Linear(544,208),nn.GELU(),nn.Linear(208,8))
        assert sum(p.numel() for p in self.parameters())==PARAMETERS
    def forward(self,x):return self.layers(x)

class WeightBank:
    def __init__(self,root,*,max_agents=FLEET):
        self.root=Path(root).resolve();self.root.mkdir(parents=True,exist_ok=True)
        self.max_agents=max_agents
        if not 1<=max_agents<=FLEET:raise ValueError('Invalid fleet size')
        self.file=self.root/'agent_weights.fp16'
        self.db=sqlite3.connect(self.root/'weight_ledger.sqlite3')
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('''CREATE TABLE IF NOT EXISTS agent_weights(
             agent INTEGER PRIMARY KEY, status TEXT NOT NULL, steps INTEGER NOT NULL DEFAULT 0,
             sha256 TEXT NOT NULL,updated TEXT NOT NULL,baseline_loss REAL,
             final_loss REAL,heldout_loss REAL,weight_precision TEXT NOT NULL)''')
        self.db.commit()
        expected=self.max_agents*BYTES_PER_AGENT
        # Sparse file reservation: fast, but disk MUST have real room to persist updates.
        if not self.file.exists():
            with self.file.open('wb') as f:
                f.truncate(expected)
        if self.file.stat().st_size!=expected:raise RuntimeError('Weight bank size differs from configured fleet: refusing to open')
        self.bank=np.memmap(self.file,dtype=np.float16,mode='r+',shape=(max_agents,PARAMETERS))

    def _row(self,agent):
        if not isinstance(agent,int) or isinstance(agent,bool) or not 1<=agent<=self.max_agents:raise ValueError('Agent outside registered range')
        return agent-1

    def status(self,agent):
        self._row(agent)
        row=self.db.execute('SELECT status,steps,sha256,baseline_loss,final_loss,heldout_loss FROM agent_weights WHERE agent=?',(agent,)).fetchone()
        if row is None:return {'agent':f'AG-{agent:05d}','status':'reserved_not_initialized','steps':0,'parameters':PARAMETERS}
        return {'agent':f'AG-{agent:05d}','status':row[0],'steps':row[1],'sha256':row[2],
                'baseline_loss':row[3],'final_loss':row[4],'heldout_loss':row[5],'parameters':PARAMETERS}
    def summary(self):
        groups=self.db.execute('SELECT status,COUNT(*),SUM(steps) FROM agent_weights GROUP BY status').fetchall()
        registered=sum(v[1] for v in groups)
        return {'agents_reserved':self.max_agents,'parameters_per_agent':PARAMETERS,
                'total_agent_specific_parameters':self.max_agents*PARAMETERS,
                'full_fleet_parameter_target':FLEET*PARAMETERS,
                'weight_storage_bytes':self.max_agents*BYTES_PER_AGENT,
                'precision':'FP16 storage; FP32 temporary training',
                'initialized_agents':registered,
                'trained_agents':sum(count for status,count,_ in groups if status=='trained'),
                'uninitialized_agents':self.max_agents-registered,
                'total_recorded_gradient_steps':sum(steps or 0 for _,_,steps in groups),
                'weight_bank_exists':self.file.exists(),
                'status_by_group':{status:count for status,count,_ in groups},
                'benchmark_scope':'synthetic action-policy exercise; no validated general intelligence or trading edge'}
    def _write_row(self,agent,flat,status,steps=0,baseline=None,final=None,heldout=None):
        pos=self._row(agent)
        arr=np.asarray(flat,dtype=np.float16)
        if arr.shape!=(PARAMETERS,) or not np.isfinite(arr).all():raise ValueError('Invalid weight vector')
        digest=hashlib.sha256(arr.tobytes()).hexdigest()
        self.bank[pos,:]=arr
        self.bank.flush()
        now=datetime.now(timezone.utc).isoformat(timespec='seconds')
        self.db.execute('INSERT OR REPLACE INTO agent_weights(agent,status,steps,sha256,updated,baseline_loss,final_loss,heldout_loss,weight_precision) VALUES(?,?,?,?,?,?,?,?,?)',
          (agent,status,steps,digest,now,baseline,final,heldout,'fp16'))
        self.db.commit()
        return digest
    def initialize(self,agent):
        old=self.status(agent)
        if old['status']!='reserved_not_initialized':return old
        # independent seeded initialization across entire model, not identical copies.
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(9256001+agent*101)
            net=AgentPolicy()
        flat=parameters_to_vector(net.parameters()).detach().numpy()
        self._write_row(agent,flat,'initialized')
        return self.status(agent)
    def verify(self,agent):
        st=self.status(agent)
        if st['status']=='reserved_not_initialized':return False
        got=hashlib.sha256(self.bank[self._row(agent)].tobytes()).hexdigest()
        return st['sha256']==got
    def load_model(self,agent):
        if self.status(agent)['status']=='reserved_not_initialized':raise RuntimeError('Agent weights not initialized')
        if not self.verify(agent):raise RuntimeError('Agent weight checksum mismatch')
        net=AgentPolicy()
        v=torch.from_numpy(np.asarray(self.bank[self._row(agent)],dtype=np.float32).copy())
        vector_to_parameters(v,net.parameters())
        return net
    @staticmethod
    def _exercise(agent,samples,seed):
        g=torch.Generator(device='cpu').manual_seed(seed+agent*70001)
        x=torch.randn(samples,32,generator=g)
        # The teacher intentionally uses a fixed, inspectable synthetic program.
        weights=torch.tensor([[.9,-.7,.4,.0,.3,-.1,.2,.5],[-.4,.7,.5,.3,-.2,.4,0.,.1],
          [.3,.1,-.4,.8,.2,.1,.5,-.3],[.5,-.1,.2,.4,.1,.8,-.2,.6],
          [-.2,.3,.1,.1,.7,-.4,.5,.2],[.4,-.1,.8,-.2,.2,.3,.1,.5],
          [.1,.5,.2,-.3,.6,.2,.3,-.2],[-.4,.2,-.1,.5,.2,.4,.8,.1]])
        target=x[:,:8]@weights
        trait=(agent%97)/97.0-.5
        target+=trait*torch.sin(x[:,8:9]*torch.arange(1,9).float())
        return x,target
    def train_one(self,agent,*,steps=5,lr=.002,samples=64,seed=2006):
        if not 1<=steps<=2000:raise ValueError('steps must be 1..2000')
        if not 4<=samples<=8192:raise ValueError('samples must be 4..8192')
        self.initialize(agent)
        old=self.status(agent)
        net=self.load_model(agent)
        x,y=self._exercise(agent,samples,seed)
        xv,yv=self._exercise(agent,max(16,samples//2),seed+919)
        opt=torch.optim.AdamW(net.parameters(),lr=lr,weight_decay=0)
        net.eval()
        with torch.no_grad():
            before=float(nn.functional.mse_loss(net(x),y))
            heldout_before=float(nn.functional.mse_loss(net(xv),yv))
        for _ in range(steps):
            net.train();opt.zero_grad(set_to_none=True)
            loss=nn.functional.mse_loss(net(x),y)
            loss.backward();nn.utils.clip_grad_norm_(net.parameters(),1.0);opt.step()
        net.eval()
        with torch.no_grad():
            after=float(nn.functional.mse_loss(net(x),y))
            heldout_after=float(nn.functional.mse_loss(net(xv),yv))
        if not np.isfinite(after) or not np.isfinite(heldout_after):raise RuntimeError('Non-finite loss; declining checkpoint')
        if after >= before:raise RuntimeError('No in-sample loss improvement; declining checkpoint')
        flat=parameters_to_vector(net.parameters()).detach().numpy()
        self._write_row(agent,flat,'trained',steps=old['steps']+steps,
                        baseline=before,final=after,heldout=heldout_after)
        return {'agent':agent,'parameters_updated_with_backprop':PARAMETERS,
            'weight_vector_changed':old['sha256']!=self.status(agent)['sha256'],
            'training_loss_before':round(before,6),'training_loss_after':round(after,6),
            'heldout_loss_before':round(heldout_before,6),'heldout_loss_after':round(heldout_after,6),
            'steps':steps,'total_steps':old['steps']+steps,'verified':self.verify(agent),
            'scope':'synthetic objective, not independent general intelligence or market skill'}
    def close(self):
        self.bank.flush();del self.bank;self.db.close()

def main():
    p=argparse.ArgumentParser(description='MYRIAD Ω independent full-size per-agent neural policy weights')
    p.add_argument('command',choices=['status','initialize','train','verify'])
    p.add_argument('--dir',default=str(Path(__file__).resolve().parent/'weightbank'))
    p.add_argument('--fleet',type=int,default=FLEET)
    p.add_argument('--start',type=int,default=1)
    p.add_argument('--count',type=int,default=1)
    p.add_argument('--steps',type=int,default=5)
    p.add_argument('--threads',type=int,default=2)
    a=p.parse_args()
    if a.command in ('initialize','train'):
        if a.start<1 or a.count<1 or a.start+a.count-1>a.fleet:p.error('Invalid agent range')
        free=shutil.disk_usage(Path(a.dir).parent).free
        if free<min(2_000_000_000,a.fleet*BYTES_PER_AGENT+500_000_000):
            p.error('Not enough free disk for safe training. Free space or change --dir.')
    torch.set_num_threads(max(1,min(a.threads,8)))
    bank=WeightBank(a.dir,max_agents=a.fleet)
    try:
        if a.command=='status':print(json.dumps(bank.summary(),indent=2))
        elif a.command in ('initialize','train'):
            completed=0
            for aid in range(a.start,a.start+a.count):
                result=bank.initialize(aid) if a.command=='initialize' else bank.train_one(aid,steps=a.steps)
                completed+=1
                if completed%100==0 or completed==a.count:
                    print(json.dumps({'progress':completed,'of':a.count,'last_agent':aid,'result':result},default=str),flush=True)
            print(json.dumps(bank.summary(),indent=2))
        elif a.command=='verify':
            checked=[{'agent':n,'verified':bank.verify(n)} for n in range(a.start,a.start+a.count)]
            print(json.dumps(checked,indent=2))
            if not all(x['verified'] for x in checked):raise SystemExit(1)
    finally:bank.close()

if __name__=='__main__':main()
