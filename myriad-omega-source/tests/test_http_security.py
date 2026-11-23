import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from http_security import localhost_host_allowed

def test_hosts_restrict_dns_rebinding_and_invalid_port():
    for host in ('127.0.0.1','localhost','localhost:8788','127.0.0.1:8789','[::1]','[::1]:8788'):
        assert localhost_host_allowed(host),host
    for host in ('evil.example','127.0.0.1.evil.example','evil.example:8788','localhost:99999',
                 'evil.example@127.0.0.1','127.0.0.1:0','127.0.0.1/path','127.0.0.1\r\nx-host:evil',''):
        assert not localhost_host_allowed(host),host

from http_security import mutation_request_allowed

def test_mutation_requires_same_scheme_host_port_and_json():
    assert mutation_request_allowed('127.0.0.1:8788','','application/json')
    assert mutation_request_allowed('127.0.0.1:8788','http://127.0.0.1:8788','application/json; charset=utf8')
    assert mutation_request_allowed('localhost:8788','http://localhost:8788','application/json')
    for origin in ['https://attacker.test','http://localhost:1','http://127.0.0.1:9999',
                   'null','file:///tmp/index.html','http://127.0.0.1:8788.attacker.test',
                   'https://127.0.0.1:8788/path','http://evil@127.0.0.1:8788']:
        assert not mutation_request_allowed('127.0.0.1:8788',origin,'application/json'),origin
    for mime in ['text/plain','application/x-www-form-urlencoded','multipart/form-data','']:
        assert not mutation_request_allowed('127.0.0.1:8788','',''+mime)
    assert not mutation_request_allowed('external.test:8788','','application/json')
