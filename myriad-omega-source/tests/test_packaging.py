from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile
from tools.package_source import allowed, build


def test_source_release_denylist():
    assert allowed(Path('training/fleet_trainer.py'))
    for name in ['training/agentbank/agent_weights.fp16',
                 'training/abilitybank/weights.fp16',
                 'evaluation_runs/EVAL-123/PRIVATE_HOLDOUT_KEY.json',
                 'evaluation_runs/EVAL-123/PRIVATE_TRANSCRIPTS.json',
                 'training/adaptive_candidates/a.safetensors',
                 'myriad_events.sqlite3', 'model_cache/qwen/model.gguf',
                 '.env', 'foo/.env.secret', 'private/key.pt',
                 'tests/__pycache__/whatever.pyc', '../secrets']:
        assert not allowed(Path(name)), name


def test_source_zip_is_deterministic_and_has_no_weights():
    with TemporaryDirectory() as temp:
        a,b=Path(temp)/'a.zip',Path(temp)/'b.zip'
        p=build(a)
        build(b)
        assert a.read_bytes() == b.read_bytes()
        assert p['fully_trained_portable_deployment'] is False
        with ZipFile(a) as z:
            files=z.namelist()
            assert any(name.endswith('/README.md') for name in files)
            assert any(name.endswith('/RELEASE_MANIFEST.json') for name in files)
            assert not any('/agentbank/' in name or '/abilitybank/' in name or '/adaptive_candidates/' in name for name in files)
            assert not any(name.endswith('.sqlite3') or name.endswith('.fp16') for name in files)
