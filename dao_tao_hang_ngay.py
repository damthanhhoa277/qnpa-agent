# encoding: utf-8
"""
HỆ THỐNG ĐÀO TẠO HÀNG NGÀY — QNPA TOÀN BỘ MÁY
8 Phòng ban + Ban Lãnh đạo · CAS 8 tầng · 1 Người 1 Việc
Lịch: 7:30 bài học | 8:00 họp sáng | 12:00 check-in | 17:30 họp chiều | 20:00 báo cáo
"""
import sys, os, time, json, requests
from datetime import datetime, timezone, timedelta

sys.stdout.reconfigure(encoding="utf-8")

TELEGRAM_TOKEN = "8608503050:AAEax-HkoZWrWL2QVXP5DXJYhk1FShWd7Zw"
CHAT_PHONGBAN  = "-5436962310"   # QNPA NỘI BỘ PHÒNG BAN
CHAT_COACHING  = "-5017089871"   # Coaching CAS — báo cáo lên chị Hoa
CHAT_SALE      = "-5204359056"   # Sales team
VN             = timezone(timedelta(hours=7))

_STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dao_tao_state.json")

# ─────────────────────────────────────────────────────────────
# CHƯƠNG TRÌNH HỌC — 8 PHÒNG BAN + BAN LÃNH ĐẠO
# Mỗi module: (tên_bài, nội_dung)
# ─────────────────────────────────────────────────────────────
PHONG_BAN = {

    # ══════════════════════════════════════════════
    # BAN LÃNH ĐẠO — CEO + COO + CFO + Trợ Lý
    # ══════════════════════════════════════════════
    "lanh_dao": {
        "ten": "Ban Lãnh Đạo",
        "emoji": "👑",
        "thanh_vien": "Minh TGĐ · Lan COO · Kim CFO · Mai Trợ Lý",
        "chat": CHAT_PHONGBAN,
        "bai_hoc": [
            ("4DX — 4 Nguyên Tắc Thực Thi",
             "4 nguyên tắc thực thi tốt nhất:\n"
             "1️⃣ <b>WIG</b>: Chỉ 1 mục tiêu sống chết (tháng 7: 15 HV mới)\n"
             "2️⃣ <b>Lead Measures</b>: Đo việc làm, không đo kết quả\n"
             "   • Inbox/ngày, gọi/ngày, học thử/tuần\n"
             "3️⃣ <b>Scoreboard</b>: Bảng điểm hiển thị mọi người thấy\n"
             "4️⃣ <b>Accountability</b>: Họp 15 phút mỗi sáng\n\n"
             "✏️ BÀI TẬP: Xác định 1 Lead Measure quan trọng nhất của bộ phận mình."),

            ("OKR vs KPI — dùng đúng công cụ",
             "KPI = đo lường vận hành (inbox, CPL, tỷ lệ chốt)\n"
             "OKR = đặt mục tiêu đột phá (Objective + Key Results)\n\n"
             "QNPA tháng 7:\n"
             "• O: Tăng học viên mới lên 15 HV\n"
             "• KR1: Inbox/ngày ≥ 30\n"
             "• KR2: CPL < 120k\n"
             "• KR3: Tỷ lệ học thử → chốt ≥ 35%\n\n"
             "✏️ BÀI TẬP: Kiểm tra 3 KR trên — hiện đang ở đâu?"),

            ("Delegation — giao việc đúng cách",
             "5 cấp độ giao việc:\n"
             "1. Làm theo hướng dẫn (người mới)\n"
             "2. Đề xuất rồi làm (đang học)\n"
             "3. Làm rồi báo cáo (đã thạo)\n"
             "4. Làm — báo nếu có vấn đề (tin tưởng)\n"
             "5. Tự quyết toàn bộ (chuyên gia)\n\n"
             "✏️ BÀI TẬP: Đánh giá từng nhân sự đang ở cấp độ mấy."),

            ("Họp hiệu quả — tránh lãng phí thời gian",
             "Họp tốt = 3 yếu tố:\n"
             "• Mục tiêu rõ trước khi họp\n"
             "• Chỉ người có liên quan tham gia\n"
             "• Kết thúc = Action items + Owner + Deadline\n\n"
             "Loại bỏ:\n"
             "❌ Họp để 'update' — gửi text thay thế\n"
             "❌ Họp không có agenda\n"
             "❌ Họp quá 30 phút không có quyết định\n\n"
             "✏️ BÀI TẬP: Review họp sáng hôm nay — đạt 3 tiêu chí không?"),

            ("Báo cáo nhanh — Scoreboard mỗi sáng",
             "Scoreboard QNPA — cập nhật 7h mỗi ngày:\n"
             "📊 Inbox hôm qua: ___\n"
             "📞 Gọi lead: ___\n"
             "🎓 Học thử tuần này: ___\n"
             "💰 Chốt tuần này: ___\n"
             "📈 Trend so hôm qua: 🟢/🟡/🔴\n\n"
             "✏️ BÀI TẬP: Điền đủ số hôm nay và gửi vào nhóm."),

            ("Quản lý tài chính — P&L đơn giản",
             "P&L cơ bản mỗi tháng:\n"
             "• Doanh thu: học phí + phụ kiện\n"
             "• Chi phí cố định: lương, thuê sân, điện\n"
             "• Chi phí biến đổi: Ads, vật tư, sự kiện\n"
             "• LNST = DT - CF cố định - CF biến đổi\n\n"
             "Break-even QNPA: ~65-70 HV (doanh thu ~130-140tr)\n\n"
             "✏️ BÀI TẬP: Lan báo số doanh thu tháng 6 thực tế vào nhóm."),

            ("Văn hóa tổ chức — xây từ ngày đầu",
             "3 yếu tố văn hóa QNPA:\n"
             "1️⃣ <b>Cam kết và làm</b>: Nói gì làm nấy — không phải 'để anh xem'\n"
             "2️⃣ <b>Số liệu thật</b>: Báo đúng thực tế — xấu cũng báo, không đẹp số\n"
             "3️⃣ <b>Học mỗi ngày</b>: Tham gia bài học = cam kết phát triển\n\n"
             "✏️ BÀI TẬP: Kể 1 câu chuyện của tuần này thể hiện văn hóa tốt."),
        ]
    },

    # ══════════════════════════════════════════════
    # PHÒNG 1 — NGHIÊN CỨU KHÁCH HÀNG (Tầng 1)
    # Trưởng phòng: AN · NV: CHI (ICP), BÌNH (Keywords)
    # ══════════════════════════════════════════════
    "phong1_nghien_cuu": {
        "ten": "P1 · Nghiên Cứu Khách Hàng",
        "emoji": "🔍",
        "thanh_vien": "An (Trưởng) · Chi · Bình",
        "chat": CHAT_PHONGBAN,
        "bai_hoc": [
            ("ICP — Chân Dung Khách Hàng Lý Tưởng",
             "ICP QNPA hiện tại:\n"
             "• Mẹ 28-42 tuổi, con 6-15 tuổi\n"
             "• Ở Hạ Long / Cẩm Phả / Uông Bí\n"
             "• Thu nhập gia đình 20-50tr/tháng\n"
             "• Quan tâm: vận động, kỹ năng xã hội, an toàn\n"
             "• Nỗi sợ: con ít vận động, nghiện điện thoại, nhút nhát\n\n"
             "✏️ BÀI TẬP Chi: Phỏng vấn 2 phụ huynh hiện tại — hỏi vì sao họ chọn QNPA."),

            ("100 Từ Khóa Mục Tiêu — ưu tiên chuyển đổi",
             "Phân loại từ khóa theo ý định:\n"
             "🔥 Mua ngay: 'trại hè pickleball Hạ Long', 'học pickleball trẻ em QN'\n"
             "🤔 Cân nhắc: 'pickleball cho bé', 'lợi ích pickleball trẻ em'\n"
             "📚 Tìm hiểu: 'pickleball là gì', 'cách chơi pickleball'\n\n"
             "✏️ BÀI TẬP Bình: Dùng Google Keyword Planner tìm 20 từ khóa 'Mua ngay' cho QNPA."),

            ("Customer Journey — hành trình khách hàng",
             "5 giai đoạn hành trình:\n"
             "1. Chưa biết → Thấy Ads/content\n"
             "2. Biết → Xem profile, đọc bài\n"
             "3. Quan tâm → Inbox hỏi\n"
             "4. Cân nhắc → Học thử miễn phí\n"
             "5. Mua → Đăng ký, thanh toán\n\n"
             "✏️ BÀI TẬP An: Vẽ hành trình và ghi điểm ma sát (friction) ở mỗi bước."),

            ("Phân tích đối thủ — điểm mạnh/yếu",
             "Đối thủ QNPA tại QN:\n"
             "• Sân pickleball tự phát (dạy ad-hoc)\n"
             "• CLB thể thao đa năng\n"
             "• Không có học viện chuyên pickleball trẻ em\n\n"
             "Điểm khác biệt QNPA:\n"
             "• Chuyên biệt cho trẻ em\n"
             "• Chương trình có lộ trình rõ ràng\n"
             "• Cộng đồng phụ huynh\n\n"
             "✏️ BÀI TẬP: Research 3 sân/CLB ở Hạ Long và điền vào bảng so sánh."),

            ("Voice of Customer — lắng nghe khách nói gì",
             "3 nguồn VOC:\n"
             "1. Comment/inbox trên Fanpage\n"
             "2. Câu hỏi phụ huynh hỏi trực tiếp\n"
             "3. Lý do từ chối của lead\n\n"
             "Dùng VOC để:\n"
             "• Viết caption dùng ngôn ngữ của họ\n"
             "• Tạo FAQ trả lời đúng nỗi lo\n"
             "• Cải thiện sản phẩm\n\n"
             "✏️ BÀI TẬP: Đọc 20 inbox gần nhất — note 5 câu phụ huynh hay hỏi nhất."),
        ]
    },

    # ══════════════════════════════════════════════
    # PHÒNG 2 — CONTENT & TRAFFIC (Tầng 2)
    # Trưởng: NGỌC · 7 NV: Cường(YT), Dung(FB), Diễm(TT), Phương(IG), Giang(Threads), Hiền(Group), Ích(Blog)
    # ══════════════════════════════════════════════
    "phong2_content": {
        "ten": "P2 · Content & Traffic",
        "emoji": "🎬",
        "thanh_vien": "Ngọc (Trưởng) · Cường · Dung · Diễm · Phương · Giang · Hiền · Ích",
        "chat": CHAT_PHONGBAN,
        "bai_hoc": [
            ("Hook 3 giây — quyết định mọi thứ",
             "3 loại hook hiệu quả nhất:\n"
             "1️⃣ <b>Pain hook</b>: 'Con bạn có đang nghiện điện thoại không?'\n"
             "2️⃣ <b>Curiosity hook</b>: 'Tại sao 47 bé Hạ Long chọn môn này hè 2026?'\n"
             "3️⃣ <b>Result hook</b>: 'Sau 4 tuần, bé từ nhút nhát thành tự tin'\n\n"
             "Rule: 3 giây đầu video = 80% quyết định người xem có ở lại\n\n"
             "✏️ BÀI TẬP: Mỗi người viết 1 hook phù hợp kênh mình quản lý."),

            ("Content Pillar — 3 trụ cột nội dung QNPA",
             "Trụ 1 — GIÁO DỤC (40%):\n"
             "• Lợi ích pickleball với trẻ em\n"
             "• Kỹ thuật cơ bản, quy tắc thi đấu\n\n"
             "Trụ 2 — CHỨNG MINH (40%):\n"
             "• Clip bé tập thật\n"
             "• Testimonial phụ huynh\n"
             "• Kết quả trước/sau\n\n"
             "Trụ 3 — CỘNG ĐỒNG (20%):\n"
             "• Sự kiện, giải đấu\n"
             "• Behind the scenes\n\n"
             "✏️ BÀI TẬP: Kiểm tra 10 bài gần nhất — phân bổ 3 trụ đang cân không?"),

            ("Script video 60 giây chuẩn QNPA",
             "Cấu trúc:\n"
             "• 0-3s: Hook\n"
             "• 3-15s: Problem (con ít vận động, nhút nhát)\n"
             "• 15-40s: Solution (QNPA dạy như thế nào)\n"
             "• 40-55s: Proof (clip thật, testimonial)\n"
             "• 55-60s: CTA (Inbox học thử miễn phí)\n\n"
             "✏️ BÀI TẬP: Ngọc tạo 1 script mẫu cho cả team dùng chung."),

            ("Storytelling — kể chuyện bán hàng",
             "Công thức: Trước → Biến cố → Sau\n"
             "• Trước: 'Con Nam 8 tuổi, suốt ngày ở nhà xem điện thoại'\n"
             "• Biến cố: 'Tuần đầu học QNPA, Nam sợ, không dám đánh'\n"
             "• Sau: 'Tuần 3, tự kéo mẹ đến sân trước giờ học 30 phút'\n\n"
             "Nguyên tắc: Phụ huynh mua CẢM XÚC, không mua tính năng\n\n"
             "✏️ BÀI TẬP: Phỏng vấn 1 phụ huynh theo công thức này, viết thành caption."),

            ("Lịch đăng content — không đăng tự phát",
             "Content Calendar chuẩn:\n"
             "• T2: Bài giáo dục (tip kỹ thuật)\n"
             "• T3: Clip buổi tập\n"
             "• T4: Testimonial phụ huynh\n"
             "• T5: Behind the scenes / story\n"
             "• T6: Giới thiệu khóa học / CTA\n"
             "• T7-CN: Sự kiện / giải đấu / cộng đồng\n\n"
             "✏️ BÀI TẬP: Điền lịch tuần tới theo template và share vào nhóm."),

            ("SEO Facebook & TikTok — reach organic",
             "Facebook SEO:\n"
             "• Từ khóa trong caption: 'pickleball trẻ em Hạ Long'\n"
             "• Alt text ảnh đầy đủ\n"
             "• Đăng đúng giờ: 7-9h, 11-13h, 19-21h\n\n"
             "TikTok SEO:\n"
             "• Nói từ khóa trong video (AI nghe)\n"
             "• Caption + hashtag có từ khóa\n"
             "• #pickleballvietnam #treemhalo\n\n"
             "✏️ BÀI TẬP: Cập nhật caption 3 bài gần nhất theo chuẩn SEO."),

            ("Tổng kết tuần — đo lường content",
             "Chỉ số cần theo dõi:\n"
             "• Reach/Impressions — bao nhiêu người thấy\n"
             "• Engagement rate — tương tác/reach\n"
             "• Profile visit — quan tâm tới trang\n"
             "• Link click / Inbox từ content\n\n"
             "Kết luận đúng cách:\n"
             "❌ 'Bài này đẹp' → ✅ 'Bài này reach 5000, ER 8%, tạo 3 inbox'\n\n"
             "✏️ BÀI TẬP: Ngọc tổng hợp top 3 bài hiệu quả nhất tuần này."),
        ]
    },

    # ══════════════════════════════════════════════
    # PHÒNG 3 — THU LEAD (Tầng 3)
    # Trưởng: BÌNH · NV: Khải (Lead Magnet), Long (Squeeze Page)
    # ══════════════════════════════════════════════
    "phong3_thu_lead": {
        "ten": "P3 · Thu Lead",
        "emoji": "🧲",
        "thanh_vien": "Bình (Trưởng) · Khải · Long",
        "chat": CHAT_PHONGBAN,
        "bai_hoc": [
            ("Lead Magnet — mồi câu số điện thoại",
             "Lead magnet tốt nhất cho phụ huynh:\n"
             "🎁 Checklist: '10 dấu hiệu con cần vận động nhiều hơn'\n"
             "🎁 Video: 'Buổi học thử pickleball miễn phí'\n"
             "🎁 Ebook: 'Hướng dẫn chọn môn thể thao cho bé 6-15 tuổi'\n\n"
             "Nguyên tắc: Lead magnet phải liên quan trực tiếp đến quyết định MUA\n\n"
             "✏️ BÀI TẬP Khải: Thiết kế 1 checklist PDF đơn giản cho QNPA."),

            ("Squeeze Page — landing page thu SĐT",
             "Squeeze page hiệu quả:\n"
             "• 1 tiêu đề rõ benefit\n"
             "• 3-5 bullet points lợi ích\n"
             "• Form chỉ hỏi Tên + SĐT\n"
             "• CTA button nổi bật\n"
             "• Không có menu, không có link thoát\n\n"
             "✏️ BÀI TẬP Long: Mock-up 1 squeeze page cho 'Học thử miễn phí'."),

            ("Tỷ lệ chuyển đổi Lead — đọc số đúng",
             "Funnel thu lead:\n"
             "Reach → Click → Form điền → Lead xác nhận\n\n"
             "Benchmark:\n"
             "• Click/Reach: 2-5% là tốt\n"
             "• Lead/Click: 20-40% là tốt\n"
             "• CPL < 120k là OK\n\n"
             "✏️ BÀI TẬP Bình: Tính tỷ lệ chuyển đổi thực tế tuần này."),

            ("Phân loại Lead — nóng/ấm/lạnh",
             "🔥 Lead nóng: Hỏi giá, hỏi lịch → Telesale trong 30 phút\n"
             "🌡️ Lead ấm: Quan tâm nhưng chưa hỏi cụ thể → Nuôi dưỡng 7 ngày\n"
             "❄️ Lead lạnh: Inbox nhưng im lặng → Sequence email/Zalo\n\n"
             "✏️ BÀI TẬP: Phân loại 20 lead gần nhất vào 3 nhóm."),
        ]
    },

    # ══════════════════════════════════════════════
    # PHÒNG 4 — NUÔI DƯỠNG LEAD (Tầng 4)
    # Trưởng: LINH Agent · NV: My (Sequence), Linh (Chatbot)
    # ══════════════════════════════════════════════
    "phong4_nuoi_duong": {
        "ten": "P4 · Nuôi Dưỡng Lead",
        "emoji": "🤖",
        "thanh_vien": "Linh Agent (Trưởng) · My · Linh",
        "chat": CHAT_PHONGBAN,
        "bai_hoc": [
            ("Sequence 7 tin — tự động nuôi dưỡng",
             "7 tin nhắn sau khi khách inbox lần đầu:\n"
             "• Ngay lập tức: Xác nhận + câu hỏi (Linh agent)\n"
             "• Ngày 1: Clip buổi học thực tế\n"
             "• Ngày 2: Testimonial phụ huynh\n"
             "• Ngày 3: FAQ (giá, lịch học, địa chỉ)\n"
             "• Ngày 5: Ưu đãi học thử miễn phí\n"
             "• Ngày 7: Urgency (slot còn lại)\n"
             "• Ngày 10: Lần cuối follow-up\n\n"
             "✏️ BÀI TẬP My: Viết đủ 7 tin nhắn template."),

            ("Chatbot Pancake — cấu hình đúng",
             "Linh Agent phải:\n"
             "✅ Trả lời inbox < 5 phút\n"
             "✅ Phát hiện số điện thoại → báo HOTLEAD\n"
             "✅ Không gửi tin nhắn trùng\n"
             "✅ Trả lời cả comment Facebook\n\n"
             "Kiểm tra mỗi sáng:\n"
             "• Agent log có lỗi không?\n"
             "• Inbox nào chưa được trả lời?\n\n"
             "✏️ BÀI TẬP Linh: Báo cáo số inbox đã trả lời hôm qua."),

            ("Tái kích hoạt lead im lặng",
             "Lead im lặng > 7 ngày:\n"
             "Cách tái kích hoạt:\n"
             "1. Gửi nội dung mới (clip, ưu đãi)\n"
             "2. Hỏi thẳng: 'Bé nhà mình đã sẵn sàng thử chưa ạ?'\n"
             "3. Urgency thật: 'Tháng 7 còn X slot'\n"
             "4. Nếu không phản hồi sau 3 lần → archive\n\n"
             "✏️ BÀI TẬP: Liệt kê tất cả lead im lặng > 7 ngày, lên plan tái kích hoạt."),

            ("CRM đơn giản — quản lý trên Google Sheet",
             "Cột cần có trong Sheet Lead:\n"
             "Tên | SĐT | Ngày inbox | Trạng thái | Lần liên hệ cuối | Ghi chú\n\n"
             "Trạng thái: Mới / Đang nuôi / Học thử / Chốt / Từ chối\n\n"
             "✏️ BÀI TẬP My: Cập nhật trạng thái toàn bộ lead tháng 6 vào Sheet."),
        ]
    },

    # ══════════════════════════════════════════════
    # PHÒNG 5 — KINH DOANH & BÁN HÀNG (Tầng 5)
    # Trưởng: HÙNG · NV: Quân (Telesale), Sơn (Upsell), Uy (TMĐT)
    # ══════════════════════════════════════════════
    "phong5_kinh_doanh": {
        "ten": "P5 · Kinh Doanh & Bán Hàng",
        "emoji": "💰",
        "thanh_vien": "Hùng (Trưởng) · Quân · Sơn · Uy",
        "chat": CHAT_SALE,
        "bai_hoc": [
            ("Kịch bản telesale — 60 giây đầu",
             "60 giây đầu quyết định khách có nghe tiếp không:\n\n"
             "'Dạ chào chị [tên], em Hùng QNPA ạ. Hôm trước chị hỏi Trại hè Pickleball đúng không ạ? "
             "Em gọi để chia sẻ thêm và giúp chị chọn lịch. Chị đang rảnh không ạ?'\n\n"
             "Nguyên tắc:\n"
             "✅ Gọi tên khách\n✅ Nhắc lý do họ quan tâm\n✅ Xin phép nói\n✅ KHÔNG chào hàng ngay\n\n"
             "✏️ BÀI TẬP Quân: Luyện script 5 lần trước khi gọi thật."),

            ("5 câu từ chối — xử lý chuẩn",
             "1. 'Để tôi nghĩ đã' → 'Chị băn khoăn điều gì nhất, em giải thích ngay?'\n"
             "2. 'Giá cao quá' → 'Bên em có buổi thử miễn phí, chị cho bé thử trước nhé?'\n"
             "3. 'Bé chưa hứng' → 'Bé nào cũng vậy. Tuần 2 tự kéo mẹ đi. Thử 1 buổi thôi ạ?'\n"
             "4. 'Bận lắm' → 'Lịch linh hoạt T2-T6. Chị chọn buổi nào tiện nhất?'\n"
             "5. 'Hỏi chồng đã' → 'Em gửi thông tin để anh chị cùng xem. Cho em Zalo nhé?'\n\n"
             "✏️ BÀI TẬP: Thuộc 5 câu này — test với Hùng trưởng phòng."),

            ("Upsell — nâng giá trị đơn hàng",
             "Upsell đúng lúc: SAU khi khách đồng ý, TRƯỚC khi thanh toán\n\n"
             "'Chị đăng ký Cơ bản 20 buổi rồi ạ! Bên em có CLB cuối tuần 300k/tháng, bé được giao lưu thêm. "
             "Nhiều phụ huynh đăng ký cả 2 luôn. Chị muốn đăng ký luôn không ạ?'\n\n"
             "Nguyên tắc: Chỉ upsell 1 sản phẩm · Gắn lợi ích cụ thể · Hỏi — không ép\n\n"
             "✏️ BÀI TẬP Sơn: Viết kịch bản upsell Trại hè → Cơ bản."),

            ("Urgency thật — chốt đơn nhanh",
             "Urgency THẬT (không bịa):\n"
             "• 'Lớp còn 3 chỗ, đăng ký sớm giữ chỗ nhé'\n"
             "• 'Ưu đãi tháng 6 hết [ngày], sau tăng giá'\n"
             "• 'Lịch đó đang có 2 bé hỏi, giữ 24h nhé'\n\n"
             "Urgency GIẢ → phụ huynh biết ngay → mất tin tưởng hoàn toàn\n\n"
             "✏️ BÀI TẬP: Liệt kê 3 urgency THẬT của QNPA tháng 7."),

            ("Follow-up — không bị ghét",
             "Timeline follow-up chuẩn:\n"
             "• Ngày 1: Gọi giới thiệu\n"
             "• Ngày 3: Nhắn Zalo (gửi clip bé học)\n"
             "• Ngày 7: Gọi lại ('Hỏi thăm bé sẵn sàng chưa?')\n"
             "• Ngày 14: Nhắn ưu đãi\n"
             "• Ngày 21: Lần cuối\n\n"
             "Mỗi lần follow-up = GIÁ TRỊ MỚI (clip mới, ưu đãi mới)\n\n"
             "✏️ BÀI TẬP Hùng: Setup lịch follow-up cho 21 HV tháng 6."),

            ("Sàn TMĐT — Shopee & TikTok Shop",
             "TikTok Shop QNPA:\n"
             "• Sản phẩm: Paddle, bóng, phụ kiện pickleball cho trẻ\n"
             "• Link video → sản phẩm (affiliate tự doanh)\n"
             "• Kết hợp Live bán hàng cuối tuần\n\n"
             "Shopee:\n"
             "• Tối ưu title: 'Vợt pickleball trẻ em size nhỏ nhẹ'\n"
             "• Ảnh chuẩn: bé cầm vợt thật\n\n"
             "✏️ BÀI TẬP Uy: Tạo 1 sản phẩm mẫu trên TikTok Shop."),
        ]
    },

    # ══════════════════════════════════════════════
    # PHÒNG 6 — TĂNG TRƯỞNG & ADS (Tầng 6)
    # Trưởng: HẢI · NV: Oanh (SEO), Phúc (Ads)
    # ══════════════════════════════════════════════
    "phong6_tang_truong": {
        "ten": "P6 · Tăng Trưởng & Ads",
        "emoji": "📣",
        "thanh_vien": "Hải (Trưởng) · Oanh · Phúc",
        "chat": CHAT_PHONGBAN,
        "bai_hoc": [
            ("Hook Formula — 3 loại hook Ads",
             "3 loại hook hiệu quả cho Ads phụ huynh:\n"
             "1️⃣ Pain: 'Con bạn có đang nghiện điện thoại không?'\n"
             "2️⃣ Curiosity: 'Tại sao 47 bé Hạ Long chọn môn này hè này?'\n"
             "3️⃣ Result: 'Sau 1 tháng, bé từ nhút nhát thành tự tin'\n\n"
             "✏️ BÀI TẬP: Viết 3 hook mới (mỗi loại 1 cái) cho Ads tháng 7."),

            ("CPL — đo đúng và tối ưu",
             "CPL = Tổng Ads / Số lead inbox\n"
             "QNPA tháng 6: ~195k → Mục tiêu tháng 7: <120k\n\n"
             "Giảm CPL bằng cách:\n"
             "1. Hook mạnh → CTR tăng → CPL giảm\n"
             "2. Audience chuẩn (mẹ 28-42, Hạ Long/Cẩm Phả)\n"
             "3. Tắt adset CPL > 200k sau 3 ngày\n\n"
             "✏️ BÀI TẬP Phúc: Tính CPL thực tế hôm nay và báo nhóm."),

            ("A/B Test — đúng cách",
             "CHỈ thay đổi 1 biến mỗi lần:\n"
             "• Test A: Hook pain vs Hook result (giữ nguyên ảnh)\n"
             "• Test B: Ảnh bé tập vs Ảnh phụ huynh + bé (giữ nguyên copy)\n\n"
             "Nguyên tắc:\n"
             "• Budget = nhau mỗi adset\n"
             "• Chạy tối thiểu 3 ngày\n"
             "• Scale khi CPL ổn định 2 ngày liên tiếp\n\n"
             "✏️ BÀI TẬP Hải: Thiết kế 1 bài A/B test cho tuần tới."),

            ("Creative mệt — nhận biết và thay",
             "Dấu hiệu creative mệt:\n"
             "• CTR giảm >30% so tuần đầu\n"
             "• CPL tăng >50%\n"
             "• Frequency > 3\n\n"
             "Quy trình thay creative:\n"
             "1. Giữ nguyên audience → đổi ảnh/video\n"
             "2. Thêm social proof (testimonial mới)\n"
             "3. Test hook mới\n\n"
             "✏️ BÀI TẬP: Kiểm tra creative đang chạy — có bị mệt không?"),

            ("SEO Local — Google Maps & GBP",
             "Google Business Profile QNPA:\n"
             "• Cập nhật đầy đủ: tên, địa chỉ, giờ mở cửa\n"
             "• Đăng ảnh/video mỗi tuần\n"
             "• Reply tất cả review (kể cả review xấu)\n"
             "• Post về sự kiện/ưu đãi\n\n"
             "Từ khóa local:\n"
             "'học pickleball Hạ Long', 'trại hè thể thao Quảng Ninh'\n\n"
             "✏️ BÀI TẬP Oanh: Kiểm tra GBP QNPA — thiếu gì bổ sung ngay."),

            ("Testimonial Ads — vũ khí số 1",
             "Ads có testimonial thật: CPL thấp hơn 40%\n"
             "Phụ huynh tin lời phụ huynh khác hơn quảng cáo\n\n"
             "Cách dùng testimonial trong Ads:\n"
             "• Video phụ huynh nói (15-30 giây)\n"
             "• Screenshot Zalo thật\n"
             "• Tên + ảnh thật (đã xin phép)\n\n"
             "✏️ BÀI TẬP: Phối hợp Hùng lấy 2 testimonial từ HV tháng 6 để chạy Ads."),
        ]
    },

    # ══════════════════════════════════════════════
    # PHÒNG 7 — HỆ THỐNG HÓA (Tầng 7)
    # Trưởng: TUẤN · NV: Vinh (SOP)
    # ══════════════════════════════════════════════
    "phong7_he_thong": {
        "ten": "P7 · Hệ Thống & SOP",
        "emoji": "⚙️",
        "thanh_vien": "Tuấn (Trưởng) · Vinh",
        "chat": CHAT_PHONGBAN,
        "bai_hoc": [
            ("SOP là gì — tại sao phải viết",
             "SOP = Standard Operating Procedure\n"
             "= Quy trình chuẩn để BẤT KỲ AI cũng làm được đúng\n\n"
             "QNPA cần 5 SOP lõi:\n"
             "1. SOP Inbox → Học thử (Linh agent)\n"
             "2. SOP Học thử → Đăng ký\n"
             "3. SOP Onboarding học viên mới\n"
             "4. SOP Đăng content hàng ngày\n"
             "5. SOP Báo cáo KPI hàng sáng\n\n"
             "✏️ BÀI TẬP Vinh: Chọn 1 SOP và bắt đầu viết phác thảo."),

            ("Customer Flow — hành trình trong hệ thống",
             "Vẽ flow từ khi khách biết đến QNPA:\n"
             "Thấy Ads → Inbox → Linh trả lời → HOTLEAD → Hùng gọi\n"
             "→ Học thử → Đăng ký → Onboarding → Học → Upsell → Review\n\n"
             "Tại mỗi bước:\n"
             "• Ai làm?\n"
             "• Làm gì?\n"
             "• Bao lâu?\n"
             "• Thước đo thành công?\n\n"
             "✏️ BÀI TẬP: Vẽ flow đầy đủ và đánh dấu điểm ma sát."),

            ("Automation — tự động hóa công việc lặp lại",
             "3 loại automation QNPA đang có:\n"
             "1. Linh Agent → trả lời inbox tự động\n"
             "2. AppScript → ghi lead vào GSheet tự động\n"
             "3. Dao tao hang ngay → bài học tự động 7:30\n\n"
             "Tiếp theo cần automation:\n"
             "• Sequence follow-up (Zalo OA)\n"
             "• Báo cáo KPI tự động lấy từ GSheet\n\n"
             "✏️ BÀI TẬP Tuấn: Liệt kê 3 việc lặp lại nhất đang làm thủ công."),

            ("Onboarding học viên — ấn tượng đầu tiên",
             "Onboarding checklist:\n"
             "✅ Zalo chào mừng trong 24h\n"
             "✅ Gửi lịch học + địa chỉ\n"
             "✅ Gửi guide 'Chuẩn bị cho buổi học đầu tiên'\n"
             "✅ Add vào group Zalo phụ huynh\n"
             "✅ Sau buổi 1: Nhắn hỏi thăm\n\n"
             "✏️ BÀI TẬP: Viết SOP Onboarding học viên mới đầy đủ."),
        ]
    },

    # ══════════════════════════════════════════════
    # PHÒNG 8 — ĐO LƯỜNG & BÁO CÁO (Tầng 8)
    # Trưởng: XUÂN · NV: Lan (Analytics)
    # ══════════════════════════════════════════════
    "phong8_do_luong": {
        "ten": "P8 · Đo Lường & Báo Cáo",
        "emoji": "📈",
        "thanh_vien": "Xuân (Trưởng) · Lan",
        "chat": CHAT_PHONGBAN,
        "bai_hoc": [
            ("5 KPI sống chết QNPA",
             "5 KPI phải báo mỗi sáng:\n"
             "1. 📥 Inbox/ngày → target ≥30\n"
             "2. 📞 Lead có SĐT/ngày → target ≥5\n"
             "3. 🎓 Học thử/tuần → target ≥10\n"
             "4. 💰 Chốt/tuần → target ≥5\n"
             "5. 💵 CPL → target <120k\n\n"
             "Màu: 🟢 Đạt · 🟡 Cần chú ý · 🔴 Nguy hiểm\n\n"
             "✏️ BÀI TẬP Lan: Điền đủ 5 KPI ngày hôm nay và gửi 7h sáng."),

            ("Báo cáo ngắn — đủ ý, không dài dòng",
             "Template báo cáo sáng:\n\n"
             "📊 BÁO CÁO [ngày]\n"
             "• Inbox hôm qua: [số] ([🟢/🟡/🔴] target 30)\n"
             "• Lead SĐT: [số]\n"
             "• Học thử tuần: [số]\n"
             "• Chốt tuần: [số]\n"
             "• CPL: [số]k\n"
             "🔴 Cần xử lý: [vấn đề nếu có]\n\n"
             "✏️ BÀI TẬP: Gửi báo cáo theo template này sáng mai 7h đúng."),

            ("5 WHY — tìm nguyên nhân gốc rễ",
             "Khi KPI đỏ → hỏi 5 WHY:\n\n"
             "Ví dụ: Inbox giảm từ 10 xuống 6\n"
             "• Why 1: Tại sao inbox giảm? → Ads reach ít\n"
             "• Why 2: Reach ít vì sao? → Budget hết sớm\n"
             "• Why 3: Budget hết vì sao? → 1 adset ăn hết\n"
             "• Why 4: Adset đó tốn vì sao? → Creative mệt, CPM tăng\n"
             "• Why 5: Sao không dừng? → Chưa setup alert\n\n"
             "Fix gốc rễ: Setup alert CPL > 200k\n\n"
             "✏️ BÀI TẬP: Áp dụng 5 WHY cho 1 KPI đang đỏ."),

            ("Dashboard — bảng điểm nhìn là biết",
             "GSheet Dashboard QNPA:\n"
             "• Tab 1: KPI hàng ngày (nhập số mỗi sáng)\n"
             "• Tab 2: Biểu đồ trend 30 ngày\n"
             "• Tab 3: Lead funnel (Inbox → Học thử → Chốt)\n"
             "• Tab 4: Ads performance (CPL, ROAS)\n\n"
             "Ai nhìn: Chị Hoa (quyết định), Minh TGĐ (điều phối)\n\n"
             "✏️ BÀI TẬP Xuân: Tạo 1 GSheet Dashboard cơ bản 4 tab này."),

            ("Phân tích xu hướng — nhìn xa hơn hôm nay",
             "Đừng chỉ nhìn số ngày hôm nay — nhìn xu hướng 7-30 ngày:\n\n"
             "• Inbox trend: tăng/giảm/flat?\n"
             "• CPL trend: tối ưu hay đang xấu dần?\n"
             "• Conversion rate: cải thiện hay tệ hơn?\n\n"
             "Công cụ: Google Sheets + biểu đồ đường (line chart)\n\n"
             "✏️ BÀI TẬP: Vẽ biểu đồ inbox 30 ngày qua và nhận xét xu hướng."),
        ]
    },

    # ══════════════════════════════════════════════
    # PHÒNG TÀI CHÍNH KẾ TOÁN
    # Trưởng: KIM · NV: Thu (Doanh thu), Chi (Chi phí), Thảo (Báo cáo)
    # ══════════════════════════════════════════════
    "phong_tai_chinh": {
        "ten": "Phòng Tài Chính Kế Toán",
        "emoji": "💼",
        "thanh_vien": "Kim CFO · Thu · Chi · Thảo",
        "chat": CHAT_PHONGBAN,
        "bai_hoc": [
            ("P&L cơ bản — đọc và hiểu",
             "P&L (Profit & Loss) QNPA:\n"
             "📥 Doanh thu: Học phí + Phụ kiện + Sàn TMĐT\n"
             "📤 Chi phí cố định: Lương, thuê sân, điện\n"
             "📤 Chi phí biến đổi: Ads, vật tư, sự kiện\n"
             "💰 Lợi nhuận = DT - CF cố định - CF biến đổi\n\n"
             "Break-even: ~65-70 HV (DT ~130-140tr)\n\n"
             "✏️ BÀI TẬP Thu: Cập nhật doanh thu tuần này vào Sheet."),

            ("Quản lý ngân sách Ads",
             "Ads budget QNPA:\n"
             "• Tháng: [X] triệu\n"
             "• Phân bổ: Facebook 60% · Google 30% · TikTok 10%\n\n"
             "Theo dõi hàng ngày:\n"
             "• Đã chi: [X]tr\n"
             "• Còn lại: [Y]tr\n"
             "• CPL hôm nay: [Z]k\n\n"
             "✏️ BÀI TẬP Chi: Báo ngân sách Ads còn lại tháng 6 vào nhóm."),

            ("Dòng tiền — cash flow hàng tuần",
             "Cash flow = tiền thực tế vào/ra tài khoản\n\n"
             "Theo dõi:\n"
             "• Thu vào: Học phí thu được\n"
             "• Chi ra: Lương, Ads, vật tư\n"
             "• Dự báo tuần tới: thiếu tiền không?\n\n"
             "✏️ BÀI TẬP Thảo: Tạo bảng cash flow tuần cho tháng 7."),

            ("Báo cáo tài chính — format chuẩn",
             "Báo cáo hàng tuần gửi chị Hoa:\n"
             "• Doanh thu tuần: [X]tr\n"
             "• Chi phí Ads: [Y]tr\n"
             "• Chi phí khác: [Z]tr\n"
             "• Lợi nhuận gộp: [W]tr\n"
             "• So tuần trước: +/-[%]\n\n"
             "✏️ BÀI TẬP: Gửi báo cáo theo template này mỗi thứ 6 trước 17h."),
        ]
    },
}

