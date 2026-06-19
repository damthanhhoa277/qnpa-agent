"""
Tracking & báo cáo hiệu quả quảng cáo Meta Ads
"""
from meta_api import get, AD_ACCOUNT_ID
from datetime import datetime, timedelta


FIELDS = ",".join([
    "campaign_name", "adset_name", "ad_name",
    "impressions", "reach", "clicks", "ctr",
    "spend", "cpm", "cpc",
    "actions", "cost_per_action_type",
    "date_start", "date_stop"
])


def get_account_insights(days=7, level="campaign"):
    """
    Lấy báo cáo toàn tài khoản.
    level: campaign | adset | ad
    """
    today = datetime.now().strftime("%Y-%m-%d")
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    data = get(f"{AD_ACCOUNT_ID}/insights", {
        "fields": FIELDS,
        "level": level,
        "time_range": f'{{"since":"{since}","until":"{today}"}}',
        "limit": 100
    })
    return data.get("data", [])


def get_campaign_insights(campaign_id, days=7):
    """Insights chi tiết cho 1 campaign"""
    today = datetime.now().strftime("%Y-%m-%d")
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    data = get(f"{campaign_id}/insights", {
        "fields": FIELDS,
        "time_range": f'{{"since":"{since}","until":"{today}"}}',
        "time_increment": 1  # Tách theo ngày
    })
    return data.get("data", [])


def get_leads_count_by_campaign(days=30):
    """Số leads theo từng campaign trong N ngày"""
    rows = get_account_insights(days=days, level="campaign")
    result = []
    for row in rows:
        leads = 0
        for action in row.get("actions", []):
            if action["action_type"] == "lead":
                leads = int(action["value"])
        cpl = row.get("cost_per_lead", "N/A")
        result.append({
            "campaign": row.get("campaign_name"),
            "spend": row.get("spend"),
            "leads": leads,
            "cpl": cpl,
            "ctr": row.get("ctr"),
            "reach": row.get("reach"),
            "period": f"{row.get('date_start')} → {row.get('date_stop')}"
        })
    return result


def print_bao_cao(days=7):
    """In báo cáo tổng hợp ra terminal"""
    print(f"\n{'='*60}")
    print(f"BÁO CÁO META ADS — {days} NGÀY QUA")
    print(f"{'='*60}")

    rows = get_leads_count_by_campaign(days=days)
    if not rows:
        print("Chưa có dữ liệu hoặc chưa chạy ads.")
        return

    total_spend = 0
    total_leads = 0
    for row in rows:
        spend = float(row["spend"] or 0)
        total_spend += spend
        total_leads += row["leads"]
        print(f"\n📢 {row['campaign']}")
        print(f"   Chi tiêu: {spend:,.0f} VND | Leads: {row['leads']} | CPL: {row['cpl']}")
        print(f"   CTR: {row['ctr']}% | Reach: {row['reach']}")

    print(f"\n{'─'*60}")
    print(f"TỔNG: Chi {total_spend:,.0f} VND | {total_leads} leads")
    if total_leads > 0:
        print(f"CPL trung bình: {total_spend/total_leads:,.0f} VND/lead")


if __name__ == "__main__":
    print_bao_cao(days=30)
