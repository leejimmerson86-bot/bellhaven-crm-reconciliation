from dataclasses import dataclass, field
from typing import Any, Optional

@dataclass
class Community:
    name: str
    address: str
    city: str
    state: str
    zip: str
    care_offerings: list[str] = field(default_factory=list)
    source_url: str = ""

@dataclass
class Proposal:
    fingerprint: str
    category: str
    website: dict[str, Any]
    crm: Optional[dict[str, Any]]
    action: str
    proposed_changes: dict[str, Any]
    evidence: list[str]
    confidence: float
    sop: dict[str, Any]
    status: str = "pending"
    decision_note: str = ""