# ─────────────────────────────────────────────────────────────
# TÍNH NGÀY HỌC
# ─────────────────────────────────────────────────────────────
_NGAY_BAT_DAU = datetime(2026, 6, 20, tzinfo=VN).date()

def tinh_bai_hoc_hom_nay():
    hom_nay = datetime.now(VN).date()
    so_ngay = max(0, (hom_nay - _NGAY_BAT_DAU).days)
    return so_ngay

def ten_bai(data, idx):
    bai = data["bai_hoc"]
    return bai[idx % len(bai)]

# ─────────────────────────────────────────────────────────────
# TELEGRAM
# ─────────────────────────────────────────────────────────────
def tg(chat_id, text):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            timeout=10
        )
    except Exception as e:
        print(f"TG lỗi: {e}")

# ─────────────────────────────────────────────────────────────
# GỬI BÀI HỌC SÁNG 7:30
# ─────────────────────────────────────────────────────────────
def gui_bai_hoc_sang():
    idx = tinh_bai_hoc_hom_nay()
    hom_nay_str = datetime.now(VN).strftime("%d/%m/%Y")
    thu = ["Thứ Hai","Thứ Ba","Thứ Tư","Thứ Năm","Thứ Sáu","Thứ Bảy","Chủ Nhật"][datetime.now(VN).weekday()]

    # Header
    tg(CHAT_PHONGBAN,
        f"🌅 <b>BUỔI HỌC HÀNG NGÀY — QNPA TOÀN BỘ MÁY</b>\n"
        f"📅 {thu}, {hom_nay_str} · Ngày học thứ {idx+1}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"8 Phòng ban · CAS 8 Tầng · 1 Người 1 Việc\n"
        f"⏰ Deadline nộp bài tập: 17:30 hôm nay"
    )
    time.sleep(1)

    # Gửi bài cho từng phòng
    for key, data in PHONG_BAN.items():
        ten_pb = data["ten"]
        emoji = data["emoji"]
        thanh_vien = data["thanh_vien"]
        chat = data["chat"]
        ten_b, noi_dung = ten_bai(data, idx)

        msg = (
            f"{emoji} <b>{ten_pb.upper()}</b>\n"
            f"👥 {thanh_vien}\n"
            f"━━━━━━━━━━━━\n"
            f"📚 <b>{ten_b}</b>\n\n"
            f"{noi_dung}"
        )
        tg(chat, msg)
        time.sleep(1.5)

    # Lịch ngày
    tg(CHAT_PHONGBAN,
        f"📋 <b>LỊCH NGÀY {hom_nay_str}</b>\n"
        f"• 06:30 — Bài học hàng ngày (vừa gửi)\n"
        f"• 08:00 — Họp công việc 15 phút (Lan báo KPI)\n"
        f"• 12:00 — Check-in giữa ngày\n"
        f"• 17:30 — Họp chiều 10 phút\n"
        f"• 17:30 — Nộp bài tập\n"
        f"• 20:00 — Báo cáo ngày\n\n"
        f"💡 <i>Nộp bài = đã học. Không nộp = chưa học.</i>"
    )

