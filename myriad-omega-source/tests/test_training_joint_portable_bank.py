"""Restore real agent + adapter checkpoint bytes into clean separate full banks."""
import json
from zipfile import ZipFile, ZIP_DEFLATED

import pytest

from training.individual_weight_bank import WeightBank
from training.ability_weight_bank import AbilityBank
from training.portable_bank_bundle import export_joint,restore_joint
from training.coupled_bank_training import verify_ability_span


def make_fixture(tmp_path):
    root=tmp_path/'original';ab=root/'abilities';agents=root/'agents'
    a=WeightBank(agents)
    try:
        a.train_one(1,steps=2,samples=24)
        a.train_one(2,steps=2,samples=24)
    finally:a.close()
    b=AbilityBank(ab,count=2000)
    try:
        b.train_range(1,2000,steps=8,chunk=2000)
    finally:b.close()
    return agents,ab


def test_joint_export_restores_clean_bytes_without_forged_mastery(tmp_path):
    agents, abilities=make_fixture(tmp_path)
    bundle=tmp_path/'checkpoint.zip'
    exp=export_joint(agents,abilities,bundle,start=1,end=2,ability_count=2000)
    assert exp['exported_agents']==2
    assert exp['exported_synthetic_ability_vectors']==2000
    with pytest.raises(PermissionError):
        restore_joint(bundle,tmp_path/'restore/a',tmp_path/'restore/b',ability_count=2000)
    restore=restore_joint(bundle,tmp_path/'restore/a',tmp_path/'restore/b',
                          ability_count=2000,approve_write=True)
    assert restore['agent_rows_restored_as_unverified_imports']==2
    assert restore['ability_rows_restored_as_synthetic_only']==2000
    a=WeightBank(tmp_path/'restore/a')
    b=AbilityBank(tmp_path/'restore/b',count=2000)
    try:
        assert a.status(1)['status']=='imported_unverified' and a.verify(2)
        assert verify_ability_span(b,1,1000)['verified']
        assert verify_ability_span(b,1001,2000)['verified']
    finally:b.close();a.close()
    again=restore_joint(bundle,tmp_path/'restore/a',tmp_path/'restore/b',
                         ability_count=2000,approve_write=True)
    assert again['agent_rows_restored_as_unverified_imports']==0
    assert again['ability_rows_restored_as_synthetic_only']==0


def test_joint_bundle_tamper_refused_before_any_new_checkpoint(tmp_path):
    agents,abilities=make_fixture(tmp_path)
    original=tmp_path/'original.zip';export_joint(agents,abilities,original,start=1,end=2,ability_count=2000)
    with ZipFile(original) as z:
        entries={name:z.read(name) for name in z.namelist()}
    corrupt=bytearray(entries['ability_weights.fp16']);corrupt[39]^=1
    entries['ability_weights.fp16']=bytes(corrupt)
    forged=tmp_path/'bad.zip'
    with ZipFile(forged,'w',ZIP_DEFLATED) as z:
        for name,payload in entries.items():z.writestr(name,payload)
    dest=tmp_path/'restore'
    with pytest.raises(ValueError,match='shape or digest invalid'):
        restore_joint(forged,dest/'a',dest/'b',ability_count=2000,approve_write=True)
    assert not dest.exists()