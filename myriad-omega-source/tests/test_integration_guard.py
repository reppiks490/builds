"""Negative tests ensuring MYRIAD cannot silently merge or promote synthetic research."""
from pathlib import Path
import os,sys,tempfile,copy
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from hyper_registry import capability
from integration_guard import assess, TARGETS, agent_bank_status
from integration_contract import seal,unseal,ContractError,VERSION

SHA='0'*64

def record():
    return {'schema':VERSION,'source':'myriad','target':'umbra','source_commit_sha256':SHA,
       'as_of_utc':'2026-11-23T10:00:00Z','mode':'synthetic',
       'authority':{'research_only':True,'execution_authorized':False,
                   'production_decision_authorized':False,'auto_promote':False},
       'evidence':{'name':'seeded demonstration','sha256':SHA,'scope':'synthetic_simulation',
                   'observations':['synthetic no production inference']}}

def test_gate_checks_actual_registry_and_holds_integration():
    with tempfile.TemporaryDirectory() as temp:
        p=Path(temp)
        result=assess(root=p,agent_dir=p/'no-agents',ability_dir=p/'no-abilities')
        assert result['passed_gates']==1 and result['status']=='BLOCKED'
        assert not result['automatic_merge_allowed']
        assert result['gates'][0]['id']=='structural_registry' and result['gates'][0]['passed']
        assert not result['gates'][1]['passed'] and not result['gates'][2]['passed']
        assert result['meaningful_abilities_certified']==0
        assert result['targets']['omnigenesis']['base']=='main'
        assert result['targets']['omnigenesis']['pr']==503

def test_10_million_configurations_are_not_certified_skills():
    assert capability(1)['implemented_independent_tool'] is False
    assert capability(10_000_000)['type']=='composable_configuration'

def test_no_automatic_external_side_effects_in_gate():
    import integration_guard
    code=Path(integration_guard.__file__).read_text()
    for forbidden in ('subprocess.run','requests.post','git push','merge_pull_request','urllib.request.urlopen'):
        assert forbidden not in code

def test_guard_does_not_allocate_weight_bank_by_inspecting_absent_path():
    with tempfile.TemporaryDirectory() as t:
        path=Path(t)/'uninitialized'
        x=agent_bank_status(path)
        assert x['trained']==0 and not path.exists()
        assert x['per_agent_parameters']>=400_000

def test_receipt_roundtrip_integrity_no_authority():
    obj=record();sealed=seal(obj)
    assert unseal(sealed)==obj
    assert sealed['hash_scope']=='integrity_only_not_authenticity'

def test_rejects_elevated_trading_authority():
    obj=record();obj['authority']['execution_authorized']=True
    with pytest.raises(ContractError,match='authority'):seal(obj)

def test_rejects_synthetic_real_world_promotion():
    obj=record();obj['evidence']['scope']='offline_research'
    with pytest.raises(ContractError,match='synthetic'):seal(obj)

def test_rejects_forged_integrity_hash():
    obj=record();r=seal(obj);r['payload']['evidence']['name']='altered'
    with pytest.raises(ContractError,match='hash mismatch'):unseal(r)

def test_rejects_extra_fields_and_oversized_observations():
    obj=record();obj['broker_authorized']=True
    with pytest.raises(ContractError):seal(obj)
    obj=record();obj['evidence']['observations']=['x'*501]
    with pytest.raises(ContractError):seal(obj)

def test_rejects_invalid_timestamp_and_source_hash():
    obj=record();obj['as_of_utc']='yesterday'
    with pytest.raises(ContractError):seal(obj)
    obj=record();obj['source_commit_sha256']='not-a-hash'
    with pytest.raises(ContractError):seal(obj)


def test_release_mode_exits_nonzero_for_incomplete_system(tmp_path):
    """A CI job cannot treat a blocked release as a successful authorization."""
    import subprocess
    script = Path(__file__).resolve().parents[1] / 'integration_guard.py'
    result = subprocess.run(
        [sys.executable, str(script), '--require-ready',
         '--agent-bank-dir', str(tmp_path / 'no-agents'),
         '--ability-bank-dir', str(tmp_path / 'no-abilities'),
         '--out', str(tmp_path / 'gate.json')],
        capture_output=True, text=True, timeout=15,
    )
    assert result.returncode == 2
    import json
    report = json.loads((tmp_path / 'gate.json').read_text())
    assert report['status'] == 'BLOCKED'
    assert report['automatic_merge_allowed'] is False
    assert report['repositories_modified'] is False


def test_agent_bank_missing_or_invalid_size_is_not_certified(tmp_path):
    from integration_guard import agent_bank_status
    missing = agent_bank_status(tmp_path / 'not-present')
    assert missing['trained'] == 0
    assert missing['hashed_agent_rows_verified'] == 0
    fake = tmp_path / 'fabricated'
    fake.mkdir()
    (fake / 'agent_weights.fp16').write_bytes(b'fake')
    claimed = agent_bank_status(fake)
    assert claimed['status'] == 'invalid_size'
    assert claimed['hashed_agent_rows_verified'] == 0


def test_readiness_gate_demands_full_row_digest_audit():
    import inspect
    from integration_guard import agent_bank_status
    source = inspect.getsource(agent_bank_status)
    assert 'hashlib.sha256(raw).hexdigest()' in source
    assert 'return result' in source
