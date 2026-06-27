// QNPA Agent — Google Apps Script Webhook
// Deploy: Extensions → Apps Script → Deploy → New deployment → Web App → Execute as Me → Anyone
// Paste URL vào GSHEET_WEBHOOK trong qnpa_agent.py

const SPREADSHEET_ID    = "1yMbrjedTKMu51aSBLLA6EWkJ5Yg_A4Q_kPfkkBc6uSo";  // ID Google Sheet QNPA
const SHEET_NAME_LEADS  = "LEAD THÁNG 6";
const SHEET_NAME_LOCKS  = "_locks";       // sheet ẩn để lưu claim_conv + report marks
const COL_CONV_KEY      = 1;              // cột A = conv_key (ID duy nhất, không trùng)
const COL_CREATED       = 2;             // B = ngày tạo
const COL_TIME          = 3;             // C = giờ tạo
const COL_NAME          = 4;             // D = tên KH
const COL_STUDENT       = 5;            // E = học viên
const COL_AGE           = 6;             // F = tuổi
const COL_AREA          = 7;             // G = khu vực
const COL_PICKLEBALL    = 8;            // H = đã chơi PB chưa
const COL_PHONE         = 9;             // I = SĐT
const COL_SOURCE        = 10;            // J = nguồn
const COL_STATUS        = 11;           // K = tình trạng lead

function doPost(e) {
  try {
    const body = JSON.parse(e.postData.contents);
    const action = body.action || "upsert_lead";

    if (action === "claim_conv") {
      return jsonResponse(claimConv(body.lock_key, body.instance_id));
    }
    if (action === "check_report") {
      return jsonResponse(checkReport(body.report_key));
    }
    if (action === "mark_report") {
      markReport(body.report_key);
      return jsonResponse({ success: true });
    }
    if (action === "upsert_lead" || body.conv_key) {
      return jsonResponse(upsertLead(body));
    }

    return jsonResponse({ error: "unknown action", action });
  } catch (err) {
    return jsonResponse({ error: err.message });
  }
}

// ─── TÌM SHEET LEAD (tìm theo tên, fallback sang sheet đầu tiên không phải _locks) ──
function getLeadSheet(ss) {
  // Thử tên chính xác trước
  let sheet = ss.getSheetByName(SHEET_NAME_LEADS);
  if (sheet) return sheet;
  // Thử tìm sheet có tên chứa "LEAD" (không phân biệt hoa thường)
  const all = ss.getSheets();
  for (let i = 0; i < all.length; i++) {
    const n = all[i].getName().toUpperCase();
    if (n.indexOf("LEAD") >= 0 && n.indexOf("LOCK") < 0) return all[i];
  }
  return null;
}

// ─── UPSERT LEAD ───────────────────────────────────────────────
function upsertLead(data) {
  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    const ss     = SpreadsheetApp.openById(SPREADSHEET_ID);
    const sheet  = getLeadSheet(ss);
    if (!sheet) return { action: "error", reason: "sheet not found: " + SHEET_NAME_LEADS };

    const convKey = (data.conv_key || "").trim();
    if (!convKey) return { action: "error", reason: "missing conv_key" };

    const lastRow  = sheet.getLastRow();
    let existingRow = -1;

    // Tìm row có conv_key trùng (cột A)
    if (lastRow >= 2) {
      const keys = sheet.getRange(2, COL_CONV_KEY, lastRow - 1, 1).getValues();
      for (let i = 0; i < keys.length; i++) {
        if ((keys[i][0] || "").toString().trim() === convKey) {
          existingRow = i + 2; // 1-based, offset by header row
          break;
        }
      }
    }

    const vn      = new Date(new Date().getTime() + 7 * 3600 * 1000);
    const dateStr = Utilities.formatDate(vn, "GMT+7", "dd/MM/yyyy");
    const timeStr = Utilities.formatDate(vn, "GMT+7", "HH:mm");

    const rowData = [
      convKey,
      dateStr,
      timeStr,
      data.ten        || "",
      data.hoc_vien   || "",
      data.tuoi       || "",
      data.khu_vuc    || "",
      data.pickleball || "",
      data.sdt        || "",
      data.nguon      || "Facebook Fanpage",
      data.tinh_trang || "Mới tạo",
    ];

    // Nếu không tìm thấy theo conv_key → thử tìm theo SĐT (tránh insert trùng khi bot restart)
    if (existingRow < 0 && data.sdt && lastRow >= 2) {
      const phones = sheet.getRange(2, COL_PHONE, lastRow - 1, 1).getValues();
      const sdt = (data.sdt || "").toString().replace(/\D/g, "");
      for (let i = 0; i < phones.length; i++) {
        const existing_phone = (phones[i][0] || "").toString().replace(/\D/g, "");
        if (sdt && existing_phone === sdt) {
          existingRow = i + 2;
          break;
        }
      }
    }

    if (existingRow > 0) {
      // Cập nhật — chỉ ghi đè các trường không rỗng
      const existing = sheet.getRange(existingRow, COL_CONV_KEY, 1, rowData.length).getValues()[0];
      const merged   = existing.map((old, idx) => {
        const incoming = rowData[idx];
        // Giữ giá trị cũ nếu incoming rỗng, HOẶC cột là tình trạng (cho phép nhân viên đổi thủ công)
        if (idx === COL_STATUS - 1) return old || incoming; // giữ trạng thái nhân viên đặt
        return (incoming !== "" && incoming !== null && incoming !== undefined) ? incoming : old;
      });
      sheet.getRange(existingRow, COL_CONV_KEY, 1, merged.length).setValues([merged]);
      return { action: "updated", row: existingRow };
    } else {
      // Insert mới
      const targetRow = lastRow < 2 ? 2 : lastRow + 1;
      sheet.getRange(targetRow, COL_CONV_KEY, 1, rowData.length).setValues([rowData]);
      return { action: "inserted", row: targetRow };
    }
  } finally {
    lock.releaseLock();
  }
}

