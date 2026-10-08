import json
from .config import settings
from .crm_client import CRMClient
from .matching import find_best_match
from .models import Proposal
from .repository import fingerprint, upsert_proposal
from .scraper import scrape_communities

def account_parent_id(a):
    return a.get("parent_id")

def is_bellhaven_parent(a):
    n = str(a.get("name", "")).lower()
    return "bellhaven" in n and not a.get("parent_id")

def billing_requires_chow(a):
    revenue = float(a.get("lifetime_revenue") or 0)
    ar = float(a.get("outstanding_ar") or 0)
    return revenue > 0 and ar > 0

def main():
    crm = CRMClient()
    communities = scrape_communities()
    accounts = crm.list_accounts()

    # Try to identify the Bellhaven parent from CRM.
    parents = [a for a in accounts if is_bellhaven_parent(a)]
    parent = parents[0] if parents else None
    parent_id = parent.get("id") if parent else None

    bellhaven_children = [
        a for a in accounts if parent_id and a.get("parent_id") == parent_id
    ]

    matched_ids = set()

    for community in communities:
        account, score, reasons = find_best_match(community, accounts)

        website = {
            "name": community.name,
            "address": community.address,
            "city": community.city,
            "state": community.state,
            "zip": community.zip,
            "care_offerings": community.care_offerings,
            "source_url": community.source_url,
        }

        if account is None or score < 0.62:
            action = "create_account"
            category = "new_account"
            changes = {
                "name": community.name,
                "address": community.address,
                "city": community.city,
                "state": community.state,
                "zip": community.zip,
                "care_offerings": community.care_offerings,
                "parent_id": parent_id,
            }
            crm_data = account if account and score >= .45 else None
            confidence = score
            evidence = reasons + ["No sufficiently reliable CRM match."]
            sop = {"requires_chow": False}
        else:
            matched_ids.add(account.get("id"))
            current_parent = account.get("parent_id")
            changes = {}
            category = "confident_match" if score >= .85 else "needs_fix"
            action = "none"

            if account.get("name") != community.name:
                changes["name"] = community.name

            if parent_id and current_parent != parent_id:
                if billing_requires_chow(account):
                    category = "needs_fix"
                    action = "chow_new_account"
                    changes = {
                        "new_account": {
                            "name": community.name,
                            "address": community.address,
                            "city": community.city,
                            "state": community.state,
                            "zip": community.zip,
                            "care_offerings": community.care_offerings,
                            "parent_id": parent_id,
                        },
                        "old_account": {
                            "chow_current_account": "<new-account-id>"
                        }
                    }
                    sop = {
                        "requires_chow": True,
                        "lifetime_revenue": account.get("lifetime_revenue"),
                        "outstanding_ar": account.get("outstanding_ar"),
                        "reason": "Revenue history and outstanding AR require preserving the old account."
                    }
                else:
                    category = "needs_fix"
                    action = "update_account"
                    changes["parent_id"] = parent_id
                    sop = {
                        "requires_chow": False,
                        "lifetime_revenue": account.get("lifetime_revenue"),
                        "outstanding_ar": account.get("outstanding_ar"),
                    }
            else:
                sop = {
                    "requires_chow": False,
                    "lifetime_revenue": account.get("lifetime_revenue"),
                    "outstanding_ar": account.get("outstanding_ar"),
                }

            if action == "none" and changes:
                action = "update_account"
            evidence = reasons

        fp = fingerprint(
            community.name, community.address, community.city, community.state,
            community.zip, account.get("id") if account else None, action, changes
        )

        upsert_proposal(Proposal(
            fingerprint=fp,
            category=category,
            website=website,
            crm=account,
            action=action,
            proposed_changes=changes,
            evidence=evidence,
            confidence=confidence,
            sop=sop,
        ))

    # Bellhaven CRM children not represented by the website.
    for account in bellhaven_children:
        if account.get("id") not in matched_ids:
            changes = {"status": "Needs Review"}
            fp = fingerprint("crm_only", account.get("id"), changes)
            upsert_proposal(Proposal(
                fingerprint=fp,
                category="crm_only",
                website={},
                crm=account,
                action="review_crm_only",
                proposed_changes=changes,
                evidence=["Account is currently under Bellhaven but was not found in the website community scrape."],
                confidence=1.0,
                sop={
                    "requires_chow": billing_requires_chow(account),
                    "lifetime_revenue": account.get("lifetime_revenue"),
                    "outstanding_ar": account.get("outstanding_ar"),
                },
            ))

    print(f"Scraped {len(communities)} communities and evaluated {len(accounts)} CRM accounts.")
    print("Review queue updated. No CRM writes were performed.")

if __name__ == "__main__":
    main()
