import sys, os
sys.path.insert(0, 'hai_marketing')
from dotenv import load_dotenv
load_dotenv('.env')

import meta_api as api
import meta_campaigns as c
import meta_leads as l
import meta_insights as ins

print("=== 1. TOKEN ===")
me = api.get("me")
print(f"  User: {me.get('name')} | ID: {me.get('id')}")

print("\n=== 2. CAMPAIGNS ===")
campaigns = c.list_campaigns('ALL')
print(f"  Tim thay {len(campaigns)} campaigns")
for camp in campaigns:
    print(f"  [{camp['status']}] {camp['name']} | ID: {camp['id']}")

print("\n=== 3. LEAD FORMS ===")
forms = l.get_all_leadgen_forms()
print(f"  Tim thay {len(forms)} lead forms")
for f in forms:
    print(f"  {f['name']} | Leads: {f.get('leads_count', 0)}")

print("\n=== 4. INSIGHTS ===")
try:
    ins.print_bao_cao(days=7)
except Exception as e:
    print(f"  Insights error: {e}")

print("\nHOAN THANH.")
