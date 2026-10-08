from app.reconciliation import billing_requires_chow

def test_chow_when_revenue_and_ar_exist():
    assert billing_requires_chow({"lifetime_revenue": 1000, "outstanding_ar": 50})

def test_no_chow_without_ar():
    assert not billing_requires_chow({"lifetime_revenue": 1000, "outstanding_ar": 0})

def test_no_chow_without_revenue():
    assert not billing_requires_chow({"lifetime_revenue": 0, "outstanding_ar": 50})
