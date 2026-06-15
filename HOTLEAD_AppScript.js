// QNPA Lead Logger — Google Apps Script v3.0
// Cột mới chuẩn 2026 — tự tạo sheet theo tháng
// Deploy: Extensions → Apps Script → paste → Save → Deploy as Web App → Anyone

var THANG_VI = ["","THÁNG 1","THÁNG 2","THÁNG 3","THÁNG 4","THÁNG 5",
                "THÁNG 6","THÁNG 7","THÁNG 8","THÁNG 9","THÁNG 10","THÁNG 11","THÁNG 12"];

var HEADERS = [
  "STT",                        // A  1
  "Ngày tạo Lead",              // B  2
  "Thời gian tạo Lead",         // C  3
  "Tên khách hàng",             // D  4
  "Số điện thoại",              // E  5
  "Tên học viên",               // F  6
  "Tuổi học viên",              // G  7
  "Khu vực",                    // H  8
  "Đã chơi Pickleball chưa?",   // I  9
  "Nguồn Lead",                 // J  10
  "Nhu cầu chính",              // K  11
  "Mức độ quan tâm",            // L  12
  "Tình trạng Lead",            // M  13
  "Ngày gọi lần 1",             // N  14
  "Kết quả gọi lần 1",          // O  15
  "Ngày gọi lần 2",             // P  16
  "Kết quả gọi lần 2",          // Q  17
  "Ngày gọi lần 3",             // R  18
  "Kết quả gọi lần 3",          // S  19
  "Ngày gọi lần 4",             // T  20
  "Kết quả gọi lần 4",          // U  21
  "Ngày gọi lần 5",             // V  22
  "Kết quả gọi lần 5",          // W  23
  "Người phụ trách",            // X  24
  "Ngày đăng ký học thử",       // Y  25
  "conv_key"                    // Z  26 — ẩn, dùng để upsert
];

// Số thứ tự cột — tham khảo khi cần
// A=1 STT, B=2 Ngày, C=3 Giờ, D=4 Tên, E=5 SĐT, F=6 HV, G=7 Tuổi
// H=8 KV, I=9 PB, J=10 Nguồn, K=11 NhuCầu, L=12 MứcĐộ, M=13 TT
// N-W=14-23 Gọi 1-5 + KQ, X=24 PhụTrách, Y=25 NgàyTest, Z=26 conv_key

var DROPDOWN = {
  PICKLEBALL  : ["Chưa từng", "Mới chơi", "Đang chơi"],
  NGUON       : ["Facebook Ads", "Fanpage", "Zalo/Hotline", "Giới thiệu", "Khác"],
  NHU_CAU     : ["Trại hè", "Khóa cơ bản", "Khóa nâng cao", "Học thử", "Chưa rõ"],
  MUC_DO      : ["🔥 Hot", "🌡 Warm", "❄ Cold"],
  TINH_TRANG  : ["Mới tạo","Đang tư vấn","Đã liên hệ","Hẹn học thử",
                 "Đã đăng ký","Không liên lạc được","Từ chối"]
};

// ── Lấy/tạo sheet tháng hiện tại ──────────────────────────────
function getMonthSheet() {
  var name = "LEAD " + THANG_VI[new Date().getMonth() + 1];
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sh = ss.getSheetByName(name);
  if (!sh) { sh = ss.insertSheet(name); setupHeaders(sh); }
  return sh;
}

function setupHeaders(sh) {
  var ncol = HEADERS.length;
  var hr   = sh.getRange(1, 1, 1, ncol);
  hr.setValues([HEADERS]);
  hr.setBackground("#1a73e8").setFontColor("#ffffff")
    .setFontWeight("bold").setFontSize(10)
    .setHorizontalAlignment("center").setVerticalAlignment("middle");
  sh.setFrozenRows(1);
  sh.setRowHeight(1, 40);

  // Độ rộng cột
  var widths = [40,90,90,150,110,130,70,110,140,120,130,110,150,
                90,180,90,180,90,180,90,180,90,180,130,110,1];
  for (var i = 0; i < widths.length; i++)
    sh.setColumnWidth(i + 1, widths[i]);

  // Dropdown 500 dòng
  var rows = 500;
  function dd(col, opts) {
    sh.getRange(2, col, rows, 1)
      .setDataValidation(SpreadsheetApp.newDataValidation()
        .requireValueInList(opts, true).setAllowInvalid(false).build());
  }
  dd(9,  DROPDOWN.PICKLEBALL);
  dd(10, DROPDOWN.NGUON);
  dd(11, DROPDOWN.NHU_CAU);
  dd(12, DROPDOWN.MUC_DO);
  dd(13, DROPDOWN.TINH_TRANG);

  // Banded rows
  try {
    sh.getBandedRanges().forEach(function(b) { b.remove(); });
    sh.getRange(2,1,rows,ncol).applyRowBanding(SpreadsheetApp.BandingTheme.LIGHT_GREY);
  } catch(e) {}
}

