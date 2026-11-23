import hashlib
import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from training.transfer_adaptation import train_candidate,audit_candidates


def test_candidate_training_requires_real_bank_and_preserves_baseline(tmp_path):
    bank=Path(__file__).resolve().parents[1]/'training'/'agentbank'
    if not (bank/'weight_ledger.sqlite3').exists():pytest.skip('Full trained agent bank excluded')
    source_file=bank/'agent_weights.fp16'
    # Only fingerprint the selected source row (not the entire 8.22GB bank).
    with source_file.open('rb') as f:original=hashlib.sha256(f.read(822000)).hexdigest()
    result=train_candidate(1,bank,tmp_path,steps=2,batch=16)
    with source_file.open('rb') as f:after=hashlib.sha256(f.read(822000)).hexdigest()
    assert original==after
    assert result['candidate_sha256']!=result['source_sha256']
    assert result['auto_promote'] is False
    assert result['real_world_qualified'] is False
    assert result['parameters_per_candidate']==411000
    assert audit_candidates(tmp_path)['all_valid']
    with pytest.raises(FileExistsError):train_candidate(1,bank,tmp_path,steps=2,batch=16)
    p=tmp_path/result['checkpoint'];p.write_bytes(b'corrupted')
    assert audit_candidates(tmp_path)['all_valid'] is False


def test_bad_training_limits_refused(tmp_path):
    with pytest.raises(ValueError):train_candidate(1,'unused',tmp_path,steps=1000)
    with pytest.raises(ValueError):train_candidate(10001,'unused',tmp_path)