# ─────────────────────────────────────────────────────────────
# HỌP SÁNG 8:00
# ─────────────────────────────────────────────────────────────
def nhac_hop_sang():
    tg(CHAT_PHONGBAN,
        "⏰ <b>HỌP SÁNG — BẮT ĐẦU</b> (15 phút)\n\n"
        "<b>Lan COO báo trước:</b>\n"
        "📊 Inbox hôm qua | Lead | Học thử | Chốt | CPL\n\n"
        "<b>Từng phòng trả lời 3 câu:</b>\n"
        "1️⃣ Hôm qua cam kết gì — xong chưa?\n"
        "2️⃣ Số liệu của phòng mình?\n"
        "3️⃣ Hôm nay cam kết 1 việc cụ thể?\n\n"
        "📌 Thứ tự: Lan → Mai → An → Ngọc → Bình → Linh → Hùng → Hải → Tuấn → Xuân → Kim"
    )

# ─────────────────────────────────────────────────────────────
# CHECK-IN GIỮA NGÀY 12:00
# ─────────────────────────────────────────────────────────────
def check_in_giua_ngay():
    tg(CHAT_PHONGBAN,
        "☀️ <b>CHECK-IN GIỮA NGÀY</b>\n\n"
        "Mỗi phòng gửi 1 dòng:\n"
        "✅ Sáng đã làm: [việc]\n"
        "🎯 Chiều sẽ làm: [việc]\n"
        "⚠️ Cần hỗ trợ: [nếu có]\n\n"
        "⏱ Gõ ngay — 2 phút thôi!"
    )
    # Nhắc thêm vào nhóm Sale
    tg(CHAT_SALE,
        "☀️ <b>P5 CHECK-IN 12h</b>\n"
        "Hùng + team: báo số gọi sáng nay và kết quả?"
    )

