"""Fail-closed real checkpoint import + two-bank conditional training tests."""
import hashlib
import json
from pathlib import Path
import zipfile

import numpy as np
import pytest

from training.bank_bridge import import_sample,inspect_bank_paths,validate_sample
from training.coupled_bank_training import ability_range,train_coupled_candidate,verify_candidate
from training.individual_weight_bank import WeightBank, BYTES_PER_AGENT
from training.ability_weight_bank import AbilityBank


def demo_sample(tmp_path):
    from training.individual_weight_bank import WeightBank
    from training.portable_policy_demo import build_sample
    bank=tmp_path/'original'
    source=WeightBank(bank,max_agents=2)
    try:
        source.train_one(1,steps=2,samples=24)
        source.train_one(2,steps=2,samples=24)
    finally:source.close()
    # build_sample expects source ledger and contiguous flat weights, for agents 1-2.
    path=tmp_path/'sample.zip'
    build_sample(bank,path,agents=(1,2))
    return path


def test_verified_sample_import_is_strictly_unqualified_until_new_gradient_training(tmp_path):
    sample=demo_sample(tmp_path)
    target=tmp_path/'target'
    assert inspect_bank_paths(target,tmp_path/'absent')['agent_bank']['present'] is False
    r=import_sample(sample,target,max_agents=2)
    assert r['agents_imported']==2
    assert r['imported_rows_qualify_as_independently_verified_training'] is False
    b=WeightBank(target,max_agents=2)
    try:
        assert b.status(1)['status']=='imported_unverified'
        assert b.summary()['trained_agents']==0
        assert b.verify(1) and b.verify(2)
        assert b.train_one(1,steps=2,samples=24)['verified']
        assert b.status(1)['status']=='trained'
    finally:b.close()
    # Imported weights never collide with existing updated weights.
    with pytest.raises(RuntimeError,match='conflicts'):
        import_sample(sample,target,max_agents=2)


def test_sample_idempotency_and_forgery_rejected(tmp_path):
    sample=demo_sample(tmp_path)
    target=tmp_path/'target'
    import_sample(sample,target,max_agents=2)
    assert import_sample(sample,target,max_agents=2)['agents_already_present_and_matching']==2
    with zipfile.ZipFile(sample) as z:
        m=json.loads(z.read('manifest.json'))
        weights=bytearray(z.read('weights.fp16'))
    weights[17]^=1
    bad=tmp_path/'bad.zip'
    with zipfile.ZipFile(bad,'w') as z:
        z.writestr('manifest.json',json.dumps(m))
        z.writestr('weights.fp16',weights)
    with pytest.raises(ValueError,match='integrity mismatch'):
        validate_sample(bad)


def test_agent_ability_partition_is_injective_and_bounded():
    assert ability_range(1,1000)==(1,1000)
    assert ability_range(2,1000)==(1001,2000)
    assert ability_range(10000,1000)==(9999001,10000000)
    with pytest.raises(ValueError):ability_range(10001)
    with pytest.raises(ValueError):ability_range(2,1001)
    with pytest.raises(ValueError):ability_range(2,4,available=1000)


def test_paired_training_uses_both_real_banks_and_never_promotes(tmp_path):
    sample=demo_sample(tmp_path)
    target=tmp_path/'fleet'
    ab_dir=tmp_path/'ability'
    out_dir=tmp_path/'candidate'
    import_sample(sample,target,max_agents=2)
    source=WeightBank(target,max_agents=2)
    try:
        prior=source.status(2)['sha256']
    finally:source.close()
    # coupled trainer demands a full fleet-sized bank, not a 2-row test bank.
    # Create a full-layout bank with the imported rows instead.
    full=tmp_path/'full'
    import_sample(sample,full)
    a=AbilityBank(ab_dir,count=2000)
    try:
        assert a.status()['trained_synthetic']==0
    finally:a.close()
    record=train_coupled_candidate(2,full,ab_dir,out_dir,slots=4,steps=2,
                                  samples=24,ability_count=2000,approve_ability_training=True)
    assert record['ability_id_range']==[1001,1004]
    assert record['new_ability_rows_trained_synthetic']==4
    assert record['agent_parameters_updated_by_backprop']==411000
    assert record['automatic_promotion'] is False and record['base_agent_weights_overwritten'] is False
    assert verify_candidate(out_dir,record['checkpoint']+'.json',full,ab_dir,ability_count=2000)['valid']
    b=WeightBank(full)
    try:assert b.status(2)['sha256']==prior
    finally:b.close()
    with pytest.raises(FileExistsError):
        train_coupled_candidate(2,full,ab_dir,out_dir,slots=4,steps=2,
                                samples=24,ability_count=2000,approve_ability_training=True)
    data=out_dir/record['checkpoint']
    with data.open('r+b') as f:
        first=f.read(1);f.seek(0);f.write(bytes([first[0]^1]))
    with pytest.raises(RuntimeError,match='tampered'):
        verify_candidate(out_dir,record['checkpoint']+'.json',full,ab_dir,ability_count=2000)


def test_large_historic_batch_subspan_attaches_without_retraining(tmp_path):
    from training.coupled_bank_training import verify_ability_span
    b=AbilityBank(tmp_path,count=1200)
    try:
        b.train_range(1,1200,steps=8,chunk=1200)
        # Historic proof is a single batch; each agent sees only a subspan.
        assert not b.verify_batch(1,4)['verified']
        assert verify_ability_span(b,1,4)['verified']
        assert verify_ability_span(b,1001,1004)['verified']
        with pytest.raises(ValueError,match='Invalid ability slice'):
            verify_ability_span(b,1,1201)
    finally:b.close()


def test_coupled_runner_requires_approval_and_recovers(tmp_path):
    from training.run_coupled_fleet import run_range
    src=demo_sample(tmp_path)
    agent_bank=tmp_path/'bank';ability_bank=tmp_path/'abilities';output=tmp_path/'out'
    import_sample(src,agent_bank)
    with pytest.raises(PermissionError):
        run_range(agent_bank,ability_bank,output,start=1,end=2,slots=4,ability_count=2000)
    record=run_range(agent_bank,ability_bank,output,start=1,end=2,slots=4,steps=2,
                     samples=24,ability_count=2000,approve_training=True)
    assert record['status']=='completed_quarantined_training_only'
    assert record['new_agent_candidates']==2 and record['new_ability_rows_trained_synthetic']==8
    second=run_range(agent_bank,ability_bank,output,start=1,end=2,slots=4,steps=2,
                      samples=24,ability_count=2000,approve_training=True)
    assert second['new_agent_candidates']==0 and second['existing_verified_candidates']==2
    filename=f'AG-00001-CAP-00000001-00000004-S2078-E2.fp16'
    with (output/filename).open('r+b') as f:
        old=f.read(1);f.seek(0);f.write(bytes([old[0]^1]))
    with pytest.raises(RuntimeError,match='tampered'):
        run_range(agent_bank,ability_bank,output,start=1,end=2,slots=4,steps=2,
                  samples=24,ability_count=2000,approve_training=True)
    assert json.loads((output/'COUPLED_FLEET_PROGRESS.json').read_text())['status']=='interrupted_or_blocked'