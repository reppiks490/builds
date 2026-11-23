from pathlib import Path
import json
import sys
import tempfile
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pytest
from training.independent_eval import DOMAINS, generate_case,run,verify_run,EvaluationError,cli

class CompleteStub:
    """Controlled grader fixture, not real intelligence: only for wiring tests."""
    def __init__(self,answers):self.answers=answers;self.calls=[]
    def inspect(self,brain):return {'status':'ready','backend':'scripted_fixture','model':'not_an_llm'}
    def chat(self,brain,messages,max_tokens=90):
        self.calls.append((brain,messages))
        return str(self.answers[messages[-1]['content']])

SEED='f1d2d3d4e5f6a1a2b3c4d5e6f7a8b9c0'

def test_sealed_holdout_weights_across_all_domains():
    cases=[generate_case(SEED,i) for i in range(10)]
    assert set(x.domain for x in cases)==set(DOMAINS)
    assert all(isinstance(x.expected,int) and 'Return only' in x.prompt for x in cases)
    assert [x for x in cases]==[generate_case(SEED,i) for i in range(10)]
    assert cases!=[generate_case('A'*32,i) for i in range(10)]

def test_requires_consent_and_model_is_online_without_any_calls():
    f=CompleteStub({})
    with tempfile.TemporaryDirectory() as tmp:
        with pytest.raises(EvaluationError,match='allow-provider-calls'):
            run(f,brains=['NOESIS'],case_count=5,output_root=tmp)
        assert not f.calls and not list(Path(tmp).iterdir())
        with patch.object(f,'inspect',return_value={'status':'offline'}):
            with pytest.raises(EvaluationError,match='unavailable'):
                run(f,brains=['NOESIS'],case_count=5,output_root=tmp,allow_provider_calls=True)
        assert not f.calls

def test_actual_gateway_calls_bounded_and_receipt_not_model_self_scored():
    cases=[generate_case(SEED,i) for i in range(10)]
    answers={c.prompt:c.expected for c in cases}
    f=CompleteStub(answers)
    with tempfile.TemporaryDirectory() as tmp:
        result=run(f,brains=['NOESIS','AEGIS'],case_count=10,output_root=tmp,allow_provider_calls=True,private_seed=SEED)
        record=result['receipt'];folder=Path(result['path'])
        assert record['actual_requests']==20 and record['status']=='completed_synthetic_holdout'
        assert len(f.calls)==20
        assert all('expected' not in str(call) for call in f.calls)
        assert all(v['correct']==2 for v in record['per_domain']['NOESIS'].values())
        assert not record['general_intelligence_certified'] and not record['auto_promote']
        assert not any('expected' in str(x) for x in record['rows'])
        assert 'PRIVATE_HOLDOUT_KEY' not in (folder/'PUBLIC_RESULTS.json').read_text()
        assert SEED not in (folder/'PUBLIC_RESULTS.json').read_text()
        assert 'expected' in (folder/'PRIVATE_HOLDOUT_KEY.json').read_text()
        assert oct((folder/'PRIVATE_HOLDOUT_KEY.json').stat().st_mode & 0o777)=='0o600'
        assert json.loads((folder/'PUBLIC_RESULTS.json').read_text())==record
        assert verify_run(folder)['graded_rows']==20

def test_unparseable_and_provider_failure_stop_later_calls():
    class BreakStub(CompleteStub):
        def chat(self,brain,messages,max_tokens=90):
            self.calls.append(1)
            if len(self.calls)==3:raise OSError('test provider offline')
            return 'I think it is 42'  # never interpret an answer extracted from prose
    f=BreakStub({})
    with tempfile.TemporaryDirectory() as tmp:
        result=run(f,brains=['NOESIS','AEGIS'],case_count=10,output_root=tmp,allow_provider_calls=True,private_seed=SEED)
        assert len(f.calls)==3
        assert result['receipt']['status']=='partial_provider_failure'
        assert [x['state'] for x in result['receipt']['rows']]==['unparseable','unparseable','provider_error']

def test_invalid_plans_are_rejected_and_cli_fails_closed():
    f=CompleteStub({})
    with tempfile.TemporaryDirectory() as t:
        for brains,count in [(['NOESIS','NOESIS'],5),(['BOGUS'],5),(['NOESIS'],0),(['NOESIS'],41)]:
            with pytest.raises(EvaluationError):run(f,brains=brains,case_count=count,output_root=t,allow_provider_calls=True)
        assert not f.calls
        assert cli(['--brain','NOESIS','--cases','5','--out',t])==2


def test_independent_grader_rejects_forged_correctness_and_transcripts():
    cases=[generate_case(SEED,i) for i in range(5)]
    f=CompleteStub({c.prompt:c.expected for c in cases})
    with tempfile.TemporaryDirectory() as tmp:
        out=run(f,brains=['NOESIS'],case_count=5,output_root=tmp,allow_provider_calls=True,private_seed=SEED)
        folder=Path(out['path'])
        assert verify_run(folder)['verified'] is True
        pub=folder/'PUBLIC_RESULTS.json'
        record=json.loads(pub.read_text())
        record['rows'][0]['correct']=False
        pub.write_text(json.dumps(record))
        with pytest.raises(EvaluationError,match='Response score'):verify_run(folder)
        record['rows'][0]['correct']=True
        pub.write_text(json.dumps(record))
        transcripts=folder/'PRIVATE_TRANSCRIPTS.json'
        body=json.loads(transcripts.read_text())
        body['transcripts'][0]['response']='-999'
        transcripts.write_text(json.dumps(body))
        with pytest.raises(EvaluationError,match='checksum'):verify_run(folder)
