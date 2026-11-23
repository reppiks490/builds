"""Synthetic candidate stress evaluation with independent recomputation."""
import json
from zipfile import ZipFile

import pytest

from training.individual_weight_bank import WeightBank
from training.ability_weight_bank import AbilityBank
from training.coupled_bank_training import train_coupled_candidate
from training.candidate_stress_eval import evaluate, verify_report, write_report


def fixture(tmp_path):
    a=tmp_path/'agents';b=tmp_path/'abilities';c=tmp_path/'candidates'
    bank=WeightBank(a)
    try:bank.train_one(1, steps=2, samples=24)
    finally:bank.close()
    record=train_coupled_candidate(1,a,b,c,slots=1000,steps=2,samples=24,
                                   seed=407,ability_count=1000,approve_ability_training=True)
    return a,b,c,record


def test_stress_report_verifies_against_live_weights_and_never_promotes(tmp_path):
    a,b,c,r=fixture(tmp_path)
    before=(a/'agent_weights.fp16').stat().st_mtime_ns
    report=evaluate(a,b,c,agents=[1],ability_count=1000,examples=24)
    assert report['agents_examined']==1
    assert len(report['records'][0]['scenarios'])==4
    assert report['general_intelligence_certified'] is False
    assert report['automatic_promotion'] is False
    assert not report['records'][0]['auto_promoted']
    path=tmp_path/'evidence.json'
    write_report(report,path)
    assert verify_report(path,a,b,c,ability_count=1000)['verified']
    assert (a/'agent_weights.fp16').stat().st_mtime_ns==before
    with pytest.raises(FileExistsError):write_report(report,path)


def test_report_forgery_and_candidate_tampering_are_rejected(tmp_path):
    a,b,c,record=fixture(tmp_path)
    report=evaluate(a,b,c,agents=[1],ability_count=1000,examples=16)
    target=tmp_path/'evidence.json';write_report(report,target)
    fake=json.loads(target.read_text());fake['records'][0]['scenarios']['normal']['candidate_mse']=0
    target.write_text(json.dumps(fake))
    with pytest.raises(ValueError,match='digest mismatch'):
        verify_report(target,a,b,c,ability_count=1000)
    target.write_text(json.dumps(report))
    with (c/record['checkpoint']).open('r+b') as f:
        first=f.read(1);f.seek(0);f.write(bytes([first[0]^1]))
    with pytest.raises(RuntimeError,match='tampered'):
        verify_report(target,a,b,c,ability_count=1000)


def test_stress_scope_limits_and_no_unavailable_agent_fabrication(tmp_path):
    a,b,c,r=fixture(tmp_path)
    for args in ([],[1,1],[0],[10001],list(range(1,102))):
        with pytest.raises(ValueError):evaluate(a,b,c,agents=args,ability_count=1000)
    with pytest.raises(RuntimeError,match='missing/corrupt'):
        evaluate(a,b,c,agents=[2],ability_count=1000)