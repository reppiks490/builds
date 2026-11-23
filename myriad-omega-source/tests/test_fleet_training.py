"""Resumability, true gradient evidence and integrity blocking, on tiny range."""
import json,sys,torch
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from training.fleet_trainer import train_fleet
from training.individual_weight_bank import WeightBank, PARAMETERS

def test_resumable_training_and_distinct_full_weight_vectors(tmp_path):
    out=train_fleet(tmp_path,start=1,end=3,steps=2,samples=24,report_every=2)
    assert out['agents_trained_this_run']==3
    assert out['bank_summary']['trained_agents']==3
    b=WeightBank(tmp_path)
    try:
        weights=[]
        for i in (1,2,3):
            st=b.status(i)
            assert st['status']=='trained' and st['steps']==2 and st['baseline_loss']>st['final_loss']
            assert b.verify(i)
            model=b.load_model(i)
            assert sum(p.numel() for p in model.parameters())==PARAMETERS
            weights.append(st['sha256'])
        assert len(set(weights))==3
    finally:b.close()
    out=train_fleet(tmp_path,start=1,end=3,steps=2,samples=24,report_every=2)
    assert out['agents_trained_this_run']==0
    assert out['previously_trained_and_verified']==3

def test_bank_tampering_rejected_on_resume(tmp_path):
    train_fleet(tmp_path,start=1,end=1,steps=2,samples=24)
    weight=tmp_path/'agent_weights.fp16'
    with weight.open('r+b') as f:
        first=f.read(1);f.seek(0);f.write(bytes([first[0]^1]))
    with pytest.raises(RuntimeError,match='corruption'):
        train_fleet(tmp_path,start=1,end=1)
    report=json.loads((tmp_path/'FLEET_TRAINING_PROGRESS.json').read_text())
    assert report['status']=='interrupted_or_blocked'

def test_range_safety(tmp_path):
    with pytest.raises(ValueError):train_fleet(tmp_path,start=0,end=3)
    with pytest.raises(ValueError):train_fleet(tmp_path,start=1,end=10001)
    with pytest.raises(ValueError):train_fleet(tmp_path,start=1,end=1,steps=0)