// ── Tìm dòng theo conv_key ────────────────────────────────────
function findRow(sh, ck) {
  var last = sh.getLastRow();
  if (last < 2 || !ck) return -1;
  var keys = sh.getRange(2, 26, last-1, 1).getValues();
  for (var i = 0; i < keys.length; i++)
    if (keys[i][0] === ck) return i + 2;
  return -1;
}

// ── Tính mức độ quan tâm tự động ─────────────────────────────
function autoMucDo(sdt, tuoi, khu_vuc, pickleball) {
  if (sdt) return "🔥 Hot";
  if (tuoi || khu_vuc || pickleball) return "🌡 Warm";
  return "❄ Cold";
}

// ── Report flag: tránh gửi báo cáo 2 lần khi Railway restart ──
function getConfigSheet() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sh = ss.getSheetByName("CONFIG");
  if (!sh) {
    sh = ss.insertSheet("CONFIG");
    sh.getRange(1,1).setValue("report_key");
    sh.getRange(1,2).setValue("sent_at");
    sh.hideSheet();
  }
  return sh;
}

function isReportSent(reportKey) {
  var sh = getConfigSheet();
  var data = sh.getDataRange().getValues();
  var today = Utilities.formatDate(new Date(), "Asia/Ho_Chi_Minh", "dd/MM/yyyy");
  for (var i = 0; i < data.length; i++) {
    if (data[i][0] === reportKey && data[i][1] === today) return true;
  }
  return false;
}

function markReportSent(reportKey) {
  var sh = getConfigSheet();
  var today = Utilities.formatDate(new Date(), "Asia/Ho_Chi_Minh", "dd/MM/yyyy");
  var data = sh.getDataRange().getValues();
  for (var i = 0; i < data.length; i++) {
    if (data[i][0] === reportKey) { sh.getRange(i+1, 2).setValue(today); return; }
  }
  sh.appendRow([reportKey, today]);
}

// ── Nhận dữ liệu từ Agent (POST) ─────────────────────────────
function doPost(e) {
  try {
    var d  = JSON.parse(e.postData.contents);

    // Xử lý report flag
    if (d.action === "check_report") {
      return ok({ sent: isReportSent(d.report_key) });
    }
    if (d.action === "mark_report") {
      markReportSent(d.report_key);
      return ok({ marked: true });
    }

    var sh = getMonthSheet();
    var ck = d.conv_key || "";
    var now    = new Date();
    var ngay   = Utilities.formatDate(now, "Asia/Ho_Chi_Minh", "dd/MM/yyyy");
    var gio    = Utilities.formatDate(now, "Asia/Ho_Chi_Minh", "HH:mm");
    var mucDo  = autoMucDo(d.sdt, d.tuoi, d.khu_vuc, d.pickleball);
    var exist  = findRow(sh, ck);

    // Cho phép override ngày/giờ (dùng khi upload thủ công dữ liệu cũ)
    if (d.ngay_override) ngay = d.ngay_override;
    if (d.gio_override)  gio  = d.gio_override;

    if (exist > 0) {
      var row = sh.getRange(exist, 1, 1, 26).getValues()[0];
      if (!row[3] && d.ten)        sh.getRange(exist, 4).setValue(d.ten);
      if (!row[4] && d.sdt) {
        sh.getRange(exist, 5).setValue(d.sdt).setFontWeight("bold").setFontColor("#c0392b");
        sh.getRange(exist, 13).setValue("Mới tạo");
      }
      if (!row[5] && d.hoc_vien)   sh.getRange(exist, 6).setValue(d.hoc_vien);
      if (!row[6] && d.tuoi)       sh.getRange(exist, 7).setValue(d.tuoi);
      if (!row[7] && d.khu_vuc)    sh.getRange(exist, 8).setValue(d.khu_vuc);
      if (!row[8] && d.pickleball) sh.getRange(exist, 9).setValue(d.pickleball);
      if (!row[9] && d.nguon)      sh.getRange(exist, 10).setValue(d.nguon);
      if (!row[10] && d.nhu_cau)   sh.getRange(exist, 11).setValue(d.nhu_cau);
      if (d.tinh_trang)            sh.getRange(exist, 13).setValue(d.tinh_trang);
      if (d.ngay_goi1)             sh.getRange(exist, 14).setValue(d.ngay_goi1);
      if (d.ghi_chu)               sh.getRange(exist, 15).setValue(d.ghi_chu);
      sh.getRange(exist, 12).setValue(mucDo);
      sh.getRange(exist, 3).setValue(gio);
      return ok({action:"updated", row:exist});

    } else {
      var stt    = sh.getLastRow();
      var status = d.tinh_trang || "Mới tạo";
      var row = [
        stt, ngay, gio,
        d.ten        || "",
        d.sdt        || "",
        d.hoc_vien   || "",
        d.tuoi       || "",
        d.khu_vuc    || "",
        d.pickleball || "",
        d.nguon      || "Fanpage",
        d.nhu_cau    || "Chưa rõ",
        mucDo,
        status,
        d.ngay_goi1||"", d.ghi_chu||"",  // Ngày gọi 1, Kết quả gọi 1
        "","","","","","","","", // Gọi 2-5
        "","",                   // Người phụ trách, Ngày test
        ck
      ];
      sh.appendRow(row);
      var nr = sh.getLastRow();
      formatRow(sh, nr, !!d.sdt);
      return ok({action:"inserted", row:nr});
    }
  } catch(err) {
    return fail(err.toString());
  }
}