# ─────────────────────────────────────────────────────────────
# HỌP CHIỀU 17:30
# ─────────────────────────────────────────────────────────────
def nhac_hop_chieu():
    tg(CHAT_PHONGBAN,
        "🌆 <b>HỌP CHIỀU — KẾT THÚC NGÀY</b> (10 phút)\n\n"
        "1️⃣ Cam kết sáng — đã xong chưa?\n"
        "2️⃣ Block nào chưa giải quyết?\n"
        "3️⃣ Cần ai hỗ trợ tối nay?\n\n"
        "📚 <b>Nộp bài tập vào đây trước khi họp xong!</b>"
    )

# ─────────────────────────────────────────────────────────────
# BÁO CÁO ĐÀO TẠO 20:00 → CHỊ HOA
# ─────────────────────────────────────────────────────────────
def bao_cao_dao_tao():
    idx = tinh_bai_hoc_hom_nay()
    hom_nay_str = datetime.now(VN).strftime("%d/%m/%Y")

    # Tóm tắt bài hôm nay
    lines_hom_nay = []
    for key, data in PHONG_BAN.items():
        ten_b, _ = ten_bai(data, idx)
        lines_hom_nay.append(f"  {data['emoji']} <b>{data['ten']}</b>: {ten_b}")

    # Bài ngày mai
    lines_mai = []
    for key, data in PHONG_BAN.items():
        ten_b, _ = ten_bai(data, idx + 1)
        lines_mai.append(f"  {data['emoji']} {data['ten']}: {ten_b}")

    msg_hoa = (
        f"📚 <b>BÁO CÁO ĐÀO TẠO — {hom_nay_str}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📖 <b>Bài học hôm nay ({idx+1} ngày vận hành):</b>\n"
        + "\n".join(lines_hom_nay) +
        f"\n\n✅ Hệ thống đã gửi bài cho <b>9 phòng ban</b> · {sum(len(d['bai_hoc']) for d in PHONG_BAN.values())} bài trong chương trình\n"
        f"⏰ Deadline nộp bài: 17:30\n\n"
        f"📌 <b>Ngày mai:</b>\n"
        + "\n".join(lines_mai) +
        f"\n\n💡 <i>Xem ai nộp bài: nhóm QNPA NỘI BỘ PHÒNG BAN</i>"
    )
    tg(CHAT_COACHING, msg_hoa)

    # Nhắc nhóm phòng ban
    tg(CHAT_PHONGBAN,
        f"📊 <b>TỔNG KẾT NGÀY {hom_nay_str}</b>\n\n"
        f"Ai đã nộp bài tập hôm nay?\n"
        f"🙋 Gõ tên + phòng ban để confirm đã học.\n\n"
        f"Báo cáo đã gửi chị Hoa. Nghỉ ngơi tốt — hẹn 7:30 sáng mai! 💪"
    )

