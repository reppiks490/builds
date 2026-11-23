import sys
import tempfile
import json
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from curriculum import method_id,decode_method,METHOD_SPACE
from train_10000 import train,StrategyAdapterBank
from verify_weights import verify
from runtime_policy import AgentPolicy

def test_ten_billion_method_registry_endpoints():
    assert METHOD_SPACE==10000000000
    for agent,wf,var in ((1,1,0),(1,50,19999),(10000,1,0),(10000,50,19999),(1234,42,963)):
        m=method_id(agent,wf,var)
        assert decode_method(m)['agent']==f'AG-{agent:05}'
        assert decode_method(m)['workflow']==f'W{wf:02}'
        assert decode_method(m)['variant']==var
    assert method_id(10000,50,19999)==9999999999
    with pytest.raises(ValueError):decode_method(METHOD_SPACE)

def test_100_distinct_agents_receive_real_weight_updates_and_can_infer(tmp_path):
    args=type('Args',(),dict(agents=100,epochs=3,samples_per_agent=8,heldout=5,
        batch_agents=40,threads=2,lr=.025,seed=49013,output=str(tmp_path)))()
    r=train(args)
    assert r['trained_agent_weights']==r['unique_agent_parameter_sets']==100
    assert r['final_heldout']['mse'] < r['baseline_heldout']['mse']
    assert verify(tmp_path)==100
    policy=AgentPolicy(tmp_path)
    o=policy.infer('AG-00100','W50','PRAXIS',[.25]*12)
    assert o['weights_trained'] and len(o['ranked_actions'])==8
    assert o['agent']=='AG-00100'
    with pytest.raises(ValueError):policy.infer('AG-99999','W50','PRAXIS',[.25]*12)
