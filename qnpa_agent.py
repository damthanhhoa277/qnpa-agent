# encoding: utf-8
"""
QNPA AI Agent — Nhân viên ảo tư vấn Quảng Ninh Pickleball Academy
Phiên bản: 2.0 — Refactor đầy đủ theo workflow mới
"""
import sys
import re
import time
import os
import requests
from datetime import datetime, timezone, timedelta

sys.stdout.reconfigure(encoding="utf-8")

# ── File lock: chỉ cho phép 1 instance chạy ──────────────────
_BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
_LOCK_FILE = os.path.join(_BASE_DIR, "qnpa_agent.lock")
def _acquire_lock():
    if os.path.exists(_LOCK_FILE):
        try:
            with open(_LOCK_FILE) as f:
                old_pid = int(f.read().strip())
            # Kiểm tra PID đó có còn sống không
            import psutil
            if psutil.pid_exists(old_pid):
                print(f"❌ QNPA Agent đã chạy rồi (PID {old_pid}). Thoát để tránh gửi 2 lần.")
                sys.exit(1)
        except Exception:
            pass  # file lỗi → ghi đè
    with open(_LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))

def _release_lock():
    try:
        if os.path.exists(_LOCK_FILE):
            with open(_LOCK_FILE) as f:
                pid = int(f.read().strip())
            if pid == os.getpid():
                os.remove(_LOCK_FILE)
    except Exception:
        pass

# Chỉ lock khi chạy local (Railway tự đảm bảo 1 instance)
if not os.environ.get("RAILWAY_ENVIRONMENT"):
    _acquire_lock()

# ============================================================
# CẤU HÌNH
# ============================================================
PANCAKE_TOKEN  = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpbmZvIjp7Im9zIjozLCJjbGllbnRfaXAiOiIxMTMuMjMuMTA1LjUiLCJicm93c2VyIjoxLCJkZXZpY2VfdHlwZSI6M30sIm5hbWUiOiJIb8OgbmcgSOG6o28iLCJleHAiOjE3ODg3NTAwNDUsImFwcGxpY2F0aW9uIjoxLCJ1aWQiOiIwODNkY2JkNi1mYzNmLTQzZmQtOGZlNC03NDU1YTNlYzQ5MjciLCJzZXNzaW9uX2lkIjoiMzcwZDNlYzktMWE5ZC00ODY5LWE0NDktNzZhNjE2MDFiNzg4IiwiaWF0IjoxNzgwOTc0MDQ1LCJwYW5jYWtlX2lkIjoiNjIxNzY4MWMtMmFjZC00ZTM5LWE3OGUtZjgzYjFjMDE5MTg0IiwiZmJfaWQiOiIxOTE2MzE5OTQ4Njk2MDkyIiwibG9naW5fc2Vzc2lvbiI6bnVsbCwiZmJfbmFtZSI6Ikhvw6BuZyBI4bqjbyJ9.z2ZnDX3G5vGzaUgG5khHnef4IpMLsmWw-E4zTSbE9y0"
PAGE_ID        = "917102468148914"
TELEGRAM_TOKEN = "8608503050:AAEax-HkoZWrWL2QVXP5DXJYhk1FShWd7Zw"
CHAT_SALE      = "-5204359056"    # Nhóm QNPA SALE — chỉ nhận HOT LEAD + cảnh báo
CHAT_COACHING  = "-5017089871"   # Nhóm Coaching CAS — báo cáo 12h và 22h
CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY", "")
BASE           = "https://pages.fm/api/v1"
CLAUDE_BASE    = "https://api.anthropic.com/v1/messages"
POLL_INTERVAL  = 5
DRY_RUN        = False

# Google Sheet webhook (Apps Script URL — xem HOTLEAD_AppScript.js)
GSHEET_WEBHOOK = "https://script.google.com/macros/s/AKfycbzugBUoJbbr-nr3VA4BGqJhMAaPnVzUj85xiihmfJYmQqq_JWkHRt5WZoz-Occ5y6w-Og/exec"

# ============================================================
# KNOWLEDGE BASE
# ============================================================
QNPA_KNOWLEDGE = """
Bạn là Linh — nhân viên tư vấn tuyển sinh của Quảng Ninh Pickleball Academy (QNPA).
Xưng "em", gọi khách là "anh/chị" hoặc tên riêng nếu biết.

=== QUY TẮC VIẾT TIN NHẮN — BẮT BUỘC ===
1. CHỈ dùng văn bản thuần túy — TUYỆT ĐỐI KHÔNG dùng markdown (*, **, _, #) hay HTML
2. Mỗi tin nhắn tối đa 150 chữ
3. Chỉ hỏi 1 câu hỏi duy nhất mỗi tin
4. Emoji: 1 cái/tin, đặt cuối câu
5. TUYỆT ĐỐI KHÔNG đề cập học phí hay giá tiền cụ thể — học phí thay đổi theo ưu đãi, chỉ telesale mới tư vấn được
6. Nếu khách đã trả lời câu hỏi trước (dù mơ hồ) — KHÔNG hỏi lại y chang, tiến bước tiếp
7. CHỈ trả lời đúng câu hỏi MỚI NHẤT, không mang context cũ vào
8. Nếu khách hỏi địa chỉ → chỉ trả lời về địa chỉ rồi xin SĐT
9. Nếu khách hỏi học phí → chỉ trả lời về học phí rồi xin SĐT

=== MỤC TIÊU KHAI THÁC THÔNG TIN (theo thứ tự ưu tiên) ===
Cố gắng tự nhiên khai thác các thông tin sau trong quá trình hội thoại:
1. Số điện thoại (QUAN TRỌNG NHẤT)
2. Bé học hay người lớn tự học
3. Tuổi của học viên (nếu là bé)
4. Khu vực sinh sống (Hòn Gai, Cẩm Phả, Hạ Long, v.v.)
5. Đã từng học/chơi Pickleball chưa

Khai thác tự nhiên, không tra tấn khách bằng hàng loạt câu hỏi liên tiếp.
Nếu khách không muốn cung cấp thì bỏ qua, tiếp tục hội thoại bình thường.

=== MỤC TIÊU DUY NHẤT ===
Thu số điện thoại. Mọi câu trả lời đều dẫn về mục tiêu này.
Khi khách để lại SĐT: "Dạ cảm ơn anh/chị đã để lại số điện thoại ạ! Chuyên viên bên em sẽ liên hệ lại với mình trong thời gian sớm nhất ạ 😊"

=== KỊCH BẢN THEO TỪNG TÌNH HUỐNG ===

TÌNH HUỐNG 1 — Khách hỏi học phí/giá:
  KHÔNG báo học phí cụ thể. Học phí thay đổi theo chương trình ưu đãi, chỉ telesale mới tư vấn được.
  → "Dạ học phí bên em có nhiều ưu đãi theo từng thời điểm, em không muốn báo sai cho anh/chị ạ. Anh/chị cho em SĐT để chuyên viên gọi báo học phí chính xác và ưu đãi mới nhất sớm nhất nhé 😊"

TÌNH HUỐNG 2 — Khách hỏi Trại hè/cho bé:
  Tin 1: "Dạ Trại hè Pickleball khai giảng hè này rồi ạ! Bé nhà mình bao nhiêu tuổi ạ? 😊"
  Tin 2: "Dạ bé [tuổi] tuổi học được rồi ạ! Lịch Thứ 2 đến Thứ 6, 2 tiếng/buổi, đăng ký từng tháng linh hoạt. Anh/chị cho em SĐT để em gửi lịch khai giảng gần nhất nhé!"

TÌNH HUỐNG 3 — Khách hỏi lớp Cơ bản/mới bắt đầu:
  "Dạ Lớp Cơ bản bên em 20 buổi, từ nền tảng đến thi đấu được ạ. Anh/chị học cho bé hay cho bản thân? Cho em SĐT để tư vấn học phí và lịch khai giảng 30 phút nhé 😊"

TÌNH HUỐNG 4 — Khách đã biết chơi/hỏi Nâng cao:
  "Dạ Lớp Nâng cao đúng rồi ạ! Tập trung Dink, Drop, chiến thuật và thi đấu thực chiến. Anh/chị đang ở khu vực nào? Cho em SĐT để HLV tư vấn lộ trình phù hợp nhé 🏓"

TÌNH HUỐNG 5 — Khách hỏi địa điểm/địa chỉ:
  "Dạ bên em ở Quảng Ninh ạ. Anh/chị đang ở khu vực nào, em chỉ sân gần nhất và gửi link Maps luôn nhé? Cho em xin SĐT ạ 😊"

TÌNH HUỐNG 6 — Khách hỏi lịch khai giảng:
  "Dạ bên em nhận đăng ký liên tục, lớp hay đủ chỗ nhanh ạ. Anh/chị cho em SĐT để giữ chỗ sớm nhé 😊"

TÌNH HUỐNG 7 — Khách hỏi CLB cuối tuần:
  "Dạ CLB cuối tuần 300.000đ/tháng, thi đấu giao lưu mỗi cuối tuần ạ. Anh/chị cho em SĐT để gửi lịch chi tiết nhé 🏓"

TÌNH HUỐNG 8 — Khách nhắn Inbox/Ib/Inboc:
  "Dạ chào anh/chị! Em là Linh từ QNPA ạ. Anh/chị đang quan tâm đến chương trình Pickleball nào của bên em ạ? 😊"

TÌNH HUỐNG 9 — Khách để lại SĐT:
  "Dạ cảm ơn anh/chị đã để lại số điện thoại ạ! Chuyên viên bên em sẽ liên hệ lại với mình trong thời gian sớm nhất ạ 😊"

TÌNH HUỐNG 10 — Câu hỏi ngoài phạm vi:
  "Dạ câu này em cần xác nhận lại với bộ phận chuyên môn ạ. Anh/chị cho em SĐT, em nhờ chuyên viên gọi lại trả lời đầy đủ sớm nhất nhé!"

=== XỬ LÝ NGOÀI KỊCH BẢN ===
Luôn 2 phần: (1) Phản hồi điều khách vừa nói, tối đa 2 câu. (2) Xin SĐT.

Chưa biết chọn: "Bên em có 2 nhóm: cho bé thì Trại hè và Cơ bản, người lớn thì Cơ bản và Nâng cao. Anh/chị cho em SĐT, em gọi tư vấn chọn đúng sớm nhất nhé!"
Khách bực: "Dạ em xin lỗi ạ! Học phí dao động vài triệu tùy chương trình. Anh/chị cho em SĐT, em gọi báo giá ngay nhé 😊"
Phân vân/hỏi gia đình: "Dạ anh/chị cứ hỏi thêm ạ! Cho em SĐT trước, em gửi tài liệu để cả nhà cùng xem, tiện hơn 😊"
Sticker/hình/không rõ: "Dạ em nhận được rồi ạ! Anh/chị đang quan tâm chương trình nào của QNPA ạ? 😊"
OK/ừ/được không rõ: "Dạ anh/chị cho em SĐT để tư vấn chi tiết hơn nhé! Em gọi sớm nhất ạ 😊"
Thanh toán: "Dạ bên em thanh toán linh hoạt, chuyển khoản hoặc tiền mặt. Anh/chị cho em SĐT xác nhận đăng ký nhé!"
So sánh nơi khác: "Dạ QNPA có 5 HLV chuyên nghiệp, dùng phần mềm CenterUp theo dõi tiến độ. Anh/chị cho em SĐT, em mời tham quan sân miễn phí nhé!"
Hỏi lịch học: "Dạ lịch chính quy Thứ 2 đến Thứ 6, 2 tiếng/buổi. CLB cuối tuần có cho học viên đã học Cơ bản. Anh/chị cho em SĐT gửi lịch chi tiết nhé 🏓"

=== THÔNG TIN HỌC VIỆN ===
Tên: Quảng Ninh Pickleball Academy (QNPA)
Đội ngũ: 5 HLV chuyên nghiệp
Lịch học: Thứ 2 đến Thứ 6, 2 tiếng/buổi
Chương trình: Trại hè (3 tháng, đăng ký từng tháng) | Cơ bản (20 buổi) | Nâng cao | Private | CLB cuối tuần (300k/tháng)
Lộ trình: Trại hè → Cơ bản → Nâng cao → Private/CLB

=== ĐỊA CHỈ SÂN (CHỈ DÙNG THÔNG TIN NÀY, KHÔNG ĐƯỢC BỊA) ===
Khu vực Hòn Gai: Sân Sun Galaxy, Cột 5
Khu vực Bãi Cháy: Sân Hạ Long Star, Cái Dăm, Bãi Cháy

Khi khách hỏi địa chỉ → chỉ nói đúng 2 địa chỉ trên theo khu vực của khách.
Nếu khách chưa nói khu vực → hỏi khu vực rồi mới chỉ đường.
TUYỆT ĐỐI KHÔNG bịa địa chỉ, tên sân, số đường nào khác ngoài 2 sân trên.
"""

