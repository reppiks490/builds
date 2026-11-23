import sys,pytest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from training.fleet_trainer import train_fleet
from training.adaptive_sandbox import AdaptiveSandbox
from training.adaptive_telemetry import summary,agent_events

def test_readonly_new_database_not_created(tmp_path):
    m=summary(tmp_path)
    assert m['status']=='no_learning_candidates' and not tmp_path.joinpath('adaptive_memory.sqlite3').exists()
    assert agent_events(tmp_path,'AG-00001')['events']==[]

def test_real_candidate_memory_readonly(tmp_path):
    train_fleet(tmp_path/'bank',start=1,end=1)
    a=AdaptiveSandbox(tmp_path/'bank',tmp_path/'adaptive')
    try:r=a.propose(1)
    finally:a.close()
    s=summary(tmp_path/'adaptive')
    assert s['stored_candidate_count']==1 and s['auto_promotions']==0
    assert agent_events(tmp_path/'adaptive','AG-00001')['events'][0]['receipt_sha256']==r['receipt_sha256']
    with pytest.raises(ValueError):agent_events(tmp_path/'adaptive','AG-10001')
