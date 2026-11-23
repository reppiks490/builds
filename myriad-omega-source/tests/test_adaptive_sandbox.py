"""Isolated agent candidate training, hash-chain integrity and no promotion."""
from pathlib import Path
import sys,hashlib,torch
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from training.fleet_trainer import train_fleet
from training.adaptive_sandbox import AdaptiveSandbox

def test_quarantined_self_learning_does_not_touch_baseline(tmp_path):
    torch.set_num_threads(1)
    bank=tmp_path/'baseline';out=tmp_path/'proposals'
    train_fleet(bank,start=1,end=2)
    before=hashlib.sha256((bank/'agent_weights.fp16').open('rb').read(822000)).hexdigest()
    engine=AdaptiveSandbox(bank,out)
    try:
        r=engine.propose(1,steps=2)
        assert r['candidate_status'].startswith('quarantined_')
        assert r['agent_baseline_untouched']
        assert (out/(r['id']+'.fp16')).exists()
        a=engine.audit()
        assert a['all_valid'] and a['verified_proposals']==1
        assert engine.summary()['auto_promotions']==0
        # New candidate for same agent forms chained learning memory.
        q=engine.propose(1,steps=2,seed=5062)
        assert q['prior_receipt']==r['receipt_sha256']
        assert engine.audit()['verified_proposals']==2
    finally:engine.close()
    after=hashlib.sha256((bank/'agent_weights.fp16').open('rb').read(822000)).hexdigest()
    assert before==after

def test_detects_tampered_candidate(tmp_path):
    train_fleet(tmp_path/'bank',start=1,end=1)
    t=AdaptiveSandbox(tmp_path/'bank',tmp_path/'out')
    try:
        r=t.propose(1)
        path=Path(r['checkpoint_path'])
        with path.open('r+b') as f:
            v=f.read(1);f.seek(0);f.write(bytes([v[0]^1]))
        assert not t.audit()['all_valid']
    finally:t.close()