// ─── CLAIM CONV (atomic lock chống 2 instance xử lý cùng 1 conv) ──
function claimConv(lockKey, instanceId) {
  if (!lockKey) return { claimed: false, reason: "missing lock_key" };
  const lock = LockService.getScriptLock();
  lock.waitLock(8000);
  try {
    const ss    = SpreadsheetApp.openById(SPREADSHEET_ID);
    let sheet   = ss.getSheetByName(SHEET_NAME_LOCKS);
    if (!sheet) {
      sheet = ss.insertSheet(SHEET_NAME_LOCKS);
      sheet.hideSheet();
    }

    const now     = new Date();
    const lastRow = sheet.getLastRow();
    const TTL_MS  = 180 * 1000; // lock hết hạn sau 180 giây (3 phút) — đủ cho cả trường hợp Claude timeout 2 lần

    // Tìm existing lock cho key này
    if (lastRow >= 1) {
      const data = sheet.getRange(1, 1, lastRow, 3).getValues(); // [key, instance, timestamp]
      for (let i = 0; i < data.length; i++) {
        if (data[i][0] === lockKey) {
          const ts = new Date(data[i][2]);
          if ((now - ts) < TTL_MS) {
            // Lock còn hiệu lực — instance khác đang giữ
            if (data[i][1] === instanceId) return { claimed: true };  // chính mình
            return { claimed: false, held_by: data[i][1] };
          }
          // Lock hết hạn → ghi đè
          sheet.getRange(i + 1, 1, 1, 3).setValues([[lockKey, instanceId, now.toISOString()]]);
          return { claimed: true };
        }
      }
    }

    // Chưa có lock → tạo mới
    sheet.appendRow([lockKey, instanceId, now.toISOString()]);
    return { claimed: true };
  } finally {
    lock.releaseLock();
  }
}

// ─── REPORT DEDUP ──────────────────────────────────────────────
function checkReport(key) {
  if (!key) return { sent: false };
  const ss   = SpreadsheetApp.openById(SPREADSHEET_ID);
  let sheet  = ss.getSheetByName(SHEET_NAME_LOCKS);
  if (!sheet) return { sent: false };
  const lastRow = sheet.getLastRow();
  if (lastRow < 1) return { sent: false };
  const data = sheet.getRange(1, 1, lastRow, 1).getValues();
  for (let i = 0; i < data.length; i++) {
    if ((data[i][0] || "").toString() === key) return { sent: true };
  }
  return { sent: false };
}

function markReport(key) {
  if (!key) return;
  const ss   = SpreadsheetApp.openById(SPREADSHEET_ID);
  let sheet  = ss.getSheetByName(SHEET_NAME_LOCKS);
  if (!sheet) { sheet = ss.insertSheet(SHEET_NAME_LOCKS); sheet.hideSheet(); }
  sheet.appendRow([key, "report", new Date().toISOString()]);
}

// ─── HELPER ────────────────────────────────────────────────────
function jsonResponse(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
