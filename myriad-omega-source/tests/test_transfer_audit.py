import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pytest,torch
from training.transfer_audit import teacher,audit
from training.individual_weight_bank import WeightBank

def test_teacher_matches_existing_synthetic_training_definition():
    for agent in [1,49,10000]:
        x,y=WeightBank._exercise(agent,16,581)
        assert torch.allclose(y,teacher(x,agent),atol=1e-6)

def test_transfer_audit_budget_rejects_unbounded_requests():
    with pytest.raises(ValueError):audit('unused',sample=10001)
    with pytest.raises(ValueError):audit('unused',batch=1000)

def test_transfer_audit_real_weights_one_agent():
    root=Path(__file__).resolve().parents[1]/'training'/'agentbank'
    if not (root/'weight_ledger.sqlite3').exists():pytest.skip('Full weight bank not distributed with source')
    result=audit(root,sample=1,batch=16)
    assert result['trained_models_sampled']==1
    assert result['real_world_skills_certified']==0
    assert result['weights_modified'] is False
    assert result['mean_id_mse']>=0 and result['mean_shifted_mse']>=0
    assert len(result['weights_sha256_rows'][0]['sha256'])==64
