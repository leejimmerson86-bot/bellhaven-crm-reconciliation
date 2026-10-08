import requests
from .config import settings

class CRMClient:
    def __init__(self):
        if not settings.crm_api_token:
            raise RuntimeError("CRM_API_TOKEN is missing. Put it in .env.")
        self.base = settings.crm_base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {settings.crm_api_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        })

    def _request(self, method, path, **kwargs):
        r = self.session.request(method, self.base + path, timeout=30, **kwargs)
        r.raise_for_status()
        if not r.content:
            return {}
        return r.json()

    def list_accounts(self, q=None):
        params = {"q": q} if q else {}
        data = self._request("GET", "/accounts", params=params)
        if isinstance(data, list):
            return data
        for key in ("accounts", "items", "data", "results"):
            if isinstance(data.get(key), list):
                return data[key]
        return []

    def get_account(self, account_id):
        return self._request("GET", f"/accounts/{account_id}")

    def create_account(self, payload):
        return self._request("POST", "/accounts", json=payload)

    def update_account(self, account_id, payload):
        return self._request("PATCH", f"/accounts/{account_id}", json=payload)
