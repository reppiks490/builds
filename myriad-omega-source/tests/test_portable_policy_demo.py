import json
from zipfile import ZipFile, ZIP_DEFLATED
import pytest
import torch
from training.individual_weight_bank import WeightBank
from training.portable_policy_demo import build_sample, predict_from_sample


def test_portable_policy_rows_validate_and_compute(tmp_path):
    torch.set_num_threads(1)
    bank=WeightBank(tmp_path/'bank', max_agents=3)
    try:
        for id in (1,2):bank.train_one(id,steps=1,samples=16)
    finally:bank.close()
    p=tmp_path/'sample.zip'
    m=build_sample(tmp_path/'bank',p,agents=(2,1))
    assert len(m['rows'])==2
    assert predict_from_sample(p,2)['actual_trained_neural_weights_used']
    assert predict_from_sample(p,1)['external_actions_executed']==0
    with pytest.raises(ValueError,match='not present'):predict_from_sample(p,3)
    with ZipFile(p) as z:
        raw=bytearray(z.read('weights.fp16'))
        manifest=z.read('manifest.json')
    raw[0]^=1
    bad=tmp_path/'bad.zip'
    with ZipFile(bad,'w',ZIP_DEFLATED) as z:
        z.writestr('manifest.json',manifest)
        z.writestr('weights.fp16',raw)
    with pytest.raises(ValueError,match='hash mismatch'):predict_from_sample(bad,1)


def test_invalid_sample_ids(tmp_path):
    with pytest.raises(ValueError):build_sample(tmp_path,tmp_path/'no.zip',agents=(1,1))
