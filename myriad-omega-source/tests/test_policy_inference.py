from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from training.fleet_trainer import train_fleet
from training.policy_inference import PolicyInference,PolicyInferenceError,ACTIONS

def test_real_agent_policy_inference_is_reproducible(tmp_path):
    train_fleet(tmp_path,start=1,end=2)
    p=PolicyInference(tmp_path,fleet=10000)
    a=p.infer(1);b=p.infer(1);c=p.infer(2)
    assert a==b
    assert a['agent_specific_parameters']==411000
    assert a['actions_executed']==0
    assert a['gradient_steps_in_ledger']==2
    assert a['chosen_synthetic_action'] in ACTIONS
    assert a['action_scores']!=c['action_scores']
    assert not a['validated_external_performance']

def test_reject_malformed_features_and_untrained_agents(tmp_path):
    train_fleet(tmp_path,start=1,end=1)
    p=PolicyInference(tmp_path)
    with pytest.raises(ValueError):p.infer(0)
    with pytest.raises(ValueError):p.infer(1,[0]*31)
    with pytest.raises(ValueError):p.infer(1,[float('nan')]*32)
    with pytest.raises(ValueError):p.infer(1,[9]*32)
    with pytest.raises(PolicyInferenceError,match='not trained'):p.infer(2)

def test_refuse_tampered_weight_bank(tmp_path):
    train_fleet(tmp_path,start=1,end=1)
    model=PolicyInference(tmp_path)
    assert model.infer(1)['agent']=='AG-00001'
    weight=tmp_path/'agent_weights.fp16'
    with weight.open('r+b') as f:
        a=f.read(1);f.seek(0);f.write(bytes([a[0]^3]))
    with pytest.raises(PolicyInferenceError,match='Integrity failure'):
        model.infer(1)
