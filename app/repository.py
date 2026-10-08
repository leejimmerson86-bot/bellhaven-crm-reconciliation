import hashlib, json, sqlite3
from pathlib import Path
from .config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS proposals (
    fingerprint TEXT PRIMARY KEY,
    category TEXT NOT NULL,
    website_json TEXT NOT NULL,
    crm_json TEXT,
    action TEXT NOT NULL,
    changes_json TEXT NOT NULL,
    evidence_json TEXT NOT NULL,
    confidence REAL NOT NULL,
    sop_json TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    decision_note TEXT DEFAULT '',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

def connect():
    conn = sqlite3.connect(settings.review_db)
    conn.execute(SCHEMA)
    return conn

def fingerprint(*parts):
    raw = json.dumps(parts, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()

def upsert_proposal(p):
    conn = connect()
    conn.execute("""
    INSERT INTO proposals
    (fingerprint, category, website_json, crm_json, action, changes_json,
     evidence_json, confidence, sop_json, status, decision_note)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', '')
    ON CONFLICT(fingerprint) DO UPDATE SET
      website_json=excluded.website_json,
      crm_json=excluded.crm_json,
      action=excluded.action,
      changes_json=excluded.changes_json,
      evidence_json=excluded.evidence_json,
      confidence=excluded.confidence,
      sop_json=excluded.sop_json,
      updated_at=CURRENT_TIMESTAMP
    WHERE proposals.status='pending'
    """, (
        p.fingerprint, p.category, json.dumps(p.website), json.dumps(p.crm),
        p.action, json.dumps(p.proposed_changes), json.dumps(p.evidence),
        p.confidence, json.dumps(p.sop)
    ))
    conn.commit()
    conn.close()

def list_proposals(status=None):
    conn = connect()
    if status:
        rows = conn.execute("SELECT * FROM proposals WHERE status=? ORDER BY created_at", (status,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM proposals ORDER BY created_at").fetchall()
    cols = [d[0] for d in conn.execute("SELECT * FROM proposals LIMIT 0").description]
    conn.close()
    return [dict(zip(cols, r)) for r in rows]

def set_status(fp, status, note=""):
    conn = connect()
    conn.execute(
        "UPDATE proposals SET status=?, decision_note=?, updated_at=CURRENT_TIMESTAMP WHERE fingerprint=?",
        (status, note, fp),
    )
    conn.commit()
    conn.close()
