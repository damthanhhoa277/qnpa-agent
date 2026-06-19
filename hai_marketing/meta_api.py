import os
import requests

ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN", "")
AD_ACCOUNT_ID = os.environ.get("META_AD_ACCOUNT_ID", "act_138676007632717")
BUSINESS_ID = os.environ.get("META_BUSINESS_ID", "977802738178619")
BASE_URL = "https://graph.facebook.com/v20.0"


def get(endpoint, params=None):
    params = params or {}
    if "access_token" not in params:
        params["access_token"] = ACCESS_TOKEN
    r = requests.get(f"{BASE_URL}/{endpoint}", params=params)
    r.raise_for_status()
    return r.json()


def post(endpoint, data=None):
    data = data or {}
    data["access_token"] = ACCESS_TOKEN
    r = requests.post(f"{BASE_URL}/{endpoint}", data=data)
    r.raise_for_status()
    return r.json()