function formatRow(sh, nr, hasPhone) {
  sh.setRowHeight(nr, 30);
  [1,2,3,7,12,13].forEach(function(c) {
    sh.getRange(nr, c).setHorizontalAlignment("center");
  });
  sh.getRange(nr, 13).setFontWeight("bold")
    .setBackground(hasPhone ? "#fff3cd" : "#f0f0f0");
  if (hasPhone) {
    sh.getRange(nr, 5).setFontWeight("bold").setFontColor("#c0392b");
    sh.getRange(nr, 12).setFontWeight("bold").setFontColor("#c0392b");
  }
}

function doGet(e)  { return ok({status:"QNPA webhook OK"}); }
function ok(d)     { return res(JSON.stringify(Object.assign({success:true},d))); }
function fail(msg) { return res(JSON.stringify({success:false,error:msg})); }
function res(t)    { return ContentService.createTextOutput(t).setMimeType(ContentService.MimeType.JSON); }

// ── Xóa tất cả dòng không có SĐT trong sheet tháng hiện tại ──
function deleteRowsWithoutPhone() {
  var sh   = getMonthSheet();
  var last = sh.getLastRow();
  if (last < 2) { SpreadsheetApp.getUi().alert("Sheet trống, không có gì để xóa."); return; }

  var sdtCol = sh.getRange(2, 5, last - 1, 1).getValues(); // cột E = SĐT
  var toDelete = [];
  for (var i = sdtCol.length - 1; i >= 0; i--) {
    if (!sdtCol[i][0] || sdtCol[i][0].toString().trim() === "") {
      toDelete.push(i + 2); // +2 vì bắt đầu từ dòng 2
    }
  }

  if (toDelete.length === 0) {
    SpreadsheetApp.getUi().alert("✅ Không có dòng nào thiếu SĐT. Sheet đã sạch!");
    return;
  }

  toDelete.forEach(function(r) { sh.deleteRow(r); });

  // Đánh lại STT
  var newLast = sh.getLastRow();
  for (var j = 2; j <= newLast; j++) {
    sh.getRange(j, 1).setValue(j - 1);
  }

  SpreadsheetApp.getUi().alert("✅ Đã xóa " + toDelete.length + " dòng không có SĐT!");
}

// ── Chạy 1 lần để tạo sheet tháng hiện tại ───────────────────
function initCurrentMonth() {
  getMonthSheet();
  SpreadsheetApp.getUi().alert("✅ Sheet LEAD " + THANG_VI[new Date().getMonth()+1] + " đã tạo thành công!");
}

// ── Test ghi dữ liệu thử ──────────────────────────────────────
function testInsert() {
  doPost({postData:{contents:JSON.stringify({
    conv_key   : "test_002",
    ten        : "Nguyễn Thị Hoa",
    sdt        : "0987654321",
    hoc_vien   : "Bé An",
    tuoi       : "8",
    khu_vuc    : "Hòn Gai",
    pickleball : "Chưa từng",
    nguon      : "Facebook Ads",
    nhu_cau    : "Trại hè"
  })}});
  SpreadsheetApp.getUi().alert("✅ Test xong — kiểm tra sheet LEAD THÁNG 6!");
}
