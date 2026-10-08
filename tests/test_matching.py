from types import SimpleNamespace
from app.matching import score_match, find_best_match

def test_address_drives_match_when_name_changes():
    c = SimpleNamespace(
        name="Amberly Manor",
        address="123 Main Street",
        city="Hudson",
        state="OH",
        zip="44236",
    )
    a = {
        "id": "1",
        "name": "Bellhaven Amberly",
        "address": "123 Main St",
        "city": "Hudson",
        "state": "OH",
        "zip": "44236",
    }
    score, reasons = score_match(c, a)
    assert score > .65
    assert any("address" in x for x in reasons)

def test_best_match():
    c = SimpleNamespace(name="Bellhaven Example", address="10 Oak Rd",
                        city="Macon", state="GA", zip="31201")
    accounts = [
        {"id":"wrong","name":"Bellhaven Other","address":"90 Pine St","city":"Macon","state":"GA","zip":"31201"},
        {"id":"right","name":"Example Senior Living","address":"10 Oak Road","city":"Macon","state":"GA","zip":"31201"},
    ]
    a, score, _ = find_best_match(c, accounts)
    assert a["id"] == "right"
