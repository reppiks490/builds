"""Test entire 1k pipeline surface, deterministic evidence and non-mutating semantics."""
from pathlib import Path
import sys,pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pipeline_runtime import run_pipeline,summary,sha

def test_all_1000_pipelines_have_real_bounded_sample_output():
    digests=set()
    for i in range(1,1001):
        p=f'P{i:04d}'
        a=run_pipeline(p)
        assert a==run_pipeline(p)
        assert a['external_side_effects'] is False
        assert a['real_model_calls']==0 and a['training_steps']==0
        assert a['qualified_mastery'] is False
        h=a.pop('receipt_sha256')
        assert sha(a)==h and h not in digests
        digests.add(h)
    assert summary()['sample_executable']==1000

def test_validation_rejects_unknown_or_malformed_pipeline():
    for val in ('P0000','P1001','P10001','../P1','',None):
        with pytest.raises(ValueError):run_pipeline(val)

def test_critical_pipeline_verification_cases():
    assert run_pipeline('P0004')['detail']['replay_matches'] # W01 simulate
    assert run_pipeline('P0005')['detail']['tamper_detected']
    assert run_pipeline('P0008')['detail']['replay_deterministic']
    assert not run_pipeline('P1000')['detail']['auto_promote']
