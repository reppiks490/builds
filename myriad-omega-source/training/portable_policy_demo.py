"""Create and verify a small portable trained *synthetic* policy demonstration.

Not a full-fleet checkpoint or an LLM. No inference tools/actions are executed.
The owner-approved normal source release omits the 8.22 GB complete bank.
"""
from __future__ import annotations
import argparse, hashlib, json, math, sqlite3
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import numpy as np
import torch
from torch.nn.utils import vector_to_parameters
from .individual_weight_bank import AgentPolicy, PARAMETERS, BYTES_PER_AGENT
from .policy_inference import ACTIONS, PolicyInference

SCHEMA='myriad.portable_synthetic_policy_demo.v1'


def build_sample(bank:Path, output:Path,*,agents:tuple[int,...]=(1,2,3,4,5,6,7,8,9,10)) -> dict:
    bank,output=Path(bank),Path(output)
    if not agents or len(agents)>100 or len(set(agents))!=len(agents) or any(type(a)!=int or a<1 or a>10000 for a in agents):
        raise ValueError('Expected 1 to 100 distinct valid agent IDs')
    ledger=bank/'weight_ledger.sqlite3'
    weights=bank/'agent_weights.fp16'
    if not ledger.is_file() or not weights.is_file():raise ValueError('Missing trained agent bank')
    conn=sqlite3.connect(f'file:{ledger}?mode=ro',uri=True)
    try:
        with weights.open('rb') as f:
            payload=bytearray()
            rows=[]
            for agent in agents:
                info=conn.execute('SELECT status,steps,sha256 FROM agent_weights WHERE agent=?',(agent,)).fetchone()
                if not info or info[0]!='trained' or not info[1]:
                    raise ValueError(f'AG-{agent:05d} not trained')
                f.seek((agent-1)*BYTES_PER_AGENT)
                raw=f.read(BYTES_PER_AGENT)
                if len(raw)!=BYTES_PER_AGENT or hashlib.sha256(raw).hexdigest()!=info[2]:
                    raise ValueError(f'AG-{agent:05d} failed integrity check')
                payload.extend(raw)
                rows.append({'agent_id':agent,'gradient_steps':int(info[1]),'sha256':info[2]})
    finally:conn.close()
    manifest={'schema':SCHEMA,'precision':'FP16','parameters_per_agent':PARAMETERS,
              'policy_kind':'small synthetic decision neural network, not a language model',
              'rows':rows,'packed_sha256':hashlib.sha256(payload).hexdigest(),
              'source':'locally verified training bank, no external provenance attestation',
              'model_approved_for_real_world_actions':False}
    output.parent.mkdir(parents=True,exist_ok=True)
    with ZipFile(output,'w',compression=ZIP_DEFLATED,compresslevel=6) as z:
        z.writestr('manifest.json',json.dumps(manifest,indent=2)+'\n')
        z.writestr('weights.fp16',bytes(payload))
    return manifest


def predict_from_sample(path:Path, agent:int) -> dict:
    if type(agent)!=int or not 1<=agent<=10000:raise ValueError('Invalid agent')
    with ZipFile(path) as z:
        if set(z.namelist())!={'manifest.json','weights.fp16'}:
            raise ValueError('Unexpected sample archive contents')
        info=z.getinfo('weights.fp16')
        if info.file_size > 100*BYTES_PER_AGENT:
            raise ValueError('Oversized sample weights')
        m=json.loads(z.read('manifest.json'))
        rows=m.get('rows',[])
        if m.get('schema')!=SCHEMA or m.get('parameters_per_agent')!=PARAMETERS or m.get('precision')!='FP16' or not 1<=len(rows)<=100:
            raise ValueError('Invalid sample manifest')
        raw=z.read('weights.fp16')
    if len(raw)!=len(rows)*BYTES_PER_AGENT or hashlib.sha256(raw).hexdigest()!=m['packed_sha256']:
        raise ValueError('Sample packed hash mismatch')
    ids=[row.get('agent_id') for row in rows]
    if len(set(ids))!=len(ids) or ids.count(agent)!=1:
        raise ValueError('Selected agent not present exactly once')
    idx=ids.index(agent)
    vector=raw[idx*BYTES_PER_AGENT:(idx+1)*BYTES_PER_AGENT]
    if hashlib.sha256(vector).hexdigest()!=rows[idx]['sha256']:
        raise ValueError('Agent row hash mismatch')
    flat=np.frombuffer(vector,dtype='<f2').astype(np.float32)
    if not np.isfinite(flat).all():raise ValueError('Invalid weights')
    model=AgentPolicy()
    vector_to_parameters(torch.tensor(flat.copy()),model.parameters())
    model.eval()
    features=PolicyInference.demo_features(agent)
    with torch.inference_mode():
        y=model(torch.tensor(features,dtype=torch.float32).reshape(1,32)).flatten().tolist()
    if not all(math.isfinite(x) for x in y):raise ValueError('Invalid prediction')
    index=max(range(8),key=lambda i:y[i])
    return {'schema':'myriad.portable_policy_demo_result.v1','agent':f'AG-{agent:05d}',
        'synthetic_action':ACTIONS[index],'eight_action_scores':[round(x,5) for x in y],
        'parameters_checked':PARAMETERS,'stored_weight_sha256':rows[idx]['sha256'],
        'actual_trained_neural_weights_used':True,'external_mastery_certified':False,
        'provider_model_calls':0,'external_actions_executed':0}


def main():
    p=argparse.ArgumentParser(description='Portable, checksum-verified synthetic neural-policy demo')
    p.add_argument('mode',choices=['build','infer']);p.add_argument('--bank-dir',type=Path,default=Path('training/agentbank'))
    p.add_argument('--sample',type=Path,required=True);p.add_argument('--agent',type=int,default=1)
    args=p.parse_args()
    result=build_sample(args.bank_dir,args.sample) if args.mode=='build' else predict_from_sample(args.sample,args.agent)
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