# ============================================================
# PANCAKE API
# ============================================================
def get_conversations(limit=50, conv_type="inbox"):
    url = f"{BASE}/pages/{PAGE_ID}/conversations?access_token={PANCAKE_TOKEN}&type={conv_type}&limit={limit}"
    try:
        r = requests.get(url, timeout=15)
        data = r.json()
        return data.get("conversations", []) if isinstance(data, dict) else []
    except Exception as e:
        log(f"⚠️ get_conversations lỗi: {e}")
        return []


def get_messages(conv_id, customer_id=None, limit=15):
    url = f"{BASE}/pages/{PAGE_ID}/conversations/{conv_id}/messages?access_token={PANCAKE_TOKEN}&limit={limit}"
    if customer_id:
        url += f"&customer_id={customer_id}"
    try:
        r = requests.get(url, timeout=15)
        data = r.json()
        if not isinstance(data, dict):
            return []
        if data.get("success") is False:
            return []
        return data.get("messages", [])
    except Exception as e:
        log(f"⚠️ get_messages lỗi: {e}")
        return []


def send_message(conv_id, text, customer_id=None, source_type="inbox"):
    if DRY_RUN:
        log(f"  [DRY RUN] Sẽ gửi: {text[:80]}")
        return {"dry_run": True}
    url = f"{BASE}/pages/{PAGE_ID}/conversations/{conv_id}/messages?access_token={PANCAKE_TOKEN}"
    if customer_id:
        url += f"&customer_id={customer_id}"
    action = "reply_comment" if source_type == "comment" else "reply_inbox"
    try:
        r = requests.post(url, json={"message": text, "action": action}, timeout=15)
        return r.json()
    except Exception as e:
        log(f"⚠️ send_message lỗi: {e}")
        return {"error": str(e)}

# ============================================================
# TELEGRAM — CHỈ HOT LEAD + CẢNH BÁO + BÁO CÁO
# ============================================================
def tg_send(chat_id, text):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            timeout=10
        )
    except Exception:
        pass


def tg_alert(text):
    """Cảnh báo lỗi — dùng Google Sheets throttle, chống spam kể cả 2 Railway instance"""
    # Key có slot 4 tiếng: mỗi alert chỉ gửi 1 lần/4h xuyên tất cả instance
    slot = datetime.now(timezone(timedelta(hours=7))).strftime("%Y%m%d%H")[:-1]  # 4h slot
    alert_key = f"alert_{slot}_{text[:50]}"
    if GSHEET_WEBHOOK:
        try:
            rj = requests.post(GSHEET_WEBHOOK,
                               json={"action": "check_report", "report_key": alert_key},
                               timeout=5).json()
            if isinstance(rj, dict) and rj.get("sent"):
                log(f"  [alert throttled] {text[:60]}")
                return
            requests.post(GSHEET_WEBHOOK,
                          json={"action": "mark_report", "report_key": alert_key},
                          timeout=5)
        except Exception:
            pass
    tg_send(CHAT_SALE, f"⚠️ {text}")
    tg_send(CHAT_COACHING, f"⚠️ {text}")


def tg_hot_lead(lead: dict):
    """Gửi HOT LEAD về nhóm SALE khi có SĐT"""
    now_str = datetime.now(timezone(timedelta(hours=7))).strftime("%H:%M")
    age = lead.get("age", "Chưa rõ")
    be_str = f"{age} tuổi" if age and age != "Chưa rõ" else "Chưa rõ"
    pb = lead.get("pickleball", "Chưa rõ")
    trinh_do = pb if pb and pb != "Chưa rõ" else "Chưa từng chơi Pickleball"
    nguon = lead.get("source", "Facebook Fanpage")
    msg = (
        f"🔥 <b>HOT LEAD MỚI</b>\n"
        f"👤 Tên KH: <b>{lead.get('parent', 'Chưa rõ')}</b>\n"
        f"👶 Bé: {be_str}\n"
        f"📍 Khu vực: {lead.get('area', 'Chưa rõ')}\n"
        f"🏓 Trình độ: {trinh_do}\n"
        f"📞 SĐT: <b>{lead.get('phone', 'Chưa có')}</b>\n"
        f"💬 Nguồn: {nguon}\n"
        f"⏰ Thời gian: {now_str}\n"
        f"👉 Cần telesale gọi lại sớm nhất có thể."
    )
    tg_send(CHAT_SALE, msg)


def gsheet_check_report(key: str) -> bool:
    """Kiểm tra Google Sheet xem báo cáo đã gửi chưa — dùng làm lock chống gửi 2 lần"""
    if not GSHEET_WEBHOOK:
        return False
    try:
        r = requests.post(GSHEET_WEBHOOK, json={"action": "check_report", "report_key": key}, timeout=8)
        return r.json().get("sent", False)
    except:
        return False

def gsheet_mark_report(key: str):
    """Đánh dấu báo cáo đã gửi vào Google Sheet"""
    if not GSHEET_WEBHOOK:
        return
    try:
        requests.post(GSHEET_WEBHOOK, json={"action": "mark_report", "report_key": key}, timeout=8)
    except:
        pass

