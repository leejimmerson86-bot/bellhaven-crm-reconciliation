import tempfile
from app import repository

def test_fingerprint_is_deterministic():
    a = repository.fingerprint("acct1", "update_account", {"parent_id":"p1"})
    b = repository.fingerprint("acct1", "update_account", {"parent_id":"p1"})
    assert a == b

def test_fingerprint_changes_when_target_changes():
    a = repository.fingerprint("acct1", {"parent_id":"p1"})
    b = repository.fingerprint("acct1", {"parent_id":"p2"})
    assert a != b
