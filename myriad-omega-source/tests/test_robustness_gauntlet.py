import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from training.robustness_gauntlet import gauntlet, SCENARIOS


def test_gauntlet_rejects_unsafe_eval_size():
    with pytest.raises(ValueError):gauntlet('/unavailable',sample=1001)
    with pytest.raises(ValueError):gauntlet('/unavailable',batch=4096)


def test_gauntlet_measures_frozen_trained_weights_without_promotion():
    root=Path(__file__).resolve().parents[1]/'training'/'agentbank'
    if not (root/'weight_ledger.sqlite3').exists():pytest.skip('Large weights excluded from portable source')
    r=gauntlet(root,sample=2,batch=16)
    assert r['sampled_agent_count']==2
    assert r['covered_workflows']==2
    assert r['independent_real_world_certifications']==0
    assert r['model_weights_modified'] is False
    assert r['auto_promotion_authorized'] is False
    assert len(r['content_sha256'])==64
    assert set(r['measurements'])==set(SCENARIOS)
    assert r['results'][0]['agent_id']=='AG-00001'
    assert r['results'][1]['agent_id']=='AG-05001'
    assert all(v['mean_mse']>=0 for v in r['measurements'].values())
