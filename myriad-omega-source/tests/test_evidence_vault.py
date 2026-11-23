"""Durability, audit and fail-closed tests for untrusted provider memory."""
import hashlib
import sqlite3
import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from evidence_vault import EvidenceVault, IntegrityError, sha


def example(vault, *, job='M-0123456789', brain='NOESIS', answer='candidate explanation, not verified',agent='AG-00001'):
    return vault.record(job_id=job,agent_id=agent,workflow='W01',brain=brain,
       model_id='local-fixture:1',request_sha256=sha('prompt'),
       response_sha256=sha(answer),answer=answer)


def test_durable_read_only_memory_and_explicit_untrusted_scope(tmp_path):
    file=tmp_path/'vault.sqlite3';v=EvidenceVault(file)
    try:
        first=example(v)
        assert first['recorded'] is True
        again=example(v)
        assert again['recorded'] is False
        assert first['receipt_sha256']==again['receipt_sha256']
        example(v,brain='AEGIS',answer='model critique, not independent review')
        assert v.summary()['observations']==2
        assert v.summary()['trusted_claims']==0
        assert v.audit()['all_valid']
        assert len(v.agent_history('AG-00001')['records'])==2
        assert v.agent_history('AG-00002')['records']==[]
    finally:v.close()
    reopened=EvidenceVault(file)
    try:
        assert reopened.audit()['verified']==2
        assert reopened.agent_history('AG-00001')['accepted_as_truth'] is False
    finally:reopened.close()


def test_conflicting_replay_rejected(tmp_path):
    v=EvidenceVault(tmp_path/'vault.sqlite3')
    try:
        example(v)
        with pytest.raises(IntegrityError):example(v,answer='new model result with different hash')
        with pytest.raises(IntegrityError):v.record(job_id='M-0123456789',agent_id='AG-00001',
          workflow='W01',brain='NOESIS',model_id='local-fixture:1',
          request_sha256=sha('different prompt'),response_sha256=sha('candidate explanation, not verified'),
          answer='candidate explanation, not verified')
        assert v.summary()['observations']==1
    finally:v.close()


def test_cannot_forge_response_checksum(tmp_path):
    v=EvidenceVault(tmp_path/'vault.sqlite3')
    try:
        with pytest.raises(IntegrityError):v.record(job_id='M-0123456789',agent_id='AG-00001',
             workflow='W01',brain='METIS',model_id='test:1',request_sha256=sha('prompt'),
             response_sha256='a'*64,answer='wrong')
        assert v.summary()['observations']==0
    finally:v.close()


def test_tampered_row_refused_on_restart(tmp_path):
    path=tmp_path/'vault.sqlite3';v=EvidenceVault(path);example(v);v.close()
    db=sqlite3.connect(path)
    db.execute("UPDATE observations SET excerpt='tampered' WHERE seq=1")
    db.commit();db.close()
    with pytest.raises(IntegrityError):EvidenceVault(path)


def test_tail_deletion_detected_by_separate_anchor(tmp_path):
    path=tmp_path/'vault.sqlite3';v=EvidenceVault(path)
    example(v);example(v,brain='AEGIS');v.close()
    db=sqlite3.connect(path)
    db.execute('DELETE FROM observations WHERE seq=2');db.commit();db.close()
    with pytest.raises(IntegrityError):EvidenceVault(path)


def test_agent_id_and_budget_restrictions(tmp_path):
    v=EvidenceVault(tmp_path/'vault.sqlite3')
    try:
        with pytest.raises(ValueError):v.agent_history('AG-99999')
        with pytest.raises(ValueError):v.agent_history('AG-00001',limit=10000000)
        with pytest.raises(ValueError):example(v,agent='AG-99999')
    finally:v.close()
