from rapidfuzz.fuzz import ratio, token_set_ratio
from .normalize import normalize, normalize_address, normalize_zip, normalize_name

def _field(a, *names):
    for n in names:
        if n in a:
            return a.get(n)
    return ""

def score_match(community, account):
    c_name = normalize_name(community.name)
    a_name = normalize_name(_field(account, "name", "account_name"))
    c_addr = normalize_address(community.address)
    a_addr = normalize_address(_field(account, "address", "street", "street_address"))
    c_city = normalize(community.city)
    a_city = normalize(_field(account, "city"))
    c_state = normalize(community.state)
    a_state = normalize(_field(account, "state"))
    c_zip = normalize_zip(community.zip)
    a_zip = normalize_zip(_field(account, "zip", "postal_code"))

    name_score = ratio(c_name, a_name) / 100 if c_name and a_name else 0
    addr_score = ratio(c_addr, a_addr) / 100 if c_addr and a_addr else 0
    token_score = token_set_ratio(c_name, a_name) / 100 if c_name and a_name else 0

    location = 0
    if c_zip and a_zip and c_zip == a_zip:
        location += 0.35
    if c_city and a_city and c_city == a_city:
        location += 0.15
    if c_state and a_state and c_state == a_state:
        location += 0.10

    score = min(1.0, 0.40 * addr_score + 0.20 * name_score + 0.10 * token_score + location)

    reasons = []
    if c_zip and c_zip == a_zip: reasons.append("ZIP matches")
    if c_city and c_city == a_city: reasons.append("city matches")
    if c_state and c_state == a_state: reasons.append("state matches")
    if addr_score >= .85: reasons.append("street address strongly matches")
    if name_score >= .85: reasons.append("name strongly matches")
    if name_score < .70 and addr_score >= .85: reasons.append("address supports match despite name difference")

    return score, reasons

def find_best_match(community, accounts):
    scored = [(score_match(community, a), a) for a in accounts]
    scored.sort(key=lambda x: x[0][0], reverse=True)
    if not scored:
        return None, 0, []
    (score, reasons), account = scored[0]
    return account, score, reasons
