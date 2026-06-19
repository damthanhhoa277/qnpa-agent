"""
Quản lý Campaigns, Ad Sets, Ads trên Meta Ads
"""
from meta_api import get, post, AD_ACCOUNT_ID


# ─── ĐỌC ───────────────────────────────────────────────────────────────────

def list_campaigns(status_filter="ACTIVE"):
    """Lấy danh sách campaigns"""
    params = {
        "fields": "id,name,status,objective,daily_budget,lifetime_budget,start_time,stop_time",
        "limit": 50
    }
    if status_filter != "ALL":
        params["effective_status"] = f'["{status_filter}"]'
    data = get(f"{AD_ACCOUNT_ID}/campaigns", params)
    return data.get("data", [])


def list_adsets(campaign_id=None):
    """Lấy Ad Sets (theo campaign hoặc tất cả)"""
    endpoint = f"{campaign_id}/adsets" if campaign_id else f"{AD_ACCOUNT_ID}/adsets"
    data = get(endpoint, {
        "fields": "id,name,status,daily_budget,targeting,start_time,end_time",
        "limit": 50
    })
    return data.get("data", [])


def list_ads(adset_id=None):
    """Lấy Ads"""
    endpoint = f"{adset_id}/ads" if adset_id else f"{AD_ACCOUNT_ID}/ads"
    data = get(endpoint, {
        "fields": "id,name,status,creative,effective_status",
        "limit": 50
    })
    return data.get("data", [])


# ─── TẠO MỚI ────────────────────────────────────────────────────────────────

def create_campaign(name, objective="LEAD_GENERATION", daily_budget_vnd=500000, status="PAUSED"):
    """
    Tạo campaign mới.
    objective: LEAD_GENERATION | BRAND_AWARENESS | REACH | TRAFFIC | CONVERSIONS
    daily_budget_vnd: ngân sách ngày tính bằng VND (500.000 = 500k)
    """
    daily_budget_cents = int(daily_budget_vnd * 100)
    data = post(f"{AD_ACCOUNT_ID}/campaigns", {
        "name": name,
        "objective": objective,
        "status": status,
        "daily_budget": daily_budget_cents,
        "special_ad_categories": "[]"
    })
    return data


def pause_campaign(campaign_id):
    """Tạm dừng campaign"""
    return post(f"{campaign_id}", {"status": "PAUSED"})


def activate_campaign(campaign_id):
    """Bật lại campaign"""
    return post(f"{campaign_id}", {"status": "ACTIVE"})


def clone_campaign(campaign_id):
    """Nhân bản campaign"""
    return post(f"{AD_ACCOUNT_ID}/campaigns", {
        "source_campaign_id": campaign_id,
        "name": f"[CLONE] Campaign {campaign_id}"
    })


# ─── CẬP NHẬT NGÂN SÁCH ─────────────────────────────────────────────────────

def update_budget(campaign_id, daily_budget_vnd):
    """Cập nhật ngân sách ngày"""
    return post(f"{campaign_id}", {
        "daily_budget": int(daily_budget_vnd * 100)
    })


if __name__ == "__main__":
    print("=== CAMPAIGNS ĐANG CHẠY ===")
    campaigns = list_campaigns("ALL")
    if not campaigns:
        print("Chưa có campaign nào.")
    else:
        for c in campaigns:
            budget = c.get("daily_budget", c.get("lifetime_budget", "N/A"))
            print(f"  [{c['status']}] {c['name']} | Budget: {budget} | ID: {c['id']}")
