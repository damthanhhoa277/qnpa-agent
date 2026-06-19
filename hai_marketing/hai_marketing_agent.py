"""
Agent Hải Marketing — QNPA
Tự động: lấy leads mới, báo cáo hàng ngày, cảnh báo ads kém hiệu quả
"""
import os
import json
import time
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

import meta_leads as leads_mod
import meta_campaigns as camp_mod
import meta_insights as insight_mod

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [HAI] %(message)s",
    handlers=[
        logging.FileHandler("hai_marketing.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

LEADS_SEEN_FILE = "hai_leads_seen.json"


def load_seen_leads():
    if os.path.exists(LEADS_SEEN_FILE):
        with open(LEADS_SEEN_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_seen_leads(seen):
    with open(LEADS_SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(list(seen), f)


def send_telegram(msg):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    import requests
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}
    )


def check_new_leads():
    """Kiểm tra và thông báo leads mới"""
    seen = load_seen_leads()
    since = int((datetime.now() - timedelta(hours=1)).timestamp())
    new_leads = leads_mod.get_all_new_leads(since_timestamp=since)

    fresh = [l for l in new_leads if l["id"] not in seen]
    if not fresh:
        log.info("Không có lead mới.")
        return

    for lead in fresh:
        seen.add(lead["id"])
        name = lead.get("full_name", lead.get("ten", "Không rõ"))
        phone = lead.get("phone_number", lead.get("so_dien_thoai", ""))
        form = lead.get("form_name", "")
        msg = (
            f"🎯 <b>LEAD MỚI — QNPA</b>\n"
            f"Họ tên: {name}\n"
            f"SĐT: {phone}\n"
            f"Form: {form}\n"
            f"Thời gian: {lead.get('created_time', '')}"
        )
        log.info(f"Lead mới: {name} | {phone}")
        send_telegram(msg)

    save_seen_leads(seen)
    log.info(f"Đã xử lý {len(fresh)} lead mới.")


def daily_report():
    """Gửi báo cáo tổng hợp hàng ngày"""
    rows = insight_mod.get_leads_count_by_campaign(days=1)
    if not rows:
        send_telegram("📊 Báo cáo hôm nay: Chưa có dữ liệu ads.")
        return

    total_spend = sum(float(r["spend"] or 0) for r in rows)
    total_leads = sum(r["leads"] for r in rows)

    lines = [f"📊 <b>BÁO CÁO META ADS — {datetime.now().strftime('%d/%m/%Y')}</b>\n"]
    for r in rows:
        lines.append(f"▸ {r['campaign']}: {r['leads']} leads | Chi {float(r['spend'] or 0):,.0f}đ")

    lines.append(f"\n<b>Tổng: {total_leads} leads | {total_spend:,.0f}đ</b>")
    if total_leads > 0:
        lines.append(f"CPL trung bình: {total_spend/total_leads:,.0f}đ/lead")

    send_telegram("\n".join(lines))
    log.info(f"Đã gửi báo cáo ngày: {total_leads} leads, {total_spend:,.0f}đ")


def check_underperforming_ads():
    """Cảnh báo ads có CPL cao bất thường (> 500k/lead)"""
    CPL_THRESHOLD = 500000
    rows = insight_mod.get_leads_count_by_campaign(days=3)
    alerts = []
    for r in rows:
        spend = float(r["spend"] or 0)
        if r["leads"] > 0:
            cpl = spend / r["leads"]
            if cpl > CPL_THRESHOLD:
                alerts.append(f"⚠️ {r['campaign']}: CPL {cpl:,.0f}đ (vượt ngưỡng {CPL_THRESHOLD:,}đ)")
        elif spend > 200000:
            alerts.append(f"⚠️ {r['campaign']}: Chi {spend:,.0f}đ nhưng 0 lead")

    if alerts:
        msg = "🚨 <b>CẢNH BÁO ADS KÉM HIỆU QUẢ</b>\n" + "\n".join(alerts)
        send_telegram(msg)
        log.warning(f"Cảnh báo: {len(alerts)} ads cần xem lại")


def run():
    log.info("Agent Hải Marketing khởi động...")
    send_telegram("🚀 Agent Hải Marketing đã online — đang theo dõi Meta Ads QNPA")

    last_daily = None

    while True:
        now = datetime.now()

        # Kiểm tra leads mới mỗi 15 phút
        check_new_leads()

        # Báo cáo ngày lúc 8h sáng
        if now.hour == 8 and (last_daily is None or last_daily.date() < now.date()):
            daily_report()
            check_underperforming_ads()
            last_daily = now

        time.sleep(900)  # 15 phút


if __name__ == "__main__":
    run()
