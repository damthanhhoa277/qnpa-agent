"""
Lấy leads từ Facebook/Instagram Lead Ads Forms
"""
import os
from meta_api import get, AD_ACCOUNT_ID, ACCESS_TOKEN
from datetime import datetime

PAGE_ID = os.environ.get("META_PAGE_ID", "917102468148914")


def _get_page_token():
    """Lấy Page Access Token từ User Token"""
    data = get("me/accounts", {"fields": "id,name,access_token"})
    for page in data.get("data", []):
        if page["id"] == PAGE_ID:
            return page["access_token"]
    return ACCESS_TOKEN


def get_all_leadgen_forms():
    """Lấy danh sách tất cả Lead Forms của Page"""
    try:
        page_token = _get_page_token()
        data = get(f"{PAGE_ID}/leadgen_forms", {
            "fields": "id,name,status,leads_count,created_time",
            "limit": 100,
            "access_token": page_token
        })
        return data.get("data", [])
    except Exception as e:
        print(f"[WARN] leadgen_forms error: {e}")
        return []


def get_leads_from_form(form_id, since_timestamp=None):
    """Lấy leads từ một form cụ thể"""
    params = {
        "fields": "id,created_time,field_data",
        "limit": 100
    }
    if since_timestamp:
        params["filtering"] = f'[{{"field":"time_created","operator":"GREATER_THAN","value":{since_timestamp}}}]'

    leads = []
    data = get(f"{form_id}/leads", params)
    leads.extend(data.get("data", []))

    # Phân trang nếu có nhiều leads
    while "paging" in data and "next" in data["paging"]:
        cursor = data["paging"]["cursors"]["after"]
        params["after"] = cursor
        data = get(f"{form_id}/leads", params)
        leads.extend(data.get("data", []))

    return leads


def parse_lead(lead_raw):
    """Chuyển lead thô thành dict dễ đọc"""
    result = {
        "id": lead_raw["id"],
        "created_time": lead_raw["created_time"]
    }
    for field in lead_raw.get("field_data", []):
        key = field["name"].lower().replace(" ", "_")
        result[key] = field["values"][0] if field["values"] else ""
    return result


def get_all_new_leads(since_timestamp=None):
    """Lấy tất cả leads mới từ tất cả forms"""
    forms = get_all_leadgen_forms()
    all_leads = []
    for form in forms:
        raw_leads = get_leads_from_form(form["id"], since_timestamp)
        for lead in raw_leads:
            parsed = parse_lead(lead)
            parsed["form_name"] = form["name"]
            parsed["form_id"] = form["id"]
            all_leads.append(parsed)
    return all_leads


if __name__ == "__main__":
    print("=== LEADS MỚI NHẤT ===")
    forms = get_all_leadgen_forms()
    if not forms:
        print("Chưa có Lead Form nào. Tạo Lead Ads trước nhé!")
    else:
        for form in forms:
            print(f"\nForm: {form['name']} | Tổng leads: {form.get('leads_count', 0)}")
            leads = get_leads_from_form(form["id"])
            for lead in leads[:5]:
                print(f"  - {parse_lead(lead)}")
