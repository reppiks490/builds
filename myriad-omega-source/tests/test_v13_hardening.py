"""New negative evidence tests for next-session continuity and release safety."""
from pathlib import Path
import hashlib
import json
import pytest
from evidence_vault import EvidenceVault, sha
from training.transfer_adaptation import audit_candidates


def test_vault_prevents_cross_workflow_agent_impersonation(tmp_path):
    vault=EvidenceVault(tmp_path/'ledger.sqlite3')
    try:
        def record(agent, workflow):
            return vault.record(job_id='M-0123456789',agent_id=agent,workflow=workflow,
                                brain='NOESIS',model_id='fixture',request_sha256=sha('prompt'),
                                response_sha256=sha('answer'),answer='answer')
        with pytest.raises(ValueError,match='Workflow does not own'):record('AG-00101','W01')
        with pytest.raises(ValueError,match='Invalid workflow'):record('AG-00001','W999')
        assert record('AG-00101','W02')['recorded']
    finally:vault.close()


def test_candidate_audit_rejects_orphan_files(tmp_path):
    (tmp_path/'AG-00001-S1-E1.fp16').write_bytes(b'partial')
    verdict=audit_candidates(tmp_path)
    assert verdict['all_valid'] is False
    assert verdict['untracked_weight_files']==1


def test_candidate_audit_rejects_stale_pending_file(tmp_path):
    (tmp_path/'AG-00001-S1-E1.pending').write_bytes(b'incomplete')
    verdict=audit_candidates(tmp_path)
    assert not verdict['all_valid']


def test_candidate_audit_rejects_report_without_weight(tmp_path):
    name='AG-00001-S5-E2.fp16'
    (tmp_path/(name+'.json')).write_text(json.dumps({'checkpoint':name,'agent':'AG-00001'}))
    result=audit_candidates(tmp_path)
    assert not result['all_valid']
