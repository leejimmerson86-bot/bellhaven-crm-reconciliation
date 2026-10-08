import json
import streamlit as st
from .config import settings
from .crm_client import CRMClient
from .repository import list_proposals, set_status

st.set_page_config(page_title="Bellhaven CRM Review", layout="wide")
st.title("Bellhaven CRM Ownership Review")
st.caption("No CRM mutation occurs until a reviewer explicitly approves a proposal.")

rows = list_proposals()
pending = [r for r in rows if r["status"] == "pending"]
st.metric("Pending proposals", len(pending))

if not pending:
    st.success("No pending proposals.")
    st.stop()

for i, row in enumerate(pending):
    website = json.loads(row["website_json"])
    crm = json.loads(row["crm_json"]) if row["crm_json"] else None
    changes = json.loads(row["changes_json"])
    evidence = json.loads(row["evidence_json"])
    sop = json.loads(row["sop_json"])

    with st.expander(f"{i+1}. {row['category']} — {row['action']} — confidence {row['confidence']:.0%}", expanded=i == 0):
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Website evidence")
            st.json(website)
        with c2:
            st.subheader("Current CRM")
            st.json(crm or {})

        st.subheader("Proposed change")
        st.json(changes)
        st.write("**Evidence:**", "; ".join(evidence))
        st.write("**Billing / CHOW check:**")
        st.json(sop)

        note = st.text_input("Reviewer note", key=f"note_{row['fingerprint']}")

        a, b = st.columns(2)
        with a:
            if st.button("Approve", key=f"approve_{row['fingerprint']}", type="primary"):
                try:
                    crm_client = CRMClient()
                    if row["action"] == "update_account":
                        crm_client.update_account(crm["id"], changes)
                    elif row["action"] == "create_account":
                        crm_client.create_account(changes)
                    elif row["action"] == "chow_new_account":
                        new_id = crm_client.create_account(changes["new_account"]).get("id")
                        crm_client.update_account(crm["id"], {"chow_current_account": new_id})
                    elif row["action"] == "review_crm_only":
                        crm_client.update_account(crm["id"], {"status": "Needs Review"})
                    elif row["action"] == "none":
                        pass
                    else:
                        raise ValueError(f"Unsupported action: {row['action']}")
                    set_status(row["fingerprint"], "approved", note)
                    st.rerun()
                except Exception as exc:
                    st.error(f"CRM write failed: {exc}")
        with b:
            if st.button("Reject", key=f"reject_{row['fingerprint']}"):
                set_status(row["fingerprint"], "rejected", note)
                st.rerun()
