# Bellhaven CRM Ownership Reconciliation

A small, review-first data-quality pipeline for reconciling Bellhaven Senior Living communities from the public website against the CRM sandbox.

## What it does

1. Scrapes Bellhaven communities and care offerings.
2. Pulls CRM accounts.
3. Normalizes names and addresses.
4. Scores website ↔ CRM matches.
5. Classifies records as:
   - confident match
   - needs fix
   - new account
   - CRM-only / no longer listed
   - needs review
6. Applies the billing/CHOW SOP before proposing parent changes.
7. Stores proposals and decisions locally in SQLite.
8. Provides a Streamlit review UI.
9. Writes to the CRM only after an explicit approval.
10. Is safe to re-run: previously decided proposals are not recreated unless their fingerprint changes.

## Important security note

Do NOT put the assessment API token in this repository.

Create a local `.env` file from `.env.example`:

```text
CRM_API_TOKEN=your_personal_token
CRM_BASE_URL=https://analyst-assessment-production.up.railway.app/api/v1
BELLHAVEN_WEBSITE=https://analyst-assessment-production.up.railway.app
```

`.env` is ignored by Git.

## Run locally

Python 3.11+ recommended.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` and add your personal token.

### Generate proposals

```bash
python -m app.reconciliation
```

This does NOT write CRM changes. It creates/updates the local review queue in `review_queue.db`.

### Launch review app

```bash
streamlit run app/review_app.py
```

Review every proposed change. Only clicking Approve causes a CRM mutation.

### Run tests

```bash
pytest -q
```

## API assumptions

The assessment exposes accounts under `/api/v1/accounts`. The client uses:

- `GET /accounts`
- `GET /accounts/{id}`
- `POST /accounts`
- `PATCH /accounts/{id}`

If the sandbox's Swagger schema uses a slightly different mutation verb/path, update the three methods in `app/crm_client.py`; all business logic remains unchanged.

## Matching approach

Address is the strongest signal because facility names can change after acquisition/rebranding. The scorer uses:

- exact normalized ZIP
- exact normalized city/state
- normalized street/address similarity
- facility-name similarity
- token overlap

A strong address match can overcome a changed facility name. A name-only match is never enough for an automatic high-confidence decision.

## Billing / CHOW SOP

Before proposing a parent change, the pipeline checks `lifetime_revenue` and `outstanding_ar`.

If BOTH are true:

- lifetime revenue > 0
- outstanding AR > 0

then the old account is preserved. The proposal creates a new account under the correct parent and sets `chow_current_account` on the old account to the new account ID.

Otherwise, the existing account can be re-parented directly.

Duplicate handling sets `duplicate_of_account` on the losing account and marks it `Inactive`. Nothing is deleted because the API has no delete/merge operation.

## Idempotency

Every proposal gets a SHA-256 fingerprint from the source record, CRM account, proposed action, and target values. The SQLite queue keeps the decision.

Running the pipeline again therefore:

- refreshes source/CRM data
- creates only new or materially changed proposals
- does not re-propose already decided work
- does not write CRM changes during reconciliation

## Daily schedule

A GitHub Actions example is included at:

`.github/workflows/daily-reconciliation.yml`

The scheduled job generates the queue. Production deployment would additionally connect the reviewer UI to the same persistent review store.

## Submission checklist

- [ ] Run `python -m app.reconciliation`
- [ ] Review all proposals in Streamlit
- [ ] Approve/reject every proposal
- [ ] Confirm the final CRM state
- [ ] Run `pytest -q`
- [ ] Do not commit `.env`
- [ ] Zip this project or publish it to GitHub