# ─────────────────────────────────────────────────────────────
# HỌP WIG THỨ 2 HÀNG TUẦN — gửi vào sáng thứ 2
# ─────────────────────────────────────────────────────────────
def hop_wig_thu_hai():
    tg(CHAT_PHONGBAN,
        "📅 <b>HỌP WIG TUẦN — THỨ HAI</b> (30 phút · 8:00)\n\n"
        "Agenda:\n"
        "1. Scoreboard tuần trước — đạt/không đạt WIG?\n"
        "2. Lead Measures của từng phòng\n"
        "3. Ai đã giữ cam kết? Ai chưa?\n"
        "4. Điều chỉnh gì cho tuần này?\n"
        "5. Cam kết mới từng người\n\n"
        "🎯 WIG tháng 7: <b>15 học viên mới</b>\n"
        "📊 Tiến độ: Cập nhật số vào đây trước 7:30"
    )
    tg(CHAT_COACHING,
        "📅 <b>HỌP WIG TUẦN — BÁO CÁO CHỊ HOA</b>\n\n"
        "Hôm nay thứ Hai — họp WIG toàn bộ máy lúc 8:00.\n"
        "Agenda đã gửi nhóm phòng ban.\n"
        "Kết quả họp sẽ gửi chị sau 8:30."
    )

