"""Read-only telemetry reflects actual individual PyTorch weights, never simulation."""
from pathlib import Path
import sys,pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from training.fleet_telemetry import summary,inspect
from training.fleet_trainer import train_fleet

def test_empty_bank_never_created_on_read(tmp_path):
    p=tmp_path/'uncreated'
    s=summary(p)
    assert not p.exists() and s['gradient_trained_ledger_rows']==0
    assert not s['real_world_mastery_verified']
    a=inspect(p,'AG-00001')
    assert a['status']=='reserved_not_initialized' and not p.exists()

def test_training_integrity_independent_read_only_inspection(tmp_path):
    train_fleet(tmp_path,start=1,end=3,report_every=3)
    s=summary(tmp_path)
    assert s['gradient_trained_ledger_rows']==3
    assert s['gradient_steps_ledger']==6
    assert s['status']=='partial_training'
    for aid in (1,2,3):
        a=inspect(tmp_path,f'AG-{aid:05d}')
        assert a['status']=='trained' and a['byte_hash_verified']
    assert inspect(tmp_path,'AG-01000')['status']=='reserved_not_initialized'

def test_invalid_agent_ids(tmp_path):
    for aid in ('AG-00000','AG-10001','AG-foo','../passwd','AG-1'):
        with pytest.raises(ValueError):inspect(tmp_path,aid)
