import hashlib
import tarfile
from pathlib import Path
from tools.snapshot_source import snapshot

def test_snapshot_excludes_weights_secrets_and_reconstructs(tmp_path):
    root=tmp_path/'project';root.mkdir()
    (root/'server.py').write_text('print("ok")\n')
    (root/'README.md').write_text('source\n')
    (root/'training').mkdir();(root/'training'/'agentbank').mkdir()
    (root/'training'/'agentbank'/'agent_weights.fp16').write_bytes(b'secret model weights')
    (root/'training'/'credentials.env').write_text('KEY=SECRET')
    info=snapshot(root,tmp_path/'out')
    assert info['source_files']==3  # server, readme, manifest
    assert info['compressed_bytes']>0
    assert info['portable_zip_bytes']>0
    assert len(info['compressed_sha256'])==64
    assert all(x!='agent_weights.fp16' for x in info['parts'])