def tg_report_14h_live(live: dict):
    """Báo cáo giữa ngày từ dữ liệu Pancake thực tế"""
    leads = live.get("leads", {})
    inbox = live.get("inbox", 0)
    comments = live.get("comments", 0)
    total = inbox + comments
    rate = f"{len(leads)/total*100:.0f}%" if total > 0 else "0%"
    lead_list = "\n".join(f"  {i+1}. {v['name']} — {v['phone']}"
                          for i, v in enumerate(list(leads.values())[:10]))
    msg = (
        f"📊 <b>BÁO CÁO GIỮA NGÀY</b>\n"
        f"📥 Inbox mới: <b>{inbox}</b>\n"
        f"💬 Comment mới: <b>{comments}</b>\n"
        f"📞 SĐT thu được: <b>{len(leads)}</b>\n"
        f"📈 Tỷ lệ → SĐT: <b>{rate}</b>\n"
        f"🔥 Danh sách lead:\n{lead_list if lead_list else '  (chưa có)'}\n"
        f"👉 Telesale gọi ngay các số trên!"
    )
    tg_send(CHAT_SALE, msg)

def tg_report_24h_live(live: dict):
    """Tổng kết ngày từ dữ liệu Pancake thực tế"""
    leads = live.get("leads", {})
    inbox = live.get("inbox", 0)
    comments = live.get("comments", 0)
    total = inbox + comments
    rate = f"{len(leads)/total*100:.0f}%" if total > 0 else "0%"
    lead_list = "\n".join(f"  {i+1}. {v['name']} — {v['phone']}"
                          for i, v in enumerate(list(leads.values())[:15]))
    msg = (
        f"📊 <b>TỔNG KẾT NGÀY</b>\n"
        f"📥 Inbox: <b>{inbox}</b>\n"
        f"💬 Comment: <b>{comments}</b>\n"
        f"📞 SĐT thu được: <b>{len(leads)}</b>\n"
        f"📈 Tỷ lệ → SĐT: <b>{rate}</b>\n"
        f"🔥 Tất cả lead hôm nay:\n{lead_list if lead_list else '  (chưa có)'}"
    )
    tg_send(CHAT_SALE, msg)

def tg_report_14h(stats: dict):
    """Báo cáo giữa ngày — gửi lúc 14:00"""
    total = stats.get("processed", 0)
    leads = stats.get("leads", 0)
    no_reply = total - leads
    rate = f"{leads/total*100:.0f}%" if total > 0 else "0%"
    f2h  = stats.get("followup_2h", 0)
    f10h = stats.get("followup_10h", 0)
    f20h = stats.get("followup_20h", 0)
    fman = stats.get("followup_manual", 0)
    top_q = stats.get("top_questions", [])
    top_q_str = " ".join(f"{i+1}. {q}" for i, q in enumerate(top_q[:3])) if top_q else "Chưa có dữ liệu"
    errors = stats.get("errors", [])
    van_de = errors[-1] if errors else "Không có vấn đề phát sinh"
    msg = (
        f"📊 <b>BÁO CÁO GIỮA NGÀY</b>\n"
        f"• Inbox mới: <b>{stats.get('new_inbox', 0)}</b>\n"
        f"• Comment mới: <b>{stats.get('comments', 0)}</b>\n"
        f"• Tự chăm KH: <b>2h={f2h} | 10h={f10h} | 20h={f20h}</b>\n"
        f"• Chăm thủ công (>24h): <b>{fman}</b>\n"
        f"• SĐT thu được: <b>{leads}</b>\n"
        f"• Tỷ lệ Inbox → SĐT: <b>{rate}</b>\n"
        f"• Lead nóng đã gửi: <b>{stats.get('full_leads', 0)}</b>\n"
        f"• Khách không phản hồi: <b>{no_reply}</b>\n"
        f"Top câu hỏi: {top_q_str}\n"
        f"⚠️ Vấn đề phát sinh: {van_de}"
    )
    tg_send(CHAT_SALE, msg)


def tg_report_24h(stats: dict):
    """Tổng kết ngày — gửi lúc 24:00 (0h)"""
    total = stats.get("processed", 0)
    leads = stats.get("leads", 0)
    no_reply = total - leads
    rate = f"{leads/total*100:.0f}%" if total > 0 else "0%"
    f2h  = stats.get("followup_2h", 0)
    f10h = stats.get("followup_10h", 0)
    f20h = stats.get("followup_20h", 0)
    fman = stats.get("followup_manual", 0)
    top_q = stats.get("top_questions", [])
    top_q_str = " ".join(f"{i+1}. {q}" for i, q in enumerate(top_q[:5])) if top_q else "Chưa có dữ liệu"
    de_xuat = "Tiếp tục follow khách chưa phản hồi và tối ưu kịch bản hỏi SĐT."
    if no_reply > 5:
        de_xuat = "Cần review lại kịch bản — tỷ lệ không phản hồi cao. Thử A/B test câu hỏi SĐT khác."
    msg = (
        f"📊 <b>TỔNG KẾT NGÀY</b>\n"
        f"📥 Inbox mới: <b>{stats.get('new_inbox', 0)}</b>\n"
        f"💬 Comment mới: <b>{stats.get('comments', 0)}</b>\n"
        f"🔁 Tự chăm KH: <b>2h={f2h} | 10h={f10h} | 20h={f20h}</b>\n"
        f"📋 Chăm thủ công (>24h): <b>{fman}</b>\n"
        f"📞 SĐT thu được: <b>{leads}</b>\n"
        f"📈 Tỷ lệ chuyển đổi Inbox → SĐT: <b>{rate}</b>\n"
        f"🔥 Lead nóng: <b>{stats.get('full_leads', 0)}</b>\n"
        f"❌ Không phản hồi: <b>{no_reply}</b>\n"
        f"⚠️ Cần xử lý thủ công: <b>{stats.get('manual_needed', 0)}</b>\n"
        f"Top 5 câu hỏi: {top_q_str}\n"
        f"Đề xuất cải thiện ngày mai: {de_xuat}"
    )
    tg_send(CHAT_SALE, msg)

# ============================================================
# TRÍCH XUẤT THÔNG TIN LEAD TỪ HỘI THOẠI
# ============================================================
def extract_lead_info(messages, customer_name: str) -> dict:
    """
    Quét toàn bộ tin nhắn của khách, trích xuất:
    phone, age, area, pickleball_exp, student_name, parent_name
    """
    lead = {
        "parent"      : customer_name or "Chưa có",
        "student"     : "Chưa có",
        "age"         : "Chưa có",
        "area"        : "Chưa có",
        "pickleball"  : "Chưa rõ",
        "phone"       : "",
        "conv_key"    : "",
    }

    all_customer_text = " ".join(
        strip_html(str(m.get("original_message") or m.get("message", "")))
        for m in messages
        if str(m.get("from", {}).get("id", "")) != PAGE_ID
    ).lower()

    # SĐT — pattern 10 số bắt đầu bằng 0
    phones = re.findall(r"0\d{9}", all_customer_text)
    if phones:
        lead["phone"] = phones[0]

    # Tuổi — "X tuổi", "X t", "X tháng"
    age_m = re.search(r"(\d{1,2})\s*(tuổi|t\b)", all_customer_text)
    if age_m:
        lead["age"] = f"{age_m.group(1)} tuổi"
    else:
        month_m = re.search(r"(\d{1,2})\s*tháng", all_customer_text)
        if month_m:
            lead["age"] = f"{month_m.group(1)} tháng"

    # Khu vực
    areas = {
        "hòn gai": "Hòn Gai", "hon gai": "Hòn Gai",
        "hạ long": "Hạ Long", "ha long": "Hạ Long",
        "cẩm phả": "Cẩm Phả", "cam pha": "Cẩm Phả",
        "uông bí": "Uông Bí", "uong bi": "Uông Bí",
        "móng cái": "Móng Cái", "mong cai": "Móng Cái",
        "vân đồn": "Vân Đồn", "tình yêu": "Bãi Tình Yêu",
        "bạch đằng": "Bạch Đằng",
    }
    for kw, area_name in areas.items():
        if kw in all_customer_text:
            lead["area"] = area_name
            break

    # Đã học Pickleball chưa
    yes_kw = ["đã học", "đã chơi", "biết chơi", "chơi rồi", "có học", "chơi được", "đang chơi"]
    no_kw  = ["chưa học", "chưa chơi", "chưa biết", "mới bắt đầu", "mới tập", "chưa bao giờ"]
    if any(k in all_customer_text for k in yes_kw):
        lead["pickleball"] = "Đã học/chơi"
    elif any(k in all_customer_text for k in no_kw):
        lead["pickleball"] = "Chưa học"

    # Nhu cầu chính — khớp với dropdown Sheet
    if any(k in all_customer_text for k in ["trại hè", "trai he", "hè", "mùa hè", "camp"]):
        lead["nhu_cau"] = "Trại hè"
    elif any(k in all_customer_text for k in ["nâng cao", "nang cao", "advanced", "chơi rồi", "đã chơi"]):
        lead["nhu_cau"] = "Khóa nâng cao"
    elif any(k in all_customer_text for k in ["học thử", "hoc thu", "thử", "trải nghiệm", "trai nghiem"]):
        lead["nhu_cau"] = "Học thử"
    elif any(k in all_customer_text for k in ["cơ bản", "co ban", "mới học", "bắt đầu", "từ đầu"]):
        lead["nhu_cau"] = "Khóa cơ bản"
    else:
        lead["nhu_cau"] = "Chưa rõ"

    return lead


