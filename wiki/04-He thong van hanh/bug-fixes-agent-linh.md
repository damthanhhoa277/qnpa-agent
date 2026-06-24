---
name: bug-fixes-agent-linh
description: Nhật ký toàn bộ bug đã fix trên Agent Linh — đọc trước khi sửa code để không làm hỏng fix cũ
metadata:
  type: project
---

# NHẬT KÝ BUG ĐÃ FIX — AGENT LINH

> ⚠️ ĐỌC KỸ TRƯỚC KHI SỬA CODE. Mỗi fix bên dưới đã được kiểm chứng thực tế. Đừng revert.

---

## BUG 1 — Không trả lời khách (max_age quá hẹp)
**Triệu chứng:** Khách nhắn → bot im lặng 19–39 phút sau restart Railway
**Nguyên nhân:** `max_age = 30 phút` → conv cũ hơn 30 phút bị bỏ qua sau restart
**Fix:** `max_age = 120 phút` cho inbox (đủ bắt kịp sau restart ngắn, không flood conv cũ)
**File:** `qnpa_agent.py` dòng ~962
**Không được đổi lại:** Đừng giảm xuống dưới 60 phút — Railway restart mất ~3-5 phút, cần buffer

---

## BUG 2 — 200 Claude calls/ngày (vòng lặp vô hạn)
**Triệu chứng:** Telegram báo "đã gọi 200 lần hôm nay"
**Nguyên nhân 1:** Pancake trả về `{}` (empty) khi không gửi được → agent xóa `_replied_convs` → retry mỗi 5s → lặp mãi
**Nguyên nhân 2:** Railway deploy nhiều lần → `_claude_calls_today` reset → đếm lại từ 0
**Fix:**
- `_send_fail_count[conv_id]`: sau 3 lần Pancake/Claude lỗi → block conv vĩnh viễn
- Persist `_claude_calls_today` vào `stats_today.json` qua restart
- `MAX_CLAUDE_CALLS_PER_CYCLE = 3` (không tăng lên)
**File:** `qnpa_agent.py` dòng ~744, ~898, ~1076, ~1176

---

## BUG 3 — Claude API lỗi 400 (spend limit)
**Triệu chứng:** Bot dừng hoàn toàn, Telegram báo "Claude API lỗi 400"
**Nguyên nhân:** Monthly spend limit $30 hết; CLAUDE_API_KEY chưa có trong Railway Variables
**Fix:**
- Tăng spend limit lên $50 trong Anthropic console
- Thêm CLAUDE_API_KEY vào Railway Variables
- Code fallback: khi lỗi 400 → gửi tin mẫu thay vì bỏ qua khách
**Model đúng:** `claude-haiku-4-5-20251001` — KHÔNG dùng `claude-3-5-haiku-20241022` (trả 404)

---

## BUG 4 — HOT LEAD mất hoàn toàn (AppScript rỗng)
**Triệu chứng:** Khách để lại SĐT nhưng không có gì trong Sheet, không có alert Telegram
**Nguyên nhân:** `HOTLEAD_AppScript.js` rỗng → gsheet_upsert_lead trả `"updated"` (exception) → bỏ qua HOT LEAD
**Fix:**
- Viết lại AppScript đầy đủ với upsert + claim_conv + dedup
- Khi sheet_action == "error" → VẪN gửi HOT LEAD Telegram (không để mất lead)
**Invariant quan trọng:** `if phone_detected:` bảo vệ → chỉ ghi Sheet khi có SĐT

---

## BUG 5 — Sheet không tìm được tab "LEAD THÁNG 6" (encoding)
**Triệu chứng:** AppScript trả `{"error":"sheet not found: LEAD TH?NG 6"}`
**Nguyên nhân:** Chữ "Á" bị corrupt khi deploy AppScript standalone
**Fix:** Hàm `getLeadSheet(ss)` tìm sheet theo keyword "LEAD" thay vì tên chính xác
**Fix thêm:** Dùng `SpreadsheetApp.openById(SPREADSHEET_ID)` thay vì `getActiveSpreadsheet()`
**SPREADSHEET_ID đúng:** `1yMbrjedTKMu51aSBLLA6EWkJ5Yg_A4Q_kPfkkBc6uSo`

---

## BUG 6 — SĐT có khoảng trắng không được detect
**Triệu chứng:** Khách gõ "098 207 4838" → bot không nhận ra là SĐT → không ghi Sheet, không HOT LEAD
**Nguyên nhân:** Regex cũ `0\d{9}` chỉ bắt số liền nhau
**Fix:** Regex mới cho phép spaces/dashes: `0[\d\s\-\.]{9,13}` → strip → kiểm tra đúng 10 chữ số
**File:** `qnpa_agent.py` hàm `extract_lead_info()` dòng ~394

---

## BUG 7 — Trùng HOT LEAD Telegram + trùng dòng Google Sheet
**Triệu chứng:** Cùng 1 khách bị báo HOT LEAD 2-3 lần, sheet có 2-3 dòng trùng
**Nguyên nhân:** 2 Railway instances cùng xử lý 1 conv; AppScript không có dedup
**Fix:**
- `gsheet_claim_conv()`: atomic lock qua GSheet LockService (TTL 180s)
- AppScript `upsertLead`: tìm conv_key trước khi insert — chỉ update nếu đã có
- Railway Teardown mode: đảm bảo chỉ 1 instance chạy
- `claim_conv` exception → return True (fail open) vì Teardown = 1 instance

---

## QUY TẮC KHÔNG ĐƯỢC VI PHẠM KHI SỬA CODE

1. **Không reset `_replied_convs` khi conv lỗi** trừ khi lỗi rõ ràng là tạm thời (551)
2. **Không tăng `MAX_CLAUDE_CALLS_PER_CYCLE`** quá 5
3. **Không giảm `max_age`** xuống dưới 60 phút
4. **Không dùng `getActiveSpreadsheet()`** trong standalone AppScript — dùng `openById()`
5. **Chỉ gọi `gsheet_upsert_lead` khi `phone_detected`** — kiểm tra điều kiện tại dòng ~1030
6. **Model Claude:** `claude-haiku-4-5-20251001` — không đổi
7. **Khi sửa bất kỳ flow nào** → đọc file này trước để không phá fix cũ
