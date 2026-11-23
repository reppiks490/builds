from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pytest
from coordination.check_ownership import load_contract, owner_of, validate

def test_no_ambiguous_ownership_for_actual_paths():
    root=Path(__file__).resolve().parents[1]
    contract=load_contract()
    examples=[p.relative_to(root).as_posix() for p in root.rglob('*.py') if not {'__pycache__','.pytest_cache'}.intersection(p.parts)]
    for x in examples:
        owner_of(x,contract)

def test_each_head_can_only_commit_its_own_subsystem():
    assert validate('HEAD_A',['docs/HANDOFF.md','index.html'])['status']=='PASS'
    assert validate('HEAD_B',['training/individual_weight_bank.py','tests/test_independent_eval.py'])['status']=='PASS'
    assert validate('HEAD_C',['server.py','provider_budget.py','tests/test_provider_budget.py'])['status']=='PASS'
    assert validate('HEAD_B',['server.py'])['status']=='BLOCKED'
    assert validate('HEAD_C',['docs/KNOWN_GAPS.md'])['status']=='BLOCKED'
    assert validate('HEAD_A',['training/adaptive_sandbox.py'])['status']=='BLOCKED'
    assert validate('HEAD_A',['unassigned/file.py'])['status']=='BLOCKED'

def test_disallows_traversal_and_overlap():
    for bad in ('/tmp/key.txt','../Icarus/README.md','a/../../b','a\\b'):
        with pytest.raises(ValueError):owner_of(bad)
    contract=load_contract()
    contract['rules']['HEAD_B'].append('server.py')
    with pytest.raises(ValueError,match='Ambiguous'):
        owner_of('server.py',contract)
