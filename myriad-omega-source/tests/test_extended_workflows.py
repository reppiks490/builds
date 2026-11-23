import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from operations import run_operation

def test_all_hundred_workflows_execute_real_offline_demo():
    for i in range(1,101):
        name=f'W{i:02d}'
        a=run_operation(name)
        b=run_operation(name)
        assert a==b, name
        assert a['operation']=='local_deterministic_demo'
        assert len(a['evidence_hash'])==16
        assert a['output'].get('sample_implemented') is not False
        assert a['output'].get('type')!='workflow_contract_preview_only'

def test_trading_demos_never_execute_orders_and_detect_leakage():
    assert run_operation('W91')['output']['orders_placed']==0
    assert run_operation('W93')['output']['real_orderbook_replay'] is False
    assert run_operation('W94')['output']['reject_backtest'] is True

def test_adversarial_approval_is_fail_closed():
    assert not run_operation('W87')['output']['benchmark_pass']
    assert not run_operation('W100')['output']['promote']
    assert not run_operation('W99')['output']['agent_can_merge']