# ============================================================
# GOOGLE SHEET — UPSERT (cập nhật nếu đã có, thêm mới nếu chưa)
# ============================================================
def gsheet_upsert_lead(lead: dict, source_type: str = "inbox") -> str:
    """Ghi hoặc cập nhật lead vào Google Sheet. Trả về 'inserted'/'updated'/'error'."""
    if not GSHEET_WEBHOOK:
        return "error"
    try:
        payload = {
            "conv_key"    : lead.get("conv_key", ""),
            "ten"         : lead.get("parent", ""),
            "hoc_vien"    : lead.get("student", ""),
            "tuoi"        : lead.get("age", ""),
            "khu_vuc"     : lead.get("area", ""),
            "pickleball"  : lead.get("pickleball", ""),
            "sdt"         : lead.get("phone", ""),
            "nhu_cau"     : lead.get("nhu_cau", "Chưa rõ"),
            "nguon"       : "Facebook Fanpage" if source_type == "inbox" else "Fanpage Comment",
            "tinh_trang"  : "Mới tạo",
        }
        r = requests.post(GSHEET_WEBHOOK, json=payload, timeout=10)
        if r.status_code == 200:
            rj = r.json()
            action = rj.get("action", "unknown") if isinstance(rj, dict) else "unknown"
            log(f"  ✅ Sheet {action}: {lead.get('parent')} — {lead.get('phone','chưa SĐT')}")
            return action  # "inserted" hoặc "updated"
        else:
            log(f"  ⚠️ Sheet lỗi {r.status_code}: {r.text[:80]}")
            return "error"
    except Exception as e:
        log(f"  ⚠️ Lỗi ghi Sheet: {e}")
        return "error"