# ─────────────────────────────────────────────────────────────
# STATE
# ─────────────────────────────────────────────────────────────
def load_state():
    try:
        if os.path.exists(_STATE_FILE):
            with open(_STATE_FILE, encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def save_state(state):
    try:
        with open(_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# ─────────────────────────────────────────────────────────────
# VÒNG LẶP CHÍNH
# ─────────────────────────────────────────────────────────────
def run_loop():
    print("DAO TAO HANG NGAY (9 phong ban) — khoi dong...")
    while True:
        now = datetime.now(VN)
        h, m = now.hour, now.minute
        thu = now.weekday()  # 0=T2 ... 6=CN
        ngay = now.strftime("%Y-%m-%d")
        state = load_state()
        s = state.get(ngay, {})

        try:
            # 6:30 — Bài học
            if h == 6 and 30 <= m < 40 and not s.get("bai_hoc"):
                print(f"[{now.strftime('%H:%M')}] Gui bai hoc sang...")
                gui_bai_hoc_sang()
                s["bai_hoc"] = True

            # 8:00 — Thứ 2: Họp Ban Điều Hành · Các ngày khác: Họp sáng WIG
            elif h == 8 and 0 <= m < 5 and not s.get("hop_sang"):
                print(f"[{now.strftime('%H:%M')}] Nhac hop sang...")
                if thu == 0:
                    # Thứ 2: gửi brief họp ban điều hành
                    try:
                        import hop_ban_dieu_hanh
                        hop_ban_dieu_hanh.gui_brief_chuan_bi()
                    except Exception as e:
                        print(f"Brief hop loi: {e}")
                    hop_wig_thu_hai()
                else:
                    nhac_hop_sang()
                s["hop_sang"] = True

            # 12:00 — Check-in giữa ngày
            elif h == 12 and 0 <= m < 5 and not s.get("checkin"):
                print(f"[{now.strftime('%H:%M')}] Check-in giua ngay...")
                check_in_giua_ngay()
                s["checkin"] = True

            # 17:30 — Họp chiều
            elif h == 17 and 30 <= m < 35 and not s.get("hop_chieu"):
                print(f"[{now.strftime('%H:%M')}] Nhac hop chieu...")
                nhac_hop_chieu()
                s["hop_chieu"] = True

            # 20:00 — Báo cáo đào tạo
            elif h == 20 and 0 <= m < 10 and not s.get("bao_cao"):
                print(f"[{now.strftime('%H:%M')}] Gui bao cao dao tao...")
                bao_cao_dao_tao()
                s["bao_cao"] = True

            # 21:30 — Nhắc chị Hoa mở agent sáng mai
            elif h == 21 and 30 <= m < 40 and not s.get("nhac_mai"):
                tg(CHAT_COACHING,
                    "⏰ <b>NHẮC NHỞ — MAI 6:30 HỆ THỐNG KHỞI ĐỘNG</b>\n\n"
                    "Chị Hoa nhớ mở <code>chay_agent.bat</code> trước 6:30 sáng mai nhé!\n\n"
                    "📂 File tại: <code>D:\\NÃO CỦA HOA\\chay_agent.bat</code>\n"
                    "▶️ Double-click là chạy — giữ cửa sổ đó mở cả ngày.\n\n"
                    "<i>Nếu đã mở rồi thì bỏ qua tin này ạ 😊</i>"
                )
                s["nhac_mai"] = True

            if s:
                state[ngay] = s
                save_state(state)

        except Exception as e:
            print(f"Loi: {e}")

        time.sleep(30)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "test":
            print("Test gui bai hoc sang...")
            gui_bai_hoc_sang()
        elif cmd == "bao_cao":
            bao_cao_dao_tao()
        elif cmd == "hop_sang":
            nhac_hop_sang()
        elif cmd == "wig":
            hop_wig_thu_hai()
        elif cmd == "checkin":
            check_in_giua_ngay()
        else:
            print(f"Lenh: test | bao_cao | hop_sang | wig | checkin")
    else:
        run_loop()
