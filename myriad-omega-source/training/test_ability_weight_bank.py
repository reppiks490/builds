import tempfile
from pathlib import Path
import numpy as np
import pytest
from training.ability_weight_bank import AbilityBank,WIDTH,_teacher,_initial,PROBE

def test_independent_ability_learning_and_resumability(tmp_path):
    b=AbilityBank(tmp_path, count=109)
    try:
        assert b.status()['trained_synthetic']==0
        result=b.train_range(1,109,steps=8,chunk=17)
        assert result['newly_trained']==109
        assert result['newly_improved_holdout']==109
        assert result['mean_after_new']<result['mean_before_new']
        assert b.status()['trained_synthetic']==109
        a=b.inspect(1);z=b.inspect(109)
        assert a['trained'] and z['trained']
        assert a['weight_sha256']!=z['weight_sha256']
        assert a['holdout_error_after']<a['holdout_error_before']
        assert b.verify_batch(1,17)['verified']
        assert b.train_range(1,109,steps=8,chunk=17)['newly_trained']==0
    finally:b.close()
    b=AbilityBank(tmp_path,count=109)
    try:
        assert b.status()['trained_synthetic']==109
        assert b.verify_batch(103,109)['verified']
    finally:b.close()

def test_training_remains_bounded(tmp_path):
    b=AbilityBank(tmp_path,count=7)
    try:
        with pytest.raises(ValueError):b.inspect(8)
        with pytest.raises(ValueError):b.train_range(7,2)
        assert not b.inspect(1)['trained']
    finally:b.close()

def test_teacher_unique():
    t=_teacher(np.arange(1,1001))
    assert np.unique(t,axis=0).shape[0]==1000
    assert not np.array_equal(_initial([1]),_initial([2]))
