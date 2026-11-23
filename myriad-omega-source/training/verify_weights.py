"""Independently reload and verify checkpoint and every one of the 10k weights."""
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
from safetensors.torch import load_file
from train_10000 import StrategyAdapterBank,tensor_digest,scenarios,D,K
import torch

def verify(out=None):
    folder=Path(out).resolve() if out else Path(__file__).resolve().parent/'checkpoints'
    report=json.loads((folder/'TRAINING_CERTIFICATION.json').read_text('utf8'))
    f=folder/report['checkpoint']
    assert hashlib.sha256(f.read_bytes()).hexdigest()==report['checkpoint_sha256'],'Checkpoint checksum differs'
    ledger=folder/report['weight_ledger']
    assert hashlib.sha256(ledger.read_bytes()).hexdigest()==report['weight_ledger_sha256'],'Ledger checksum differs'
    state=load_file(str(f),device='cpu')
    a=report['configured_agents'];model=StrategyAdapterBank(a);model.load_state_dict(state,strict=True);model.eval()
    seen=set();count=0
    with ledger.open(encoding='utf8') as rows:
        for i,line in enumerate(rows):
            record=json.loads(line)
            assert record['id']==f'AG-{i+1:05d}', f'Agent order mismatch at {i}'
            assert record['weight_updated'],f'Missing update at {i}'
            digest=tensor_digest(model.adapter_a[i],model.adapter_b[i],model.agent_bias[i])
            assert digest==record['weight_sha256'], f'Adapter mismatch at {i}'
            assert digest not in seen,'Non-unique agent parameterization'
            seen.add(digest);count+=1
    assert count==a==report['trained_agent_weights'],'Agent count mismatch'
    with torch.no_grad():
        ids=torch.tensor([0,a//2,a-1],dtype=torch.long)
        x,_,_=scenarios(ids,2,seed=430001)
        values=model(x,ids)
        assert values.shape==(3,2,K) and bool(torch.isfinite(values).all())
    print(json.dumps({'checkpoint_verified':True,'agents_verified':count,'unique_weights':len(seen),'sha256':report['checkpoint_sha256'],'heldout':report['final_heldout']},indent=2))
    return count
if __name__=='__main__':verify(sys.argv[1] if len(sys.argv)>1 else None)