# ============================================================
# CLAUDE AI
# ============================================================
def strip_html(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&nbsp;", " ").replace("&#39;", "'").replace("&quot;", '"')
    return re.sub(r"\s+", " ", text).strip()


def build_conversation_history(messages: list) -> list:
    """
    Chuyển messages Pancake → Claude format.
    Pancake trả về tin cũ nhất trước (index 0 = cũ nhất).
    reversed() → lặp từ mới nhất → cũ nhất → history[0] = mới nhất.
    """
    NON_TEXT = {"[sticker]", "[hình ảnh]", "[file]", "[video]", "[audio]", "[gif]"}
    history = []
    for m in reversed(messages):
        raw  = m.get("original_message") or m.get("message", "")
        text = strip_html(str(raw)).strip()
        is_page = str(m.get("from", {}).get("id", "")) == PAGE_ID

        if not text or text.lower() in NON_TEXT:
            if not is_page:
                text = "(khách gửi hình hoặc sticker)"
            else:
                continue

        role = "assistant" if is_page else "user"
        if history and history[-1]["role"] == role:
            history[-1]["content"] += "\n" + text
        else:
            history.append({"role": role, "content": text})
    return history
    # history[0] = mới nhất, history[-1] = cũ nhất


def get_hardcoded_reply(history: list, customer_name: str):
    """Trả lời cứng cho các pattern phổ biến — bypass Claude."""
    if not history or len(history) < 1:
        return None

    last_user = ""
    last_page = ""
    for h in history:   # history[0] = mới nhất
        if h["role"] == "user" and not last_user:
            last_user = h["content"].lower()
        if h["role"] == "assistant" and not last_page:
            last_page = h["content"].lower()

    name = customer_name or "anh/chị"

    # Pattern: Inbox/Ib
    if any(k in last_user for k in ["inbox", "inboc", "ib ", "ib\n", "^ib$"]) and len(last_user) < 15:
        return f"Dạ chào {name}! Em là Linh từ QNPA ạ. {name} đang quan tâm đến chương trình Pickleball nào của bên em ạ? 😊"

    # Pattern: Địa chỉ — trả lời đúng theo khu vực, không bịa
    is_addr = any(k in last_user for k in [
        "địa chỉ", "chỗ học", "ở đâu", "sân ở", "học ở", "đường nào",
        "chỉ đường", "địa điểm", "cơ sở", "cs1", "cs2", "cơ sở 1",
        "cơ sở 2", "chi nhánh", "trung tâm ở", "sân tập", "sân học",
    ])
    is_cs2 = any(k in last_user for k in ["cơ sở 2", "cs2", "hòn gai", "cột 5", "hòn gay", "galaxy"])
    is_cs1 = any(k in last_user for k in ["cơ sở 1", "cs1", "bãi cháy", "bai chay", "hạ long star", "cái dăm"])
    if is_addr or is_cs1 or is_cs2 or any(k in last_user for k in ["hòn gai", "hạ long", "bãi cháy", "cẩm phả"]):
        if is_cs2:
            return f"Dạ cơ sở 2 bên Hòn Gai mình học tại Sân Sun Galaxy, Cột 5 ạ! {name} cho em SĐT để em gửi link Maps và lịch khai giảng luôn nhé 😊"
        elif is_cs1:
            return f"Dạ cơ sở 1 bên Bãi Cháy mình học tại Sân Hạ Long Star, Cái Dăm ạ! {name} cho em SĐT để em gửi link Maps và lịch khai giảng luôn nhé 😊"
        elif is_addr:
            return (f"Dạ bên em có 2 cơ sở ạ!\n"
                    f"📍 Cơ sở 1 — Hòn Gai: Sân Sun Galaxy, Cột 5\n"
                    f"📍 Cơ sở 2 — Bãi Cháy: Sân Hạ Long Star, Cái Dăm\n"
                    f"{name} đang ở khu vực nào ạ? 😊")
        else:
            return f"Dạ {name} đang ở khu vực đó thì bên em có sân gần, {name} cho em SĐT để em gửi địa chỉ chi tiết nhé 😊"

    # Pattern: Chi phí/học phí
    if any(k in last_user for k in ["chi phí", "học phí", "giá", "bao nhiêu tiền", "mấy tiền", "tốn bao nhiêu", "giá bao nhiêu", "phí"]):
        return f"Dạ học phí bên em có ưu đãi theo từng thời điểm, em không muốn báo sai cho {name} ạ. {name} cho em SĐT để chuyên viên gọi báo học phí chính xác và ưu đãi mới nhất sớm nhất nhé 😊"

    # Pattern: Chưa biết chọn
    if any(k in last_page for k in ["chương trình nào", "trại hè", "cơ bản", "nâng cao"]):
        if any(k in last_user for k in ["chưa biết", "xem hết", "không biết", "tất cả", "tuỳ", "chưa chọn"]):
            return (f"Dạ bên em có 2 nhóm ạ! Cho bé: Trại hè và Cơ bản. Người lớn: Cơ bản và Nâng cao. "
                    f"{name} cho em SĐT, em gọi tư vấn chọn đúng chương trình sớm nhất nhé 😊")

    # Pattern: Bực bội
    if any(k in last_user for k in ["đừng hỏi", "nói thẳng", "hỏi nhiều", "thôi nói đi", "cho biết giá luôn"]):
        return (f"Dạ em xin lỗi ạ! Học phí bên em có ưu đãi linh hoạt theo từng đợt, "
                f"{name} cho em SĐT để chuyên viên gọi báo chính xác sớm nhất nhé 😊")

    # Pattern: Lịch học
    if any(k in last_user for k in ["thứ mấy", "mấy giờ", "buổi nào", "thứ 7", "chủ nhật", "cuối tuần học"]):
        return (f"Dạ lịch chính quy Thứ 2 đến Thứ 6, 2 tiếng/buổi ạ. "
                f"CLB cuối tuần 300k/tháng cho học viên đã xong Cơ bản. "
                f"{name} cho em SĐT để em gửi lịch chi tiết và giữ chỗ nhé 🏓")

    # Pattern: Phân vân/hỏi gia đình
    if any(k in last_user for k in ["hỏi vợ", "hỏi chồng", "để tôi nghĩ", "bàn với", "hỏi thêm gia đình"]):
        return (f"Dạ {name} cứ hỏi thêm ạ! "
                f"Trong khi đó {name} cho em SĐT trước, em gửi tài liệu để cả nhà cùng xem, tiện hơn 😊")

    return None


def detect_conversation_hint(history: list) -> str:
    """Tạo hint tình huống cho Claude — history[0] = mới nhất."""
    if not history or len(history) < 2:
        return ""

    last_user = ""
    last_page = ""
    for h in history:
        if h["role"] == "user" and not last_user:
            last_user = h["content"].lower()
        if h["role"] == "assistant" and not last_page:
            last_page = h["content"].lower()

    hints = []
    turns_user = len([h for h in history if h["role"] == "user"])

    if any(k in last_page for k in ["chương trình nào", "trại hè", "cơ bản"]):
        if any(k in last_user for k in ["chưa biết", "xem hết", "tất cả", "tuỳ"]):
            hints.append("Khách chưa chọn được chương trình. KHÔNG hỏi lại. Tóm tắt 2 nhóm rồi xin SĐT.")

    if any(k in last_user for k in ["đừng hỏi", "nói thẳng", "hỏi nhiều"]):
        hints.append("Khách bực vì hỏi nhiều. KHÔNG hỏi thêm. Xin lỗi ngắn, xin SĐT luôn.")

    if any(k in last_user for k in ["thứ mấy", "mấy giờ", "cuối tuần"]):
        hints.append("Khách hỏi lịch học. Trả lời: T2-T6, 2h/buổi. CLB cuối tuần có. Rồi xin SĐT.")

    if any(k in last_user for k in ["hỏi vợ", "hỏi chồng", "để tôi nghĩ"]):
        hints.append("Khách phân vân. Khuyến khích, xin SĐT để gửi tài liệu cho cả nhà xem.")

    if turns_user >= 4 and not re.search(r"0\d{9}", " ".join(h["content"] for h in history)):
        hints.append(f"Đã {turns_user} lượt hội thoại, chưa có SĐT. ƯU TIÊN CAO NHẤT: xin SĐT trong tin này.")

    return "\n".join(hints)


def ask_claude(customer_name: str, messages: list):
    """Gọi Claude AI để soạn câu trả lời."""
    if not CLAUDE_API_KEY:
        return None, "CLAUDE_API_KEY chưa cấu hình"

    history = build_conversation_history(messages)
    if not history:
        return None, "Không có tin nhắn để phân tích"

    # history[0] = MỚI NHẤT — kiểm tra tin mới nhất phải là của khách
    if history[0]["role"] != "user":
        return None, "Tin nhắn cuối là của page — không cần trả lời"

    # Hardcoded patterns trước — nhanh, chính xác
    hardcoded = get_hardcoded_reply(history, customer_name)
    if hardcoded:
        log(f"  [pattern cứng]")
        return hardcoded, None

    # Hints động
    hint = detect_conversation_hint(history)
    extra = f"\n\nKhách hàng: {customer_name}"
    if hint:
        extra += f"\n\n⚠️ CHỈ DẪN HỆ THỐNG (ưu tiên tối cao):\n{hint}"

    # Claude nhận lịch sử theo thứ tự CŨ → MỚI (chronological)
    history_for_claude = list(reversed(history))

    payload = {
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 400,
        "system": QNPA_KNOWLEDGE + extra,
        "messages": history_for_claude,
    }
    headers = {
        "x-api-key": CLAUDE_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    _FALLBACK = (
        f"Dạ em là Linh từ QNPA ạ! {customer_name or 'Anh/chị'} cho em SĐT "
        f"để chuyên viên liên hệ tư vấn chi tiết sớm nhất nhé 😊"
    )
    for attempt in range(2):
        try:
            r = requests.post(CLAUDE_BASE, json=payload, headers=headers, timeout=45)
            if r.status_code != 200:
                err_text = r.text[:200]
                if "credit balance" in err_text or "too low" in err_text:
                    now_ts = datetime.now(timezone.utc)
                    last_credit_alert = getattr(ask_claude, "_last_credit_alert", None)
                    if not last_credit_alert or (now_ts - last_credit_alert).total_seconds() > 1800:
                        ask_claude._last_credit_alert = now_ts
                        tg_alert("⛔ Claude API hết credit — vào console.anthropic.com/billing để nạp tiền. Bot tạm dừng trả lời.")
                    log(f"  ⛔ Claude hết credit — bỏ qua {customer_name}")
                    return None, f"Claude lỗi {r.status_code}"
                else:
                    # Rate-limit alert: chỉ gửi Telegram 1 lần/30 phút, không spam
                    now_ts = datetime.now(timezone.utc)
                    last_api_alert = getattr(ask_claude, "_last_api_alert", None)
                    if not last_api_alert or (now_ts - last_api_alert).total_seconds() > 1800:
                        ask_claude._last_api_alert = now_ts
                        tg_alert(f"⚠️ Claude API lỗi {r.status_code} — kiểm tra API key hoặc quota. Bot tạm dừng.")
                    log(f"  ⚠️ Claude API lỗi {r.status_code}: {err_text[:100]}")
                    return None, f"Claude lỗi {r.status_code}"
            data = r.json()
            content = data.get("content") if isinstance(data, dict) else None
            if not content or not isinstance(content, list) or not content[0]:
                return None, f"Claude response rỗng: {str(data)[:80]}"
            return content[0].get("text", "").strip(), None
        except requests.exceptions.Timeout:
            if attempt == 0:
                log(f"  ⏳ Claude timeout lần 1 — thử lại...")
                continue
            log(f"  ⚠️ Claude timeout 2 lần — dùng fallback cho {customer_name}")
            return _FALLBACK, None
        except Exception as e:
            log(f"  ⚠️ Claude exception: {e}")
            return None, str(e)


# ============================================================
# INSTANCE ID — unique mỗi lần khởi động, dùng cho GSheet conv lock
# ============================================================
import uuid as _uuid
INSTANCE_ID = _uuid.uuid4().hex[:8]

def gsheet_claim_conv(conv_id: str, snippet_key: str) -> bool:
    """Atomic lock qua GSheet LockService. True = mình được xử lý. False = instance khác đang xử lý."""
    if not GSHEET_WEBHOOK:
        return True  # không có webhook → không lock, cứ tiếp tục
    lock_key = f"conv_{conv_id}_{snippet_key[:20]}"
    try:
        r = requests.post(GSHEET_WEBHOOK, json={
            "action"      : "claim_conv",
            "lock_key"    : lock_key,
            "instance_id" : INSTANCE_ID,
        }, timeout=7)
        return r.json().get("claimed", True)
    except Exception as _e:
        log(f"  ⚠️ claim_conv lỗi: {_e} — tiếp tục không lock")
        return True

# ============================================================
# TRẠNG THÁI SESSION
# ============================================================
_replied_convs: dict = {}   # conv_id → snippet đã trả lời (reset khi có tin mới)
_blocked_convs: set  = set()  # chỉ block #100 (không tìm thấy user) — không block #551
_lead_store: dict    = {}   # conv_id → lead dict (tích lũy qua các lượt)

_stats = {
    "new_inbox"       : 0,
    "processed"       : 0,
    "leads"           : 0,
    "full_leads"      : 0,
    "no_reply"        : 0,
    "manual_needed"   : 0,
    "comments"        : 0,
    "followup_2h"     : 0,   # agent tự chăm sau 2h im lặng
    "followup_10h"    : 0,   # agent tự chăm sau 10h im lặng
    "followup_20h"    : 0,   # agent tự chăm sau 20h im lặng
    "followup_manual" : 0,   # gửi thủ công >24h qua gui_followup.py
    "errors"          : [],
    "top_questions"   : [],
}
# conv_id → {"name": str, "cust_id": str, "page_ts": datetime UTC, "tiers": set}
_followup_store: dict  = {}
_leads_counted:  set   = set()  # conv_id đã đếm SĐT — tránh đếm 2 lần
_last_replied:   dict  = {}     # conv_id → datetime — cooldown 60s tránh reply 2 lần
# conv_id → snippet_key — những conv nhân viên đã gửi thủ công (không phải bot)
_human_sent_tracked: dict = {}
_STATS_FILE      = os.path.join(_BASE_DIR, "stats_today.json")
_HUMAN_SENT_FILE = os.path.join(_BASE_DIR, "human_sent_today.json")


def load_human_sent():
    """Load danh sách conv nhân viên đã gửi hôm nay (để không đếm 2 lần sau restart)"""
    import json as _json
    global _human_sent_tracked
    try:
        if _os.path.exists(_HUMAN_SENT_FILE):
            # Chỉ load nếu file được tạo trong ngày hôm nay
            mtime = _os.path.getmtime(_HUMAN_SENT_FILE)
            from datetime import date
            if datetime.fromtimestamp(mtime).date() == date.today():
                with open(_HUMAN_SENT_FILE, encoding="utf-8") as f:
                    _human_sent_tracked = _json.load(f)
                log(f"Loaded {len(_human_sent_tracked)} human-sent convs từ file")
    except Exception:
        pass


def save_human_sent():
    import json as _json
    try:
        with open(_HUMAN_SENT_FILE, "w", encoding="utf-8") as f:
            _json.dump(_human_sent_tracked, f, ensure_ascii=False)
    except Exception:
        pass


def save_stats():
    import json
    global _leads_counted
    try:
        data = dict(_stats)
        data["_leads_counted"]  = list(_leads_counted)
        data["_report_sent"]    = _report_sent          # lưu để tránh gửi lại sau restart
        with open(_STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def load_stats():
    """Khôi phục stats + _leads_counted + _report_sent từ file khi restart"""
    import json as _json, os as _os
    global _stats, _leads_counted, _report_sent
    if not _os.path.exists(_STATS_FILE):
        return
    try:
        with open(_STATS_FILE, encoding="utf-8") as f:
            saved = _json.load(f)
        for k in _stats:
            if k in saved:
                _stats[k] = saved[k]
        if "_leads_counted" in saved:
            _leads_counted = set(saved["_leads_counted"])
        if "_report_sent" in saved:
            _report_sent.update(saved["_report_sent"])
            log(f"📂 Đã load report_sent: {_report_sent}")
        log(f"📂 Đã load stats: leads={_stats['leads']} | inbox={_stats['new_inbox']} | processed={_stats['processed']} | leads_counted={len(_leads_counted)}")
    except Exception as e:
        log(f"⚠️ load_stats lỗi: {e}")

# ============================================================
# FILE LOG
# ============================================================
import os as _os
_log_path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "agent_linh.log")

def log(msg: str):
    ts   = datetime.now().strftime("%d/%m %H:%M:%S")
    line = f"{ts}  {msg}"
    print(line)
    try:
        with open(_log_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


# ============================================================
# XỬ LÝ DANH SÁCH HỘI THOẠI
# ============================================================
MAX_CLAUDE_CALLS_PER_CYCLE = 5  # Tối đa 5 lần gọi Claude mỗi cycle — tránh burst tốn tiền

def process_conv_list(convs: list, source_type: str = "inbox"):
    processed = 0
    claude_calls_this_cycle = 0
    errors    = []

    # Dedup: Pancake đôi khi trả về cùng conv_id 2 lần trong 1 lần poll
    seen_in_cycle: set = set()
    deduped = []
    for _c in convs:
        _cid = _c.get("id")
        if _cid and _cid not in seen_in_cycle:
            seen_in_cycle.add(_cid)
            deduped.append(_c)
    convs = deduped

    for c in convs:
        if not isinstance(c, dict):
            continue
        _lsb           = c.get("last_sent_by") or {}
        last_sent_by   = _lsb if isinstance(_lsb, dict) else {}
        last_sender_id = str(last_sent_by.get("id", ""))
        conv_id        = c.get("id", "")
        if not conv_id:
            continue

        # Bỏ qua nếu page đã trả lời — nhưng kiểm tra xem bot hay nhân viên gửi
        if last_sender_id == PAGE_ID:
            snippet      = c.get("snippet", "")[:120]
            snippet_key  = snippet[:60]
            customers    = c.get("customers", [])
            _c0          = customers[0] if customers else {}
            _c0          = _c0 if isinstance(_c0, dict) else {}
            cust_name    = _c0.get("name", "?")
            # Nếu conv này KHÔNG có trong _replied_convs (bot chưa reply)
            # → nhân viên gửi thủ công → đếm vào followup_manual
            bot_sent_key = _replied_convs.get(conv_id)
            already_tracked = _human_sent_tracked.get(conv_id)
            if bot_sent_key != snippet_key and already_tracked != snippet_key:
                _stats["followup_manual"] += 1
                _human_sent_tracked[conv_id] = snippet_key
                save_human_sent()
                log(f"  👤 Nhân viên gửi thủ công → {cust_name}: \"{snippet_key[:50]}\"")
            continue
        # Bỏ qua nếu đã bị Facebook block vĩnh viễn
        if conv_id in _blocked_convs:
            continue

        customers   = c.get("customers", [])
        _cust0      = customers[0] if customers else {}
        _cust0      = _cust0 if isinstance(_cust0, dict) else {}
        customer    = _cust0.get("name", "Khách hàng")
        customer_id = _cust0.get("id")
        snippet     = c.get("snippet", "")[:120]
        snippet_key = snippet[:60]

        # Lọc conversation cũ — chỉ xử lý nếu có hoạt động trong 30 phút qua
        # Dùng updated_at vì hoạt động cho cả inbox lẫn comment
        updated_str = c.get("updated_at") or ""
        if updated_str:
            try:
                upd = datetime.fromisoformat(updated_str.replace("Z", "+00:00"))
                if upd.tzinfo is None:
                    upd = upd.replace(tzinfo=timezone.utc)
                age_min = (datetime.now(timezone.utc) - upd).total_seconds() / 60
                max_age = 30 if source_type == "inbox" else 2880  # inbox: 30 phút | comment: 48 tiếng (comment công khai không giới hạn 24h như inbox)
                if age_min > max_age:
                    _replied_convs[conv_id] = snippet_key
                    continue
            except Exception:
                pass

        # Kiểm tra 24h Facebook rule — CHỈ áp dụng cho inbox
        # Comment không dùng last_customer_interactive_at vì trường này trả về ngày đăng bài gốc
        last_active_str = ""
        if source_type == "inbox":
            last_active_str = c.get("last_customer_interactive_at") or ""
            if last_active_str:
                try:
                    la = datetime.fromisoformat(last_active_str.replace("Z", "+00:00"))
                    if la.tzinfo is None:
                        la = la.replace(tzinfo=timezone.utc)
                    age_h = (datetime.now(timezone.utc) - la).total_seconds() / 3600
                    if age_h > 23:
                        if conv_id not in _replied_convs:
                            log(f"  ⏰ Tin cũ {age_h:.0f}h — {customer} — bỏ qua")
                            _replied_convs[conv_id] = snippet_key
                        continue
                except Exception:
                    pass

        # Bỏ qua nếu snippet y hệt lần trước (chưa có tin mới)
        if conv_id in _replied_convs and _replied_convs[conv_id] == snippet_key:
            continue

        # Bỏ qua nếu vừa reply trong vòng 60 giây (tránh reply 2 lần khi snippet đổi)
        last_r = _last_replied.get(conv_id)
        if last_r and (datetime.now(timezone.utc) - last_r).total_seconds() < 60:
            continue

        ts_display = (last_active_str[:10] if source_type == "inbox" and last_active_str else c.get("updated_at", "")[:10]) or "no-ts"
        log(f"\n→ [{source_type}] {customer}: \"{snippet[:60]}\" | ts={ts_display}")
        _stats["new_inbox"] += 1

        # Lấy tin nhắn
        messages = get_messages(conv_id, customer_id=customer_id, limit=20)
        if not messages:
            log(f"  ✗ Không lấy được tin nhắn")
            continue

        # Trích xuất thông tin lead từ toàn bộ hội thoại
        lead = extract_lead_info(messages, customer)
        lead["conv_key"] = conv_id

        # Gộp với lead cũ nếu có (cập nhật dần)
        prev = _lead_store.get(conv_id, {})
        for k in ("phone", "age", "area", "pickleball", "student"):
            if not prev.get(k) or prev.get(k) in ("Chưa có", "Chưa rõ", ""):
                if lead.get(k) and lead[k] not in ("Chưa có", "Chưa rõ", ""):
                    prev[k] = lead[k]
        prev["parent"]   = lead.get("parent", prev.get("parent", customer))
        prev["conv_key"] = conv_id
        _lead_store[conv_id] = prev
        lead = prev  # dùng lead đã merge

        # Cooldown 120s — nếu vừa reply conv này thì bỏ qua (tránh gửi 2 lần khi khách nhắn nhanh)
        last_r = _last_replied.get(conv_id)
        if last_r and (datetime.now(timezone.utc) - last_r).total_seconds() < 120:
            log(f"  ⏳ Cooldown {customer} — vừa reply {int((datetime.now(timezone.utc)-last_r).total_seconds())}s trước")
            _replied_convs[conv_id] = snippet_key
            continue

        # ── GSheet Atomic Lock (LockService) — chỉ 1 instance được xử lý conv này ──
        if not gsheet_claim_conv(conv_id, snippet_key):
            log(f"  🔒 {customer} — instance khác đang xử lý, bỏ qua")
            _replied_convs[conv_id] = snippet_key
            continue

        # Đánh dấu đang xử lý NGAY — tránh cycle tiếp theo (8s sau) xử lý lại trước khi send xong
        _replied_convs[conv_id] = snippet_key

        # Đếm SĐT và ghi Sheet — Google Sheet là nguồn sự thật chống lặp qua Railway restart
        phone_detected = lead.get("phone", "")
        if phone_detected:
            sheet_action = gsheet_upsert_lead(lead, source_type)
            # Chỉ gửi HOT LEAD nếu Sheet xác nhận lead MỚI (inserted) — không phải update cũ
            if sheet_action == "inserted" and conv_id not in _leads_counted:
                _leads_counted.add(conv_id)
                _stats["leads"] += 1
                full = all(lead.get(k) not in ("Chưa có", "Chưa rõ", "") for k in ("age", "area", "pickleball"))
                if full:
                    _stats["full_leads"] += 1
                tg_hot_lead(lead)
            elif sheet_action == "updated":
                _leads_counted.add(conv_id)  # đánh dấu để bỏ qua lần sau trong session này

        # Giới hạn số lần gọi Claude mỗi cycle — tránh burst tốn tiền khi restart
        if claude_calls_this_cycle >= MAX_CLAUDE_CALLS_PER_CYCLE:
            log(f"  ⏸ Đạt giới hạn {MAX_CLAUDE_CALLS_PER_CYCLE} Claude calls/cycle — {customer} xử lý cycle sau")
            _replied_convs.pop(conv_id, None)  # cho phép xử lý cycle sau
            continue

        # Gọi Claude
        claude_calls_this_cycle += 1
        reply, err = ask_claude(customer, messages)
        if err:
            if "không cần trả lời" in err.lower():
                log(f"  → Bỏ qua: {err}")
                _replied_convs[conv_id] = snippet_key
            else:
                log(f"  ✗ Claude lỗi: {err}")
                errors.append(f"{customer}: {err}")
                _replied_convs.pop(conv_id, None)  # cho phép retry cycle sau
            continue

        log(f"  ✓ Linh soạn: {reply[:80]}...")

        # ── Anti-duplicate: random sleep + double Pancake check trước khi gửi ──
        # Nếu 2 instance cùng soạn xong: instance nào ngủ ít hơn sẽ gửi trước,
        # instance còn lại thức dậy thấy page đã gửi rồi → bỏ qua.
        # ── Anti-duplicate: sleep ngẫu nhiên rộng + 3 lần check Pancake ──
        # Instance nào ngủ ít hơn sẽ gửi trước; instance còn lại check lần 2/3 thấy page đã gửi → bỏ qua
        import random as _rnd

        def _last_msg_is_from_page(msgs):
            if not msgs:
                return False
            return str(msgs[-1].get("from", {}).get("id", "")) == PAGE_ID

        def _pancake_check(label):
            try:
                _msgs = get_messages(conv_id, customer_id=customer_id, limit=5)
                if _last_msg_is_from_page(_msgs):
                    log(f"  🔒 {label}: {customer} — page đã reply, bỏ qua")
                    _replied_convs[conv_id] = snippet_key
                    _last_replied[conv_id] = datetime.now(timezone.utc)
                    return True
            except Exception as _e:
                log(f"  ⚠️ {label} lỗi: {_e}")
            return False

        # Check lần 1 trước khi ngủ
        if _pancake_check("Pre-send #1"):
            continue

        # Ngủ random 3–8s — khoảng rộng để 2 instance không trùng nhau
        _jitter = 0.5 + _rnd.uniform(0, 1.5)  # Railway Teardown = 1 instance → chỉ cần sleep ngắn
        log(f"  ⏱ Anti-dup sleep {_jitter:.1f}s...")
        time.sleep(_jitter)

        # Check lần 2 sau khi ngủ — nếu instance kia đã gửi trong lúc ta ngủ
        if _pancake_check("Pre-send #2"):
            continue

        # Sleep thêm 1s cố định rồi check lần 3 — lưới cuối cùng
        time.sleep(0.5)
        if _pancake_check("Pre-send #3"):
            continue

        result = send_message(conv_id, reply, customer_id=customer_id, source_type=source_type)
        if not isinstance(result, dict):
            result = {}
        send_ok = result.get("dry_run") or result.get("success") or result.get("message_id") or result.get("id")

        if send_ok:
            processed += 1
            _stats["processed"] += 1
            _last_replied[conv_id] = datetime.now(timezone.utc)  # cooldown 60s

            # Đăng ký theo dõi để tự chăm lại nếu KH im lặng (2h/10h/20h)
            phone_now = lead.get("phone", "")
            if not phone_now:  # Chưa có SĐT → cần chăm tiếp
                prev_fu = _followup_store.get(conv_id, {})
                _followup_store[conv_id] = {
                    "replied_at" : datetime.now(timezone.utc),
                    "name"       : customer,
                    "cust_id"    : customer_id,
                    "f2h"        : prev_fu.get("f2h", False),
                    "f10h"       : prev_fu.get("f10h", False),
                    "f20h"       : prev_fu.get("f20h", False),
                }
            else:
                # Đã có SĐT → không cần chăm thêm
                _followup_store.pop(conv_id, None)

            # Không ghi Sheet khi chưa có SĐT — chỉ nhập lead khi đã xin được số điện thoại

        else:
            err_msg = result.get("message", str(result))[:120]
            log(f"  ✗ Pancake từ chối gửi: {err_msg}")
            if "551" in err_msg or "không có mặt" in err_msg.lower():
                # Tài khoản hạn chế tạm thời — thử lại sau 5 phút
                _last_replied[conv_id] = datetime.now(timezone.utc) - timedelta(seconds=240)
                _replied_convs.pop(conv_id, None)  # xóa để retry qua được check snippet
                log(f"  ⏭ 551 {customer} — thử lại sau ~5 phút")
            elif "100" in err_msg or "không tìm thấy" in err_msg.lower():
                # User không tồn tại — block vĩnh viễn
                _blocked_convs.add(conv_id)
                _replied_convs[conv_id] = snippet_key
            elif "#10" in err_msg or "ngoài khoảng thời gian" in err_msg or "outside" in err_msg.lower():
                # Quá 24h — block vĩnh viễn, cần gửi thủ công
                _blocked_convs.add(conv_id)
                _replied_convs[conv_id] = snippet_key
                _stats["manual_needed"] += 1
                log(f"  ⏰ Block {customer} — quá 24h FB rule (#10)")
            else:
                # Lỗi không xác định — xóa đánh dấu để retry cycle sau
                _replied_convs.pop(conv_id, None)
                errors.append(f"{customer}: {err_msg}")
                _stats["errors"].append(f"{customer}: {err_msg[:60]}")

        time.sleep(0.5)

    return processed, errors


_FOLLOWUP_SCRIPTS = {
    "2h": (
        "Dạ {name} ơi! 😊 Em Linh từ QNPA hỏi thăm ạ.\n"
        "Anh/chị có muốn em tư vấn thêm về lịch học thử miễn phí không ạ? "
        "Bé đến thử 1 buổi, thích mới đăng ký tiếp ạ!"
    ),
    "10h": (
        "Dạ {name} ơi! Bên em vừa cập nhật lịch học thử cuối tuần này — "
        "suất còn hạn chế lắm ạ. 🏓\n"
        "Anh/chị muốn em giữ suất cho bé không ạ?"
    ),
    "20h": (
        "Dạ {name} ơi! Em hỏi thăm lần cuối — bên em đang có ưu đãi "
        "1 buổi học thử miễn phí, không cần cam kết gì ạ. 🎁\n"
        "Anh/chị cho em số điện thoại để em gửi lịch cụ thể nhé!"
    ),
}


def process_followups():
    """Chủ động chăm lại KH im lặng sau 2h / 10h / 20h"""
    now = datetime.now(timezone.utc)
    for conv_id, info in list(_followup_store.items()):
        if conv_id in _blocked_convs:
            continue
        replied_at = info.get("replied_at")
        if not replied_at:
            continue
        age_h = (now - replied_at).total_seconds() / 3600
        name  = info.get("name", "anh/chị")
        cid   = info.get("cust_id")

        # Kiểm tra xem khách đã reply lại chưa — nếu có thì xóa khỏi followup_store
        convs = get_conversations(10, "inbox")
        for c in convs:
            if c["id"] == conv_id:
                last_sender = str((c.get("last_sent_by") or {}).get("id", ""))
                if last_sender != PAGE_ID:
                    # Khách đã reply lại → thôi chăm
                    _followup_store.pop(conv_id, None)
                break

        if conv_id not in _followup_store:
            continue

        # Dùng latest-wins: chỉ gửi 1 tin/lần, ưu tiên mốc cao nhất chưa gửi
        # Tránh spam khi agent bị tắt lâu rồi bật lại
        if age_h >= 20 and not info.get("f20h"):
            tier, stat_key = "20h", "followup_20h"
            info["f2h"] = info["f10h"] = True   # bỏ qua 2h/10h nếu chưa kịp gửi
        elif age_h >= 10 and not info.get("f10h"):
            tier, stat_key = "10h", "followup_10h"
            info["f2h"] = True   # bỏ qua 2h nếu chưa kịp gửi
        elif age_h >= 2 and not info.get("f2h"):
            tier, stat_key = "2h", "followup_2h"
        else:
            continue

        script = _FOLLOWUP_SCRIPTS[tier].format(name=name)

        # GSheet lock — chống 3 instance cùng gửi followup cho 1 khách
        fu_key = f"fu_{conv_id}_{tier}_{datetime.now(timezone.utc).strftime('%Y%m%d')}"
        if GSHEET_WEBHOOK:
            try:
                if gsheet_check_report(fu_key):
                    log(f"  🔒 Followup {tier} → {name} đã gửi bởi instance khác")
                    info[f"f{tier}"] = True
                    continue
                gsheet_mark_report(fu_key)
            except Exception:
                pass

        # Pre-send Pancake check — chắc chắn nhất
        try:
            pre = get_messages(conv_id, customer_id=cid, limit=3)
            if pre and str(pre[-1].get("from", {}).get("id", "")) == PAGE_ID:
                fresh = strip_html(pre[-1].get("original_message") or pre[-1].get("message", ""))
                if fresh[:60] == script[:60]:
                    log(f"  🔒 Pre-send followup {tier} → {name} đã gửi rồi")
                    info[f"f{tier}"] = True
                    continue
        except Exception:
            pass

        result = send_message(conv_id, script, customer_id=cid)
        ok = result.get("dry_run") or result.get("success") or result.get("message_id") or result.get("id")
        if ok:
            info[f"f{tier}"] = True
            _stats[stat_key] += 1
            log(f"  ↩ Follow {tier} → {name}")
        elif "#10" in str(result.get("message", "")) or "outside" in str(result.get("message", "")).lower():
            _blocked_convs.add(conv_id)
            _stats["manual_needed"] += 1
            _followup_store.pop(conv_id, None)
        time.sleep(0.5)


def warm_up_replied_convs():
    """Chạy 1 lần khi khởi động: đánh dấu conv page đã reply để không reply lại sau restart"""
    log("🔄 Warm-up: đọc lại trạng thái conversations...")
    try:
        inbox    = get_conversations(50, "inbox")
        comments = get_conversations(30, "comment")
        count = 0
        for c in (inbox + comments):
            if not isinstance(c, dict):
                continue
            _lsb           = c.get("last_sent_by") or {}
            last_sent_by   = _lsb if isinstance(_lsb, dict) else {}
            last_sender_id = str(last_sent_by.get("id", ""))
            conv_id        = c.get("id", "")
            snippet_key    = c.get("snippet", "")[:60]
            if conv_id and last_sender_id == PAGE_ID:
                _replied_convs[conv_id] = snippet_key
                count += 1
        log(f"✅ Warm-up xong: đánh dấu {count} conv đã reply — sẽ không reply lại")
    except Exception as e:
        log(f"⚠️ Warm-up lỗi: {e}")


def process_unanswered():
    inbox_convs   = get_conversations(50, "inbox")
    p1, e1        = process_conv_list(inbox_convs, "inbox")
    comment_convs = get_conversations(30, "comment")
    p2, e2        = process_conv_list(comment_convs, "comment")
    process_followups()
    return p1 + p2, e1 + e2


# ============================================================
# BÁO CÁO 12h VÀ 22h
# ============================================================
_report_sent = {"noon": False, "evening": False, "midday": False, "midnight": False}
_last_heartbeat_min = -1  # phút cuối gửi heartbeat

def check_heartbeat():
    pass  # Tắt heartbeat — im lặng khi bình thường, chỉ alert khi restart/lỗi

_agent_start_time = datetime.now(timezone.utc)

def fetch_live_stats(target_date=None):
    """Lấy số liệu thực từ Pancake API — không phụ thuộc _stats trong bộ nhớ.
    target_date: date object VN, mặc định là hôm nay. Báo cáo 0h truyền vào hôm qua."""
    VN = timezone(timedelta(hours=7))
    if target_date is None:
        target_date = datetime.now(VN).date()
    phone_re = re.compile(r"0\d{9}")

    def get_msgs(conv_id, cust_id=None):
        url = f"{BASE}/pages/{PAGE_ID}/conversations/{conv_id}/messages?access_token={PANCAKE_TOKEN}&limit=30"
        if cust_id: url += f"&customer_id={cust_id}"
        try: return requests.get(url, timeout=10).json().get("messages", [])
        except: return []

    def is_target_day(ts):
        if not ts: return False
        try:
            t = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
            if t.tzinfo is None: t = t.replace(tzinfo=timezone.utc)
            return t.astimezone(VN).date() == target_date
        except: return False

    inbox_count = 0
    comment_count = 0
    leads = {}  # conv_id → {name, phone}

    for c in get_conversations(100, "inbox"):
        if not isinstance(c, dict): continue
        if not is_target_day(c.get("last_customer_interactive_at") or c.get("updated_at")): continue
        inbox_count += 1
        conv_id = c.get("id", "")
        cust = (c.get("customers") or [{}])[0]
        cust = cust if isinstance(cust, dict) else {}
        msgs = get_msgs(conv_id, cust.get("id"))
        txt = " ".join(str(m.get("message","") or m.get("original_message","")) for m in msgs
                       if str((m.get("from") or {}).get("id","")) != PAGE_ID)
        phones = phone_re.findall(txt)
        if phones: leads[conv_id] = {"name": cust.get("name","?"), "phone": phones[0]}

    for c in get_conversations(50, "comment"):
        if not isinstance(c, dict): continue
        if not is_target_day(c.get("updated_at")): continue
        comment_count += 1
        conv_id = c.get("id", "")
        cust = (c.get("customers") or [{}])[0]
        cust = cust if isinstance(cust, dict) else {}
        msgs = get_msgs(conv_id, cust.get("id"))
        txt = " ".join(str(m.get("message","") or m.get("original_message","")) for m in msgs
                       if str((m.get("from") or {}).get("id","")) != PAGE_ID)
        phones = phone_re.findall(txt)
        if phones: leads[conv_id] = {"name": cust.get("name","?"), "phone": phones[0]}

    return {"inbox": inbox_count, "comments": comment_count, "leads": leads}


def check_and_send_daily_report():
    """Gửi báo cáo 14:00 và 0:00 giờ VN — dữ liệu từ Pancake API thực tế"""
    global _report_sent
    # Không gửi báo cáo trong 90 giây đầu sau khởi động
    # — tránh instance mới Railway gửi trùng với instance cũ
    uptime = (datetime.now(timezone.utc) - _agent_start_time).total_seconds()
    if uptime < 90:
        return

    now = datetime.now(timezone(timedelta(hours=7)))
    h, m = now.hour, now.minute

    VN_date = now.strftime("%d/%m/%Y")

    # ── Báo cáo 14h — check cả window 14:00-14:09 để không miss khi restart ──
    if h == 14 and m < 10 and not _report_sent["midday"]:
        key = f"midday_{VN_date}"
        if not gsheet_check_report(key):
            gsheet_mark_report(key)
            _report_sent["midday"] = True
            live = fetch_live_stats()
            tg_report_14h_live(live)
            log(f"📊 Đã gửi báo cáo giữa ngày (14h) — {len(live['leads'])} leads")
        else:
            _report_sent["midday"] = True  # đã gửi rồi, không gửi lại

    elif h == 15:
        _report_sent["midday"] = False

    # ── Báo cáo 0h — check cả window 0:00-0:09 ──
    if h == 0 and m < 10 and not _report_sent["midnight"]:
        VN = timezone(timedelta(hours=7))
        yesterday = (datetime.now(VN) - timedelta(days=1)).date()
        key = f"midnight_{yesterday.strftime('%d/%m/%Y')}"
        if not gsheet_check_report(key):
            gsheet_mark_report(key)
            _report_sent["midnight"] = True
            live = fetch_live_stats(target_date=yesterday)
            tg_report_24h_live(live)
            log(f"📊 Đã gửi tổng kết ngày {yesterday} — {len(live['leads'])} leads")
            _human_sent_tracked.clear()
            save_human_sent()
        else:
            _report_sent["midnight"] = True  # đã gửi rồi

    elif h == 1:
        _report_sent["midnight"] = False


# ============================================================
# HEALTH CHECK SERVER (cho UptimeRobot theo dõi)
# ============================================================
def start_health_server():
    """Chạy HTTP server nhỏ trên port 8080 — UptimeRobot ping mỗi 5 phút"""
    import threading
    from http.server import HTTPServer, BaseHTTPRequestHandler
    class HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            body = f"OK leads={_stats.get('leads',0)} processed={_stats.get('processed',0)}".encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(body)
        def log_message(self, *args): pass  # tắt log mỗi request
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    log(f"🌐 Health server chạy trên port {port}")

# ============================================================
# VÒNG LẶP CHÍNH
# ============================================================
def run_loop():
    log(f"QNPA AI Agent v2.0 khởi động (poll mỗi {POLL_INTERVAL}s)")
    log(f"Log: {_log_path}")
    start_health_server()
    load_stats()        # Khôi phục stats từ file — tránh mất số liệu khi restart
    load_human_sent()   # Khôi phục danh sách nhân viên đã gửi hôm nay (nếu có)
    warm_up_replied_convs()  # Đánh dấu conv đã reply trước khi vào loop — tránh reply lại sau restart
    if DRY_RUN:
        log("⚠️ DRY RUN — không gửi tin thật")

    tg_send(CHAT_COACHING,
        "🟢 <b>QNPA Agent v2.0 đã khởi động</b>\n"
        "📌 Chế độ: HOT LEAD + Báo cáo 12h & 22h\n"
        "🔕 Đã tắt thông báo rác Telegram\n"
        "⏱ Poll mỗi 15 giây"
    )

    cycle = 0
    while True:
        try:
            process_unanswered()
            check_heartbeat()
            check_and_send_daily_report()
            cycle += 1

            if cycle % 4 == 0:
                now_s = datetime.now(timezone(timedelta(hours=7))).strftime("%H:%M:%S")
                log(f"[{now_s}] cycle #{cycle} — leads: {_stats['leads']} | processed: {_stats['processed']}")
                save_stats()

        except KeyboardInterrupt:
            log("Đã dừng Agent.")
            tg_send(CHAT_COACHING, "🔴 <b>QNPA Agent đã dừng</b>")
            _release_lock()
            break
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            log(f"LỖI KHÔNG MONG ĐỢI: {e}\n{tb}")
            tg_alert(f"Agent lỗi nghiêm trọng: {e}")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    try:
        run_loop()
    finally:
        _release_lock()
