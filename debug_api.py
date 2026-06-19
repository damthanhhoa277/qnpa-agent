import sys, os, requests
sys.path.insert(0, 'hai_marketing')
from dotenv import load_dotenv
load_dotenv('.env')

TOKEN = os.environ.get("META_ACCESS_TOKEN")
AD_ACCOUNT = "act_138676007632717"
PAGE_ID = "917102468148914"

def check(url, params={}):
    params["access_token"] = TOKEN
    r = requests.get(url, params=params)
    print(f"Status: {r.status_code}")
    print(r.json())
    print()

print("=== 1. Test token valid ===")
check("https://graph.facebook.com/v20.0/me")

print("=== 2. Insights error detail ===")
check(f"https://graph.facebook.com/v20.0/{AD_ACCOUNT}/insights", {
    "fields": "spend,impressions",
    "date_preset": "last_7d"
})

print("=== 3. Leadgen forms via Page ===")
check(f"https://graph.facebook.com/v20.0/{PAGE_ID}/leadgen_forms")
