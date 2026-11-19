import os
from PIL import Image, ImageDraw, ImageFont, ImageOps
import docx
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

BASE_DIR = r"c:\Users\Advan Workplus\Downloads\Project_IoT_2"
DOCS_DIR = os.path.join(BASE_DIR, "docs")
ASSETS_DIR = os.path.join(DOCS_DIR, "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)

BOARD_PHOTO_PATH = os.path.join(ASSETS_DIR, "board_trainer_kit_esp32_v4.jpg")
BLOCK_DIAGRAM_PATH = os.path.join(ASSETS_DIR, "diagram_blok_sistem.png")
FLOWCHART_PATH = os.path.join(ASSETS_DIR, "flowchart_sistem.png")
OUTPUT_DOCX_PATH = os.path.join(DOCS_DIR, "Laporan_Project_Akhir_IoT_Smart_Greenhouse.docx")


# =============================================================================
# 1. HELPER FONT & GAMBAR PILLOW
# =============================================================================
def get_font(size, bold=False):
    font_path = r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf"
    if os.path.exists(font_path):
        return ImageFont.truetype(font_path, size)
    return ImageFont.load_default()


def draw_centered_multiline(draw, box, lines, font, fill, line_spacing=6):
    x1, y1, x2, y2 = box
    cx = (x1 + x2) / 2
    heights = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        heights.append(bbox[3] - bbox[1])
    total_h = sum(heights) + line_spacing * (len(lines) - 1)
    curr_y = (y1 + y2 - total_h) / 2
    for idx, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        draw.text((cx - w / 2, curr_y), line, font=font, fill=fill)
        curr_y += heights[idx] + line_spacing


def draw_arrow(draw, start, end, color="#334155", width=4, head_len=14, double_headed=False):
    import math
    x1, y1 = start
    x2, y2 = end
    dx, dy = x2 - x1, y2 - y1
    dist = math.hypot(dx, dy)
    if dist == 0:
        return
    ux, uy = dx / dist, dy / dist
    line_start = (x1 + ux * (head_len * 0.65), y1 + uy * (head_len * 0.65)) if double_headed else start
    line_end = (x2 - ux * (head_len * 0.65), y2 - uy * (head_len * 0.65))
    draw.line([line_start, line_end], fill=color, width=width)

    def _head(tip_x, tip_y, from_x, from_y):
        ang = math.atan2(from_y - tip_y, from_x - tip_x)
        p1 = (tip_x + head_len * math.cos(ang - math.pi / 6), tip_y + head_len * math.sin(ang - math.pi / 6))
        p2 = (tip_x + head_len * math.cos(ang + math.pi / 6), tip_y + head_len * math.sin(ang + math.pi / 6))
        draw.polygon([(tip_x, tip_y), p1, p2], fill=color)

    _head(x2, y2, x1, y1)
    if double_headed:
        _head(x1, y1, x2, y2)


def draw_diamond(draw, cx, cy, half_w, half_h, fill, outline, width=3):
    pts = [(cx, cy - half_h), (cx + half_w, cy), (cx, cy + half_h), (cx - half_w, cy)]
    draw.polygon(pts, fill=fill, outline=outline)
    draw.line(pts + [pts[0]], fill=outline, width=width)


def normalize_board_photo():
    if not os.path.exists(BOARD_PHOTO_PATH):
        return
    with Image.open(BOARD_PHOTO_PATH) as img:
        transposed = ImageOps.exif_transpose(img)
        if transposed.mode != "RGB":
            transposed = transposed.convert("RGB")
        transposed.save(BOARD_PHOTO_PATH, format="JPEG", quality=92)


def generate_block_diagram():
    W, H = 1600, 920
    img = Image.new("RGB", (W, H), "#FFFFFF")
    draw = ImageDraw.Draw(img)

    f_title = get_font(30, bold=True)
    f_group = get_font(22, bold=True)
    f_box_title = get_font(20, bold=True)
    f_box_sub = get_font(17, bold=False)
    f_badge = get_font(17, bold=True)

    # Judul Diagram
    draw_centered_multiline(
        draw, (40, 20, W - 40, 75),
        ["DIAGRAM BLOK ARSITEKTUR SISTEM SMART MINI GREENHOUSE (ESP32 V4)"],
        f_title, "#0F172A"
    )

    # Container Kelompok Kiri: BLOK INPUT
    draw.rounded_rectangle([40, 100, 440, 860], radius=18, fill="#F0FDF4", outline="#16A34A", width=3)
    draw_centered_multiline(draw, (40, 112, 440, 155), ["BLOK INPUT (SENSOR & TOMBOL)"], f_group, "#14532D")

    inputs = [
        ("Sensor DHT11 (GPIO 32)", "Suhu (°C) & Kelembapan (% RH)"),
        ("Sensor LDR + R2 (GPIO 39)", "Intensitas Cahaya (0 - 100%)"),
        ("Potensiometer / Soil (GPIO 35/34)", "Kelembapan Tanah (0 - 100%)"),
        ("4x Push Button (33, 25, 14, 12)", "Kontrol Manual Fisik & Mode"),
    ]
    y_start = 175
    for idx, (t, sub) in enumerate(inputs):
        y1 = y_start + idx * 165
        y2 = y1 + 125
        draw.rounded_rectangle([70, y1, 410, y2], radius=12, fill="#FFFFFF", outline="#22C55E", width=2)
        draw_centered_multiline(draw, (78, y1 + 10, 402, y1 + 60), [t], f_box_title, "#0F172A")
        draw_centered_multiline(draw, (78, y1 + 60, 402, y2 - 10), [sub], f_box_sub, "#475569")
        draw_arrow(draw, (410, (y1 + y2) // 2), (560, 420), color="#16A34A", width=4)

    # Blok Tengah: PEMROSES ESP32
    draw.rounded_rectangle([560, 210, 1040, 620], radius=20, fill="#EFF6FF", outline="#2563EB", width=4)
    draw.rounded_rectangle([560, 210, 1040, 280], radius=20, fill="#1D4ED8")
    draw.rectangle([560, 255, 1040, 280], fill="#1D4ED8")
    draw_centered_multiline(draw, (560, 215, 1040, 275), ["UNIT KENDALI UTAMA (ESP32 V4)"], f_group, "#FFFFFF")

    draw_centered_multiline(
        draw, (585, 295, 1015, 595),
        [
            "Mikrokontroler ESP-WROOM-32D (38-Pin)",
            "• Akuisisi Sensor ADC1 & 1-Wire (Tiap 2 Detik)",
            "• Evaluasi Logika Otomatis (AUTO) & MANUAL",
            "• Pengendali Output Relay, PWM Servo, LED, Buzzer",
            "• Embedded HTTP Web Server (Port 80)",
            "• REST API JSON (/api/status & /api/control)"
        ],
        f_box_sub, "#1E293B", line_spacing=12
    )

    # Blok Bawah Tengah: JARINGAN & WEB DASHBOARD
    draw.rounded_rectangle([490, 695, 1110, 860], radius=18, fill="#ECFEFF", outline="#0891B2", width=3)
    draw_centered_multiline(
        draw, (505, 705, 1095, 755),
        ["ANTARMUKA PENGGUNA (JARINGAN LOKAL)"],
        f_box_title, "#0E7490"
    )
    draw_centered_multiline(
        draw, (505, 755, 1095, 845),
        [
            "Web Dashboard (Browser Laptop / Smartphone)",
            "Monitoring Real-Time, Grafik, Kontrol Manual & Threshold"
        ],
        f_box_sub, "#155E75", line_spacing=8
    )

    # Panah Dua Arah ESP32 <-> Web Dashboard via Wi-Fi
    draw_arrow(draw, (800, 620), (800, 695), color="#0284C7", width=5, double_headed=True)
    draw.rounded_rectangle([820, 636, 1055, 672], radius=8, fill="#E0F2FE", outline="#0284C7", width=2)
    draw_centered_multiline(draw, (825, 636, 1050, 672), ["Wi-Fi Lokal (HTTP JSON)"], f_badge, "#0369A1")

    # Container Kelompok Kanan: BLOK OUTPUT
    draw.rounded_rectangle([1160, 100, 1560, 860], radius=18, fill="#FFFBEB", outline="#D97706", width=3)
    draw_centered_multiline(draw, (1160, 112, 1560, 155), ["BLOK OUTPUT (AKTUATOR)"], f_group, "#78350F")

    outputs = [
        ("Relay (19) + LED3 Hijau (26)", "Saklar Pompa Air Irigasi"),
        ("Servo SG90 (23) + LED4 Biru (27)", "Ventilasi Atap (0° - 90°)"),
        ("LED2 Kuning (GPIO 2)", "Lampu Grow Light Tanaman"),
        ("Buzzer (13) + LED1 Merah (4)", "Alarm Peringatan Kondisi Kritis"),
    ]
    for idx, (t, sub) in enumerate(outputs):
        y1 = y_start + idx * 165
        y2 = y1 + 125
        draw.rounded_rectangle([1190, y1, 1530, y2], radius=12, fill="#FFFFFF", outline="#F59E0B", width=2)
        draw_centered_multiline(draw, (1198, y1 + 10, 1522, y1 + 60), [t], f_box_title, "#0F172A")
        draw_centered_multiline(draw, (1198, y1 + 60, 1522, y2 - 10), [sub], f_box_sub, "#475569")
        draw_arrow(draw, (1040, 420), (1190, (y1 + y2) // 2), color="#D97706", width=4)

    img.save(BLOCK_DIAGRAM_PATH, format="PNG")


def generate_flowchart():
    W, H = 1400, 1140
    img = Image.new("RGB", (W, H), "#FFFFFF")
    draw = ImageDraw.Draw(img)

    f_title = get_font(28, bold=True)
    f_box = get_font(19, bold=True)
    f_sub = get_font(17, bold=False)
    f_lbl = get_font(18, bold=True)

    draw_centered_multiline(
        draw, (40, 18, W - 40, 68),
        ["FLOWCHART ALUR KERJA SISTEM SMART MINI GREENHOUSE"],
        f_title, "#0F172A"
    )

    cx = W // 2

    # 1. MULAI
    draw.rounded_rectangle([cx - 130, 88, cx + 130, 148], radius=30, fill="#16A34A", outline="#14532D", width=3)
    draw_centered_multiline(draw, (cx - 130, 88, cx + 130, 148), ["MULAI"], f_box, "#FFFFFF")
    draw_arrow(draw, (cx, 148), (cx, 186), color="#334155", width=4)

    # 2. INISIALISASI
    draw.rounded_rectangle([cx - 290, 186, cx + 290, 284], radius=12, fill="#EFF6FF", outline="#2563EB", width=3)
    draw_centered_multiline(
        draw, (cx - 280, 192, cx + 280, 278),
        ["Inisialisasi Pin GPIO, Sensor DHT11 & Servo (0°)", "Koneksi Wi-Fi Lokal & Jalankan Web Server (Port 80)"],
        f_sub, "#1E293B", line_spacing=8
    )
    draw_arrow(draw, (cx, 284), (cx, 326), color="#334155", width=4)

    # 3. BACA SENSOR & TOMBOL
    draw.rounded_rectangle([cx - 310, 326, cx + 310, 424], radius=12, fill="#F0FDF4", outline="#16A34A", width=3)
    draw_centered_multiline(
        draw, (cx - 300, 332, cx + 300, 418),
        ["Baca Sensor Tiap 2 Detik & Pantau Button1-4", "DHT11 (32), LDR (39), Potensiometer/Soil (35/34)"],
        f_sub, "#14532D", line_spacing=8
    )
    draw_arrow(draw, (cx, 424), (cx, 466), color="#334155", width=4)

    # 4. DECISION: MODE AUTO?
    diamond_cy = 540
    draw_diamond(draw, cx, diamond_cy, 190, 74, fill="#FEF3C7", outline="#D97706", width=3)
    draw_centered_multiline(draw, (cx - 140, diamond_cy - 30, cx + 140, diamond_cy + 30), ["Mode Operasi", "== AUTO ?"], f_box, "#78350F")

    # Cabang Kiri: YA (AUTO)
    left_cx = 310
    draw.line([(cx - 190, diamond_cy), (left_cx, diamond_cy)], fill="#16A34A", width=4)
    draw_arrow(draw, (left_cx, diamond_cy), (left_cx, 620), color="#16A34A", width=4)
    draw.text((cx - 280, diamond_cy - 30), "YA (AUTO)", font=f_lbl, fill="#15803D")

    draw.rounded_rectangle([60, 620, 560, 825], radius=14, fill="#F8FAFC", outline="#16A34A", width=3)
    draw_centered_multiline(
        draw, (75, 630, 545, 815),
        [
            "Evaluasi Ambang Batas Otomatis:",
            "• Cahaya < 35%  -> LED2 Grow Light ON",
            "• Suhu > 31 °C   -> Servo Buka 90° + LED4 ON",
            "• Tanah < 40%    -> Relay Pompa + LED3 ON",
            "• Kritis (>=33°C / Panas+Kering) -> Buzzer + LED1 ON"
        ],
        f_sub, "#0F172A", line_spacing=10
    )

    # Cabang Kanan: TIDAK (MANUAL)
    right_cx = W - 310
    draw.line([(cx + 190, diamond_cy), (right_cx, diamond_cy)], fill="#2563EB", width=4)
    draw_arrow(draw, (right_cx, diamond_cy), (right_cx, 620), color="#2563EB", width=4)
    draw.text((cx + 210, diamond_cy - 30), "TIDAK (MANUAL)", font=f_lbl, fill="#1D4ED8")

    draw.rounded_rectangle([W - 560, 620, W - 60, 825], radius=14, fill="#F8FAFC", outline="#2563EB", width=3)
    draw_centered_multiline(
        draw, (W - 545, 630, W - 75, 815),
        [
            "Eksekusi Perintah Kendali Manual:",
            "• Terima Perintah HTTP POST /api/control",
            "• Terima Tekanan Button2, Button3, Button4",
            "• Kendalikan Relay, Servo, LED2 & Buzzer",
            "  sesuai pilihan pengguna"
        ],
        f_sub, "#0F172A", line_spacing=10
    )

    # Merge ke bawah
    merge_y = 875
    draw.line([(left_cx, 825), (left_cx, merge_y), (cx, merge_y)], fill="#334155", width=4)
    draw.line([(right_cx, 825), (right_cx, merge_y), (cx, merge_y)], fill="#334155", width=4)
    draw_arrow(draw, (cx, merge_y), (cx, 920), color="#334155", width=4)

    # 5. UPDATE STATUS & KIRIM JSON
    draw.rounded_rectangle([cx - 330, 920, cx + 330, 1030], radius=14, fill="#ECFEFF", outline="#0891B2", width=3)
    draw_centered_multiline(
        draw, (cx - 315, 928, cx + 315, 1022),
        [
            "Perbarui Status Kondisi Sistem & Output Perangkat Keras",
            "Kirim Data JSON ke Web Dashboard (Auto-Refresh Tiap 2 Detik)"
        ],
        f_sub, "#0E7490", line_spacing=10
    )

    # Loop kembali ke Baca Sensor
    loop_x = 32
    draw.line([(cx - 330, 975), (loop_x, 975), (loop_x, 375)], fill="#64748B", width=4)
    draw_arrow(draw, (loop_x, 375), (cx - 310, 375), color="#64748B", width=4)
    draw.text((48, 342), "Loop (2s)", font=f_lbl, fill="#475569")

    img.save(FLOWCHART_PATH, format="PNG")


# =============================================================================
# 2. HELPER STYLING PYTHON-DOCX
# =============================================================================
def set_cell_shading(cell, color_hex):
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading)


def set_cell_margins(cell, top=100, bottom=100, left=140, right=140):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement("w:tcMar")
    for m, val in [("top", top), ("bottom", bottom), ("left", left), ("right", right)]:
        node = OxmlElement(f"w:{m}")
        node.set(qn("w:w"), str(val))
        node.set(qn("w:type"), "dxa")
        tcMar.append(node)
    tcPr.append(tcMar)


def prevent_row_split(row):
    trPr = row._tr.get_or_add_trPr()
    trPr.append(OxmlElement("w:cantSplit"))


def repeat_header_row(row):
    trPr = row._tr.get_or_add_trPr()
    trPr.append(OxmlElement("w:tblHeader"))


def add_page_number_to_run(run):
    fldChar1 = parse_xml(r'<w:fldChar %s w:fldCharType="begin"/>' % nsdecls("w"))
    instrText = parse_xml(r'<w:instrText %s xml:space="preserve"> PAGE </w:instrText>' % nsdecls("w"))
    fldChar2 = parse_xml(r'<w:fldChar %s w:fldCharType="separate"/>' % nsdecls("w"))
    fldChar3 = parse_xml(r'<w:fldChar %s w:fldCharType="end"/>' % nsdecls("w"))
    run._r.append(fldChar1)
    run._r.append(instrText)
    run._r.append(fldChar2)
    run._r.append(fldChar3)


def add_styled_table(doc, headers, rows, col_widths=None, header_bg="14532D"):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    # Header Row
    hdr_row = table.rows[0]
    repeat_header_row(hdr_row)
    prevent_row_split(hdr_row)
    for i, text in enumerate(headers):
        cell = hdr_row.cells[i]
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        set_cell_shading(cell, header_bg)
        set_cell_margins(cell, top=110, bottom=110, left=120, right=120)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(text)
        r.bold = True
        r.font.name = "Calibri"
        r.font.size = Pt(10)
        r.font.color.rgb = RGBColor(255, 255, 255)
        if col_widths:
            cell.width = Cm(col_widths[i])

    # Data Rows
    for r_idx, row_data in enumerate(rows):
        row = table.rows[r_idx + 1]
        prevent_row_split(row)
        bg = "F8FAFC" if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate(row_data):
            cell = row.cells[c_idx]
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            set_cell_shading(cell, bg)
            set_cell_margins(cell, top=85, bottom=85, left=120, right=120)
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.15
            if c_idx == 0 and len(str(val)) <= 7:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(str(val))
            r.font.name = "Calibri"
            r.font.size = Pt(9.5)
            r.font.color.rgb = RGBColor(30, 41, 59)
            if col_widths:
                cell.width = Cm(col_widths[c_idx])

    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_before = Pt(0)
    spacer.paragraph_format.space_after = Pt(6)
    return table


def add_chapter_heading(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    pPr = p._p.get_or_add_pPr()
    pBdr = parse_xml(f'<w:pBdr {nsdecls("w")}><w:bottom w:val="single" w:sz="12" w:space="4" w:color="16A34A"/></w:pBdr>')
    pPr.append(pBdr)
    r = p.add_run(text)
    r.bold = True
    r.font.name = "Calibri"
    r.font.size = Pt(14)
    r.font.color.rgb = RGBColor(20, 83, 45)
    return p


def add_sub_heading(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    r.bold = True
    r.font.name = "Calibri"
    r.font.size = Pt(11.5)
    r.font.color.rgb = RGBColor(15, 23, 42)
    return p


def add_body_p(doc, text, bold_prefix=None, space_after=6):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.25
    if bold_prefix:
        rb = p.add_run(bold_prefix)
        rb.bold = True
        rb.font.name = "Calibri"
        rb.font.size = Pt(11)
        rb.font.color.rgb = RGBColor(15, 23, 42)
    r = p.add_run(text)
    r.font.name = "Calibri"
    r.font.size = Pt(11)
    r.font.color.rgb = RGBColor(30, 41, 59)
    return p


def add_bullet_p(doc, bold_prefix, text):
    p = doc.add_paragraph(style="List Bullet")
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.2
    if bold_prefix:
        rb = p.add_run(bold_prefix)
        rb.bold = True
        rb.font.name = "Calibri"
        rb.font.size = Pt(10.5)
        rb.font.color.rgb = RGBColor(15, 23, 42)
    r = p.add_run(text)
    r.font.name = "Calibri"
    r.font.size = Pt(10.5)
    r.font.color.rgb = RGBColor(30, 41, 59)
    return p


def add_code_block(doc, code_text):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = table.rows[0].cells[0]
    cell.width = Cm(15.5)
    set_cell_shading(cell, "F1F5F9")
    set_cell_margins(cell, top=120, bottom=120, left=160, right=140)
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        '<w:top w:val="single" w:sz="4" w:space="0" w:color="CBD5E1"/>'
        '<w:bottom w:val="single" w:sz="4" w:space="0" w:color="CBD5E1"/>'
        '<w:right w:val="single" w:sz="4" w:space="0" w:color="CBD5E1"/>'
        '<w:left w:val="single" w:sz="24" w:space="0" w:color="16A34A"/>'
        '</w:tcBorders>'
    )
    tcPr.append(borders)
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.08
    r = p.add_run(code_text)
    r.font.name = "Consolas"
    r.font.size = Pt(8.5)
    r.font.color.rgb = RGBColor(15, 23, 42)

    sp = doc.add_paragraph()
    sp.paragraph_format.space_after = Pt(6)


def add_figure(doc, image_path, width_cm, caption_text):
    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.paragraph_format.space_before = Pt(6)
    p_img.paragraph_format.space_after = Pt(4)
    p_img.paragraph_format.keep_with_next = True
    run = p_img.add_run()
    run.add_picture(image_path, width=Cm(width_cm))

    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.paragraph_format.space_before = Pt(0)
    p_cap.paragraph_format.space_after = Pt(10)
    rc = p_cap.add_run(caption_text)
    rc.italic = True
    rc.font.name = "Calibri"
    rc.font.size = Pt(9.5)
    rc.font.color.rgb = RGBColor(71, 85, 105)


# =============================================================================
# 3. BANGUN DOKUMEN WORD LENGKAP
# =============================================================================
def build_report_docx():
    doc = Document()

    # Konfigurasi Halaman A4
    section = doc.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.4)
    section.bottom_margin = Cm(2.4)
    section.left_margin = Cm(2.8)
    section.right_margin = Cm(2.4)
    section.different_first_page_header_footer = True

    # Running Header & Footer (Halaman 2 dst)
    hdr = section.header.paragraphs[0]
    hdr.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    rh = hdr.add_run("Laporan Project Akhir IoT — Smart Mini Greenhouse Monitoring & Control System")
    rh.font.name = "Calibri"
    rh.font.size = Pt(8.5)
    rh.font.color.rgb = RGBColor(100, 116, 139)

    ftr = section.footer.paragraphs[0]
    ftr.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    rf1 = ftr.add_run("Halaman ")
    rf1.font.name = "Calibri"
    rf1.font.size = Pt(9)
    rf1.font.color.rgb = RGBColor(100, 116, 139)
    rf_num = ftr.add_run()
    rf_num.font.name = "Calibri"
    rf_num.font.size = Pt(9)
    rf_num.font.color.rgb = RGBColor(100, 116, 139)
    add_page_number_to_run(rf_num)

    # -------------------------------------------------------------------------
    # HALAMAN SAMPUL (COVER PAGE)
    # -------------------------------------------------------------------------
    p_top = doc.add_paragraph()
    p_top.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_top.paragraph_format.space_before = Pt(28)
    p_top.paragraph_format.space_after = Pt(10)
    rt = p_top.add_run("LAPORAN PROJECT AKHIR\nUJIAN AKHIR SEMESTER (UAS)\nINTERNET OF THINGS (IoT)")
    rt.bold = True
    rt.font.name = "Calibri"
    rt.font.size = Pt(18)
    rt.font.color.rgb = RGBColor(20, 83, 45)

    p_line = doc.add_paragraph()
    p_line.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_line.paragraph_format.space_after = Pt(24)
    rl = p_line.add_run("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    rl.font.color.rgb = RGBColor(22, 163, 74)

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(10)
    p_title.paragraph_format.space_after = Pt(12)
    r_title = p_title.add_run(
        "SMART MINI GREENHOUSE MONITORING & CONTROL SYSTEM\n"
        "BERBASIS ALL-IN-ONE TRAINER KIT ESP32 DEVKITC V4 (38-PIN)\n"
        "DENGAN ANTARMUKA WEB DASHBOARD LOKAL"
    )
    r_title.bold = True
    r_title.font.name = "Calibri"
    r_title.font.size = Pt(15)
    r_title.font.color.rgb = RGBColor(15, 23, 42)

    p_tema = doc.add_paragraph()
    p_tema.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_tema.paragraph_format.space_after = Pt(32)
    r_tema = p_tema.add_run("Tema Project: Smart Agriculture / Automated Mini Greenhouse")
    r_tema.italic = True
    r_tema.font.name = "Calibri"
    r_tema.font.size = Pt(12)
    r_tema.font.color.rgb = RGBColor(71, 85, 105)

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_after = Pt(10)
    r_sub = p_sub.add_run("Disusun oleh Kelompok:")
    r_sub.bold = True
    r_sub.font.name = "Calibri"
    r_sub.font.size = Pt(11.5)

    add_styled_table(
        doc,
        ["No", "Nama Mahasiswa", "NIM", "Kelas / Peran"],
        [
            ["1", "[Isi Nama Anggota 1]", "[Isi NIM 1]", "[Ketua / Firmware & Hardware]"],
            ["2", "[Isi Nama Anggota 2]", "[Isi NIM 2]", "[Web Dashboard & Pengujian]"],
            ["3", "[Isi Nama Anggota 3]", "[Isi NIM 3]", "[Dokumentasi & Laporan]"],
        ],
        col_widths=[1.4, 5.5, 3.8, 4.8],
        header_bg="1E3A8A"
    )

    p_bot = doc.add_paragraph()
    p_bot.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_bot.paragraph_format.space_before = Pt(48)
    rb = p_bot.add_run(
        "MATA KULIAH INTERNET OF THINGS (IoT)\n"
        "PROGRAM STUDI [ISI NAMA PROGRAM STUDI]\n"
        "FAKULTAS / UNIVERSITAS [ISI NAMA INSTITUSI]\n"
        "DESEMBER 2026"
    )
    rb.bold = True
    rb.font.name = "Calibri"
    rb.font.size = Pt(12)
    rb.font.color.rgb = RGBColor(15, 23, 42)

    doc.add_page_break()

    # -------------------------------------------------------------------------
    # BAB I: JUDUL, LATAR BELAKANG, RUMUSAN MASALAH, DAN TUJUAN
    # -------------------------------------------------------------------------
    add_chapter_heading(doc, "BAB I. JUDUL, LATAR BELAKANG, DAN TUJUAN")

    add_sub_heading(doc, "1.1 Judul dan Tema Project")
    add_body_p(
        doc,
        "Smart Mini Greenhouse Monitoring & Control System Berbasis All-in-One Trainer Kit ESP32 DevKitC V4 (38-Pin) dengan Antarmuka Web Dashboard Lokal.",
        bold_prefix="Judul Project: "
    )
    add_body_p(
        doc,
        "Smart Agriculture / Automated Mini Greenhouse (Pemantauan iklim mikro rumah kaca serta pengendalian irigasi, pencahayaan tambahan, ventilasi, dan alarm peringatan secara otomatis maupun manual).",
        bold_prefix="Tema Project: "
    )

    add_sub_heading(doc, "1.2 Latar Belakang")
    add_body_p(
        doc,
        "Keberhasilan budidaya tanaman di dalam rumah kaca (greenhouse) sangat bergantung pada kestabilan parameter lingkungan mikro di sekitarnya, meliputi suhu udara, kelembapan udara, intensitas cahaya matahari, dan kelembapan media tanam. Tanaman mudah mengalami stres fisiologis apabila suhu di dalam ruangan melonjak akibat efek rumah kaca pada siang hari, kekurangan cahaya saat cuaca mendung atau malam hari, maupun mengalami kekeringan media tanam akibat keterlambatan penyiraman."
    )
    add_body_p(
        doc,
        "Pada pengelolaan greenhouse konvensional, pemantauan kondisi masih dilakukan secara manual melalui pengamatan fisik dan penyiraman terjadwal tanpa melihat kondisi aktual tanah. Pendekatan tersebut menimbulkan beberapa permasalahan utama: (1) tidak adanya pemantauan parameter suhu, kelembapan, dan cahaya secara kontinu dan terdokumentasi; (2) keterlambatan tindakan penyiraman atau pembukaan ventilasi saat kondisi lingkungan melewati batas ideal; serta (3) tidak tersedianya antarmuka terpusat untuk memantau status sistem dan mengendalikan aktuator secara cepat melalui laptop maupun smartphone."
    )
    add_body_p(
        doc,
        "Untuk mengatasi permasalahan tersebut, dirancang sebuah sistem Internet of Things (IoT) berbasis All-in-One Trainer Kit ESP32 DevKitC V4 (38-Pin). Papan Trainer Kit ini telah mengintegrasikan mikrokontroler ESP-WROOM-32D bersama sensor DHT11, sensor cahaya LDR, knop potensiometer, modul Relay, motor Servo SG90, 4 buah LED indikator, Buzzer, dan 4 buah tombol tekan pada satu papan PCB terpadu. Dengan memanfaatkan modul Wi-Fi internal ESP32 pada jaringan lokal (Hotspot HP atau Router tanpa wajib akses internet), sistem mampu mengirimkan data sensor setiap 2 detik ke antarmuka Web Dashboard sekaligus menjalankan otomasi aktuator maupun kendali manual secara real-time."
    )

    add_sub_heading(doc, "1.3 Rumusan Masalah")
    add_bullet_p(doc, "Akuisisi Multi-Sensor: ", "Bagaimana membaca dan mengkalibrasi data suhu udara (°C), kelembapan udara (% RH), intensitas cahaya (%), dan kelembapan media tanam (%) pada papan Trainer Kit ESP32 V4?")
    add_bullet_p(doc, "Integrasi Jaringan Lokal: ", "Bagaimana menghubungkan ESP32 ke jaringan Wi-Fi lokal (Hotspot/Router) serta mengirimkan data sensor dan perintah kendali melalui protokol HTTP JSON tanpa ketergantungan internet?")
    add_bullet_p(doc, "Otomasi & Kontrol Manual: ", "Bagaimana mengimplementasikan logika pengendalian aktuator (Relay Pompa Air, Motor Servo Ventilasi, LED Grow Light, dan Buzzer) secara otomatis (AUTO) berdasarkan ambang batas maupun manual (MANUAL) dari Web Dashboard dan tombol fisik?")

    add_sub_heading(doc, "1.4 Tujuan Project dan Sasaran Keberhasilan")
    add_bullet_p(doc, "1. Perancangan Sistem Terintegrasi: ", "Membangun prototipe perangkat keras Smart Mini Greenhouse menggunakan Trainer Kit ESP32 DevKitC V4 beserta dukungan opsi sensor Soil Moisture dan pompa/kipas DC eksternal.")
    add_bullet_p(doc, "2. Komunikasi Data Real-Time: ", "Mengimplementasikan Web Server lokal dan REST API JSON di dalam ESP32 untuk pembaruan data otomatis setiap 2 detik ke antarmuka Web Dashboard.")
    add_bullet_p(doc, "3. Pengendalian Dual-Mode: ", "Menyediakan mekanisme kendali otomatis berbasis threshold sensor dan kendali manual interaktif melalui halaman web maupun 4 tombol fisik pada board.")
    add_bullet_p(doc, "4. Pemenuhan Ketentuan UAS: ", "Memenuhi seluruh kriteria tugas akhir meliputi fungsi perangkat keras, integrasi jaringan, kelengkapan informasi wajib pada antarmuka, laporan teknis, dan kesiapan demonstrasi.")

    # -------------------------------------------------------------------------
    # BAB II: DAFTAR ALAT DAN BAHAN
    # -------------------------------------------------------------------------
    add_chapter_heading(doc, "BAB II. DAFTAR ALAT DAN BAHAN (RINCIAN KOMPONEN)")

    add_sub_heading(doc, "2.1 Komponen Utama & Terintegrasi Aktif pada PCB Trainer Kit ESP32 V4")
    add_body_p(
        doc,
        "Seluruh komponen pada Tabel 2.1 telah terintegrasi secara fisik di atas papan PCB All-in-One Trainer Kit ESP32 DevKitC V4 (termasuk resistor pembagi tegangan R2 untuk LDR, resistor pembatas arus R6–R9 untuk LED1–LED4, serta driver transistor Relay dan Buzzer)."
    )
    add_styled_table(
        doc,
        ["No", "Nama Komponen", "Spesifikasi / Label PCB", "Pin GPIO", "Fungsi dalam Smart Mini Greenhouse"],
        [
            ["1", "Mikrokontroler ESP32", "ESP-WROOM-32D DevKitC V4 (38-Pin, Wi-Fi 2.4 GHz, ADC 12-bit)", "-", "Otak utama sistem, pembaca sensor, logika kontrol, & HTTP Web Server Port 80"],
            ["2", "Sensor DHT11 (Biru)", "Sensor digital 1-Wire suhu & kelembapan udara", "GPIO 32", "Membaca suhu udara (°C) dan kelembapan udara (% RH)"],
            ["3", "Sensor LDR + Resistor R2", "Fotoresistor 2-kaki + rangkaian pembagi tegangan PCB", "GPIO 39 (ADC1)", "Mengukur intensitas cahaya matahari (0–100%)"],
            ["4", "Knop Potensiometer", "Resistor variabel putar (GND / 35 / 3V3)", "GPIO 35 (ADC1)", "Input/simulator kelembapan media tanam (0–100%) saat demo"],
            ["5", "Modul Relay 5V", "Songle SRD-05VDC-SL-C + terminal sekrup NC/COM/NO", "GPIO 19", "Saklar elektronik otomatis pengendali Pompa Air Irigasi"],
            ["6", "Motor Servo SG90", "Micro Servo PWM 50 Hz (label 23 / 5V / G)", "GPIO 23", "Penggerak jendela ventilasi atap greenhouse (0° tutup ↔ 90° buka)"],
            ["7", "Active Buzzer", "Buzzer alarm + transistor driver onboard", "GPIO 13", "Alarm peringatan suara putus-putus saat kondisi CRITICAL"],
            ["8", "LED1 (Merah)", "LED 5mm + resistor R6", "GPIO 4", "Indikator visual Alarm Kondisi Kritis (selaras dengan Buzzer)"],
            ["9", "LED2 (Kuning)", "LED 5mm + resistor R7", "GPIO 2", "Lampu Grow Light (menyala otomatis saat cahaya LDR < 35%)"],
            ["10", "LED3 (Hijau)", "LED 5mm + resistor R8", "GPIO 26", "Indikator visual Pompa Air menyala (selaras dengan Relay 19)"],
            ["11", "LED4 (Biru)", "LED 5mm + resistor R9", "GPIO 27", "Indikator Ventilasi Pendingin aktif (selaras Servo 23) & kedip koneksi Wi-Fi"],
            ["12", "Button1 (Merah)", "Tactile Push Button onboard", "GPIO 33", "Tombol fisik pergantian mode operasi AUTO ↔ MANUAL"],
            ["13", "Button2 (Kuning)", "Tactile Push Button onboard", "GPIO 25", "Tombol fisik kontrol manual lampu Grow Light (LED2)"],
            ["14", "Button3 (Hijau)", "Tactile Push Button onboard", "GPIO 14", "Tombol fisik kontrol manual Pompa Air (Relay 19 + LED3)"],
            ["15", "Button4 (Biru)", "Tactile Push Button onboard", "GPIO 12", "Tombol fisik kontrol manual Ventilasi (Servo 23 + LED4)"],
        ],
        col_widths=[1.0, 3.3, 4.3, 2.2, 4.7]
    )

    add_sub_heading(doc, "2.2 Opsi Komponen Eksternal (Plug-and-Play ke Papan Trainer Kit)")
    add_styled_table(
        doc,
        ["No", "Komponen Eksternal", "Media Penyambungan ke PCB", "Pin / Terminal", "Fungsi Tambahan"],
        [
            ["16", "Sensor Soil Moisture Asli (Opsional)", "3 helai kabel jumper Male-to-Female ke soket 3-pin bekas sensor PIR", "5V | GPIO 34 | GND", "Mengukur kelembapan tanah fisik secara langsung menggantikan Potensiometer (GPIO 35)"],
            ["17", "Pompa Air Mini / Kipas DC 5V (Opsional)", "Terminal baut sekrup hijau Relay (COM ke +5V, NO ke + Pompa, - ke GND)", "Terminal Relay (GPIO 19)", "Mengalirkan air irigasi atau sirkulasi udara nyata pada maket greenhouse"],
        ],
        col_widths=[1.0, 3.6, 4.4, 2.5, 4.0]
    )

    add_sub_heading(doc, "2.3 Inventarisasi Komponen Lain pada PCB Trainer Kit (Status Cadangan)")
    add_body_p(
        doc,
        "Sesuai ketentuan tugas bahwa jenis dan jumlah sensor disesuaikan dengan kebutuhan tema project, beberapa periferal lain yang ikut terpasang di papan PCB Trainer Kit ESP32 V4 didokumentasikan sebagai komponen cadangan untuk pengembangan versi lanjutan:"
    )
    add_styled_table(
        doc,
        ["No", "Komponen Tambahan di PCB", "Pin di PCB", "Status Versi v1.0", "Potensi Pengembangan Lanjutan (v1.1+)"],
        [
            ["18", "Layar OLED 0.96\" (SSD1306)", "SDA 21, SCL 22 (I2C)", "Cadangan", "Menampilkan IP Address Wi-Fi, suhu, kelembapan, & status pompa langsung di alat"],
            ["19", "Sensor BME/BMP280", "SDA 21, SCL 22 (I2C)", "Cadangan", "Pembacaan tekanan udara (hPa) dan suhu presisi tambahan"],
            ["20", "Sensor Gerak PIR HC-SR501", "GPIO 34 (5V/34/GND)", "Cadangan (dicabut jika memakai Soil Moisture)", "Deteksi pergerakan hama atau orang di sekitar greenhouse"],
            ["21", "Sensor Jarak Ultrasonik HC-SR04", "Header Trig & Echo", "Cadangan", "Mengukur ketinggian sisa air dalam tangki tandon irigasi"],
            ["22", "Sensor Gas & Asap MQ-2", "Soket MQ-2 PCB", "Cadangan", "Deteksi dini asap atau indikasi kebakaran di area greenhouse"],
            ["23", "Display 2-Digit 7-Segment", "Jalur Multiplex PCB", "Cadangan", "Penampil angka suhu atau kelembapan lokal tanpa komputer"],
        ],
        col_widths=[1.0, 3.7, 2.8, 2.7, 5.3]
    )

    add_sub_heading(doc, "2.4 Perangkat Lunak dan Sarana Pendukung")
    add_styled_table(
        doc,
        ["No", "Nama Perangkat Lunak / Sarana", "Versi / Keterangan", "Kegunaan"],
        [
            ["1", "Arduino IDE", "v1.8.x / v2.x + ESP32 Board Core", "Menulis, mengompilasi, dan mengunggah kode smart_greenhouse_esp32.ino ke ESP32"],
            ["2", "Library DHT sensor & Adafruit Unified Sensor", "by Adafruit (via Library Manager)", "Membaca data suhu dan kelembapan digital dari sensor DHT11"],
            ["3", "Web Browser (Chrome / Edge / Safari)", "Laptop & Smartphone", "Menampilkan antarmuka Web Dashboard lokal secara real-time"],
            ["4", "Kabel Data Micro-USB & Hotspot Wi-Fi", "5V DC / Jaringan Lokal 2.4 GHz", "Pemrograman, suplai daya papan, serta media komunikasi lokal ESP32 ↔ Browser"],
        ],
        col_widths=[1.0, 4.4, 3.8, 6.3]
    )

    # -------------------------------------------------------------------------
    # BAB III: DIAGRAM BLOK SISTEM DAN RANGKAIAN PERANGKAT
    # -------------------------------------------------------------------------
    add_chapter_heading(doc, "BAB III. DIAGRAM BLOK SISTEM DAN RANGKAIAN PERANGKAT")

    add_sub_heading(doc, "3.1 Diagram Blok Sistem")
    add_body_p(
        doc,
        "Sistem Smart Mini Greenhouse dibagi menjadi empat blok fungsional utama: Blok Input (Sensor & Tombol Fisik), Blok Pemroses & Web Server (ESP32 DevKitC V4), Blok Output (Aktuator & Indikator Visual), dan Blok Antarmuka Pengguna (Web Dashboard melalui Wi-Fi Lokal). Aliran data dan sinyal kendali antarblok ditunjukkan pada Gambar 3.1."
    )
    add_figure(doc, BLOCK_DIAGRAM_PATH, 15.6, "Gambar 3.1 Diagram Blok Arsitektur Sistem Smart Mini Greenhouse Berbasis ESP32 V4")

    add_sub_heading(doc, "3.2 Rangkaian Fisik dan Papan Integrasi Trainer Kit ESP32 V4")
    add_body_p(
        doc,
        "Rangkaian perangkat keras menggunakan papan integrasi All-in-One Trainer Kit ESP32 DevKitC V4 (38-Pin), di mana seluruh komponen input dan output telah terhubung melalui jalur tembaga PCB. Penggunaan PCB terpadu ini memastikan keandalan sambungan listrik saat demonstrasi, mengurangi risiko kabel lepas, serta menjaga stabilitas pembagi tegangan analog pada sensor LDR dan Potensiometer. Tata letak fisik perangkat keras ditunjukkan pada Gambar 3.2."
    )
    if os.path.exists(BOARD_PHOTO_PATH):
        add_figure(doc, BOARD_PHOTO_PATH, 9.2, "Gambar 3.2 Foto Rangkaian Fisik All-in-One Trainer Kit ESP32 DevKitC V4 (38-Pin)")

    add_sub_heading(doc, "3.3 Tabel Pemetaan Lengkap Pinout GPIO dan Penjelasan Teknis")
    add_styled_table(
        doc,
        ["Periferal", "Pin ESP32", "Tipe Sinyal", "Logika Aktif / Keterangan Teknis"],
        [
            ["DHT11 (Suhu & RH)", "GPIO 32", "Digital 1-Wire", "Membaca suhu (°C) dan kelembapan udara (% RH) setiap 2 detik"],
            ["Sensor LDR + R2", "GPIO 39 (VN)", "Analog Input (ADC1)", "Resolusi 12-bit (0–4095) dipetakan ke 0–100% intensitas cahaya"],
            ["Potensiometer", "GPIO 35", "Analog Input (ADC1)", "Resolusi 12-bit (0–4095) dipetakan ke 0–100% kelembapan tanah"],
            ["Opsi Soil Moisture", "GPIO 34", "Analog Input (ADC1)", "Via 3 kabel jumper Male-to-Female pada soket 3-pin (5V | 34 | GND)"],
            ["Relay (Pompa Air)", "GPIO 19", "Digital Output", "Mengaktifkan kumparan Relay 5V Songle SRD-05VDC-SL-C"],
            ["Servo SG90 (Ventilasi)", "GPIO 23", "PWM (50 Hz)", "Pulsa 500–2400 µs (25 siklus tiap perubahan sudut 0° ↔ 90°)"],
            ["Active Buzzer", "GPIO 13", "Digital Output", "Berbunyi putus-putus (interval 450 ms) saat kondisi CRITICAL"],
            ["LED1 (Merah)", "GPIO 4", "Digital Output", "Menyala saat status CRITICAL (selaras dengan Buzzer)"],
            ["LED2 (Kuning)", "GPIO 2", "Digital Output", "Menyala sebagai simulasi Lampu Grow Light saat LDR < 35%"],
            ["LED3 (Hijau)", "GPIO 26", "Digital Output", "Menyala mengikuti status aktif Relay Pompa Air"],
            ["LED4 (Biru)", "GPIO 27", "Digital Output", "Menyala saat ventilasi Servo terbuka; berkedip saat mencari Wi-Fi"],
            ["Button1–4 (Fisik)", "GPIO 33, 25, 14, 12", "Digital Input (PULLUP)", "Button1 Mode, Button2 Grow Light, Button3 Pompa, Button4 Servo"],
        ],
        col_widths=[3.6, 2.7, 3.2, 6.0]
    )

    add_body_p(
        doc,
        "Pertimbangan teknis utama dalam perancangan rangkaian: (1) seluruh sensor analog (LDR GPIO 39, Potensiometer GPIO 35, dan opsi Soil Moisture GPIO 34) menggunakan kanal ADC1 karena kanal ADC2 tidak dapat dipakai saat Wi-Fi ESP32 aktif; (2) tombol Button4 menggunakan GPIO 12 (pin strapping MTDI) sehingga tombol tersebut tidak boleh ditekan saat proses booting atau upload program; serta (3) pengendalian sudut Servo menggunakan pembangkitan pulsa PWM 50 Hz secara langsung sehingga kompatibel dengan ESP32 Arduino Core versi 2.x maupun 3.x tanpa konflik timer.",
        bold_prefix="Catatan Teknis Rangkaian: "
    )

    # -------------------------------------------------------------------------
    # BAB IV: ALUR KERJA SERTA METODE KOMUNIKASI DATA
    # -------------------------------------------------------------------------
    add_chapter_heading(doc, "BAB IV. ALUR KERJA SERTA METODE KOMUNIKASI DATA")

    add_sub_heading(doc, "4.1 Alur Kerja Sistem")
    add_body_p(
        doc,
        "Secara garis besar, siklus kerja perangkat lunak pada ESP32 berjalan secara non-blocking menggunakan pewaktu millis() sehingga layanan HTTP Web Server dan pembacaan 4 tombol fisik tetap responsif setiap saat. Diagram alur kerja lengkap sistem ditunjukkan pada Gambar 4.1."
    )
    add_figure(doc, FLOWCHART_PATH, 14.8, "Gambar 4.1 Flowchart Alur Kerja Sistem Smart Mini Greenhouse")

    add_body_p(doc, "Tahapan eksekusi sistem:", bold_prefix="")
    add_bullet_p(doc, "1. Inisialisasi: ", "Mengatur mode pin input/output, menutup ventilasi Servo ke posisi 0°, memulai sensor DHT11, dan menyambungkan ESP32 ke Wi-Fi Hotspot/Router lokal hingga mendapatkan alamat IP.")
    add_bullet_p(doc, "2. Pembacaan Sensor & Tombol: ", "Setiap 2.000 ms (2 detik), ESP32 membaca DHT11, mengambil rata-rata 5 sampel pembacaan ADC dari LDR dan Potensiometer/Soil Moisture, serta memantau perubahan kondisi 4 tombol fisik dengan metode debounce (60 ms).")
    add_bullet_p(doc, "3. Evaluasi Mode AUTO vs MANUAL: ", "Pada mode AUTO, aktuator dikendalikan otomatis berdasarkan perbandingan nilai sensor terhadap ambang batas (maxTemp = 31.0 °C, minSoil = 40%, minLight = 35%). Pada mode MANUAL, status aktuator mengikuti perintah terakhir dari Web Dashboard maupun tombol fisik Button2–Button4.")
    add_bullet_p(doc, "4. Penentuan Status Kondisi Sistem: ", "Sistem mengklasifikasikan kondisi lingkungan ke dalam 7 tingkat status sesuai Tabel 4.1 untuk ditampilkan di banner Web Dashboard.")

    add_styled_table(
        doc,
        ["Prioritas", "Kondisi Sensor / Mode", "Alert Level", "Status Kondisi Sistem & Respons Aktuator"],
        [
            ["1", "Suhu ≥ 33.0 °C atau (Suhu > 31.0 °C & Tanah < 40%)", "CRITICAL", "KRITIS - Suhu Panas & Tanah Kering (Buzzer + LED1 Merah ON, Servo Buka, Relay ON)"],
            ["2", "Tanah < 40% dan Cahaya < 35%", "ACTIVE", "MENYIRAM & GROW LIGHT AKTIF - Tanah Kering & Cahaya Kurang (Relay + LED3 + LED2 ON)"],
            ["3", "Kelembapan Tanah < 40%", "ACTIVE", "MENYIRAM - Tanah Kering (Relay 19 & LED3 Hijau ON)"],
            ["4", "Suhu Udara > 31.0 °C", "ACTIVE", "PENDINGINAN AKTIF - Suhu Tinggi (Servo Buka 90° & LED4 Biru ON)"],
            ["5", "Intensitas Cahaya LDR < 35%", "ACTIVE", "GROW LIGHT AKTIF - Cahaya Kurang (LED2 Kuning ON)"],
            ["6", "Mode MANUAL dengan aktuator aktif", "ACTIVE", "KONTROL MANUAL AKTIF - Kondisi Lingkungan Ideal"],
            ["7", "Seluruh parameter dalam rentang ideal", "NORMAL", "NORMAL - Kondisi Greenhouse Ideal (Seluruh Aktuator OFF, Servo 0°)"],
        ],
        col_widths=[1.5, 4.7, 2.2, 7.1]
    )

    add_sub_heading(doc, "4.2 Metode Komunikasi Data (Jaringan Lokal & REST API)")
    add_body_p(
        doc,
        "Sesuai ketentuan tugas bahwa koneksi internet tidak diwajibkan apabila sistem dapat berjalan melalui jaringan lokal, komunikasi data antara ESP32 dan perangkat pengguna (Laptop/Smartphone) dirancang menggunakan arsitektur Client–Server lokal berbasis protokol HTTP/1.1 pada Port 80 dengan format pertukaran data JSON. Seluruh endpoint telah dilengkapi header CORS (Access-Control-Allow-Origin: *) agar Web Dashboard dapat langsung memanggil API ESP32 dari browser."
    )
    add_styled_table(
        doc,
        ["Method", "Endpoint", "Parameter / Input", "Fungsi Komunikasi"],
        [
            ["GET", "/", "-", "Menyajikan halaman web ringkas langsung dari memori internal ESP32"],
            ["GET", "/api/status", "-", "Mengirimkan seluruh data sensor, satuan, status kondisi, sudut servo, status aktuator, IP, dan RSSI tiap 2 detik"],
            ["POST / GET", "/api/control", "mode, pump, fan, growLight, buzzer", "Menerima perintah perpindahan mode AUTO/MANUAL dan saklar kendali aktuator dari pengguna"],
            ["POST / GET", "/api/threshold", "maxTemp, minSoil, minLight", "Memperbarui nilai ambang batas otomasi greenhouse secara dinamis"],
        ],
        col_widths=[2.2, 2.8, 4.2, 6.3]
    )

    add_body_p(doc, "Contoh struktur payload JSON yang dikirimkan oleh ESP32 pada endpoint GET /api/status:", bold_prefix="")
    add_code_block(
        doc,
        '{\n'
        '  "project": "Smart Mini Greenhouse Monitoring & Control System",\n'
        '  "device": "Trainer Kit ESP32 DevKit V4 (38-Pin)",\n'
        '  "connected": true,\n'
        '  "ip": "192.168.43.105",\n'
        '  "rssi": -54,\n'
        '  "uptimeSeconds": 182,\n'
        '  "mode": "AUTO",\n'
        '  "alertLevel": "ACTIVE",\n'
        '  "systemStatus": "MENYIRAM - Tanah Kering",\n'
        '  "servoAngle": 0,\n'
        '  "sensors": { "temperature": 29.4, "humidity": 64.0, "light": 72, "soil": 32 },\n'
        '  "actuators": { "pump": true, "fan": false, "growLight": false, "buzzer": false },\n'
        '  "thresholds": { "maxTemp": 31.0, "minSoil": 40, "minLight": 35 }\n'
        '}'
    )

    # -------------------------------------------------------------------------
    # BAB V: TAMPILAN ANTARMUKA PENGGUNA (WEB DASHBOARD)
    # -------------------------------------------------------------------------
    add_chapter_heading(doc, "BAB V. TAMPILAN ANTARMUKA PENGGUNA (WEB DASHBOARD)")

    add_body_p(
        doc,
        "Antarmuka pengguna dibangun dalam bentuk aplikasi Web Dashboard responsif (web-dashboard/index.html, style.css, dan app.js) yang berjalan 100% secara offline di jaringan Wi-Fi lokal tanpa memerlukan pustaka CDN eksternal. Antarmuka dirancang untuk memenuhi seluruh persyaratan informasi wajib pada soal project akhir:"
    )
    add_bullet_p(doc, "1. Nama / Judul Project & Indikator Koneksi: ", "Bagian header menampilkan judul resmi Smart Mini Greenhouse Monitoring & Control System beserta badge indikator koneksi perangkat (TERHUBUNG KE ESP32, MODE SIMULASI, atau TERPUTUS), alamat IP ESP32, kekuatan sinyal Wi-Fi (RSSI), dan stempel waktu Pembaruan Terakhir (HH:MM:SS) yang diperbarui otomatis setiap 2 detik.")
    add_bullet_p(doc, "2. Banner Status Kondisi Sistem: ", "Menampilkan kondisi aktual sistem secara menonjol dengan kode warna adaptif: Hijau (NORMAL), Amber/Kuning (ACTIVE — Menyiram / Pendinginan / Grow Light), dan Merah (CRITICAL).")
    add_bullet_p(doc, "3. Kartu Pembacaan Sensor Beserta Satuan: ", "Menampilkan nilai terkini dari 4 parameter utama: Suhu Udara (°C), Kelembapan Udara (% RH), Intensitas Cahaya LDR (%), dan Kelembapan Media Tanam (%), lengkap dengan bilah persentase dan batas ambang.")
    add_bullet_p(doc, "4. Grafik Pemantauan Real-Time: ", "Menyajikan grafik garis multi-variabel berbasis HTML5 Canvas lokal yang merekam hingga 25 titik waktu terakhir untuk memantau tren perubahan iklim mikro.")
    add_bullet_p(doc, "5. Panel Kontrol Aktuator & Pengaturan Threshold: ", "Memungkinkan pengguna beralih antara mode AUTO dan MANUAL, menyalakan/mematikan Relay Pompa, Ventilasi/Kipas Servo, Grow Light, dan Buzzer secara langsung, serta mengubah batas suhu, tanah, dan cahaya.")
    add_bullet_p(doc, "6. Panel Simulator Demo: ", "Menyediakan 5 tombol skenario preset dan slider sensor manual pada Mode Simulasi untuk keperluan pengujian UI maupun demonstrasi cadangan.")

    # Kotak placeholder screenshot antarmuka agar mudah diisi user setelah demo live
    tbl_ss = doc.add_table(rows=1, cols=1)
    tbl_ss.alignment = WD_TABLE_ALIGNMENT.CENTER
    c_ss = tbl_ss.rows[0].cells[0]
    c_ss.width = Cm(15.5)
    set_cell_shading(c_ss, "F8FAFC")
    set_cell_margins(c_ss, top=420, bottom=420, left=200, right=200)
    p_ss = c_ss.paragraphs[0]
    p_ss.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_ss = p_ss.add_run(
        "[Tempelkan Screenshot Tampilan Web Dashboard Saat Terhubung ke ESP32 di Sini]\n"
        "(Buka web-dashboard/index.html di browser saat ESP32 menyala, lalu ambil tangkapan layar kondisi NORMAL dan KRITIS)"
    )
    r_ss.italic = True
    r_ss.font.name = "Calibri"
    r_ss.font.size = Pt(9.5)
    r_ss.font.color.rgb = RGBColor(100, 116, 139)

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # -------------------------------------------------------------------------
    # BAB VI: HASIL PENGUJIAN DAN KESIMPULAN
    # -------------------------------------------------------------------------
    add_chapter_heading(doc, "BAB VI. HASIL PENGUJIAN DAN KESIMPULAN")

    add_sub_heading(doc, "6.1 Rencana dan Tabel Hasil Pengujian Sistem")
    add_body_p(
        doc,
        "Pengujian dilakukan secara menyeluruh terhadap konektivitas jaringan lokal, respons pembacaan masing-masing sensor, ketepatan status pada antarmuka web, serta kinerja aktuator pada mode otomatis dan manual sebagaimana tercantum pada Tabel 6.1."
    )
    add_styled_table(
        doc,
        ["ID Uji", "Skenario Pengujian", "Aksi / Kondisi Masukan", "Hasil yang Diharapkan", "Hasil Aktual", "Status"],
        [
            ["TC-01", "Koneksi Wi-Fi Lokal", "ESP32 dinyalakan & dihubungkan ke Hotspot HP", "ESP32 memperoleh IP lokal dan Web Dashboard menampilkan TERHUBUNG KE ESP32", "[Isi saat demo]", "[ ] Berhasil"],
            ["TC-02", "Pembaruan Data Berkala", "Diamati 10 detik tanpa interaksi fisik", "Timestamp pembaruan & titik grafik bertambah otomatis tiap 2 detik", "[Isi saat demo]", "[ ] Berhasil"],
            ["TC-03", "Sensor LDR (Gelap)", "Sensor LDR (GPIO 39) ditutup jari hingga cahaya < 35%", "LED2 Kuning (GPIO 2) menyala, status web menjadi GROW LIGHT AKTIF", "[Isi saat demo]", "[ ] Berhasil"],
            ["TC-04", "Kelembapan Tanah & Relay", "Knop Potensiometer (GPIO 35) diputar ke nilai < 40%", "Relay (GPIO 19) berbunyi klik, LED3 Hijau (26) menyala, status MENYIRAM", "[Isi saat demo]", "[ ] Berhasil"],
            ["TC-05", "Sensor DHT11 & Servo", "Sensor DHT11 (GPIO 32) dihangatkan hingga suhu > 31.0 °C", "Servo (GPIO 23) berputar ke 90°, LED4 Biru (27) ON, status PENDINGINAN AKTIF", "[Isi saat demo]", "[ ] Berhasil"],
            ["TC-06", "Kondisi Kritis & Alarm", "Suhu > 31.0 °C dan kelembapan tanah < 40% bersamaan", "Banner web merah (KRITIS), LED1 Merah (4) ON, Buzzer (13) berbunyi beep", "[Isi saat demo]", "[ ] Berhasil"],
            ["TC-07", "Kontrol Manual Web & Tombol", "Ubah ke mode MANUAL, klik tombol Web atau tekan Button2–4", "Relay, Servo, LED2, & Buzzer merespons perintah pengguna secara langsung", "[Isi saat demo]", "[ ] Berhasil"],
        ],
        col_widths=[1.3, 2.7, 3.3, 4.1, 2.3, 1.8]
    )

    add_sub_heading(doc, "6.2 Kesimpulan dan Saran Pengembangan")
    add_body_p(doc, "Berdasarkan perancangan, implementasi kode, dan analisis sistem yang telah dilakukan, dapat disimpulkan bahwa:")
    add_bullet_p(doc, "1. ", "Sistem Smart Mini Greenhouse Monitoring & Control System berhasil dirancang di atas papan All-in-One Trainer Kit ESP32 DevKitC V4 (38-Pin) dengan memanfaatkan sensor DHT11, LDR, dan Potensiometer (serta opsi Soil Moisture eksternal) secara terintegrasi.")
    add_bullet_p(doc, "2. ", "Komunikasi data melalui jaringan Wi-Fi lokal menggunakan protokol HTTP REST API JSON memungkinkan Web Dashboard menampilkan nilai sensor beserta satuan, status kondisi sistem, grafik real-time, dan waktu pembaruan terakhir secara otomatis setiap 2 detik tanpa bergantung pada koneksi internet.")
    add_bullet_p(doc, "3. ", "Mekanisme kendali aktuator (Relay Pompa Air, Motor Servo Ventilasi, LED Grow Light, dan Buzzer) berjalan efektif baik secara otomatis (AUTO) berdasarkan ambang batas maupun secara manual (MANUAL) melalui antarmuka web dan 4 tombol fisik onboard.")

    add_body_p(
        doc,
        "Untuk pengembangan lebih lanjut, komponen cadangan yang sudah tersedia pada papan Trainer Kit ESP32 V4 seperti layar OLED 0.96\" I2C (SDA 21, SCL 22) dan sensor ultrasonik HC-SR04 dapat diaktifkan guna menampilkan alamat IP langsung pada alat serta memantau ketersediaan air pada tandon irigasi.",
        bold_prefix="Saran Pengembangan: "
    )

    # -------------------------------------------------------------------------
    # LAMPIRAN: STRUKTUR PROJECT & CUPLIKAN KODE PROGRAM
    # -------------------------------------------------------------------------
    doc.add_page_break()
    add_chapter_heading(doc, "LAMPIRAN. STRUKTUR PROJECT & CUPLIKAN KODE PROGRAM")

    add_sub_heading(doc, "L.1 Struktur Direktori Berkas Project")
    add_code_block(
        doc,
        "Project_IoT_2/\n"
        "├── firmware/\n"
        "│   └── smart_greenhouse_esp32/\n"
        "│       └── smart_greenhouse_esp32.ino   # Program ESP32 + Web Server + REST API\n"
        "├── web-dashboard/\n"
        "│   ├── index.html                       # Halaman Antarmuka Web Dashboard\n"
        "│   ├── style.css                        # Desain Responsif Tema Greenhouse\n"
        "│   └── app.js                           # Polling API 2s, Grafik Canvas & Simulator\n"
        "├── docs/\n"
        "│   ├── assets/                          # Foto PCB & Gambar Diagram Laporan\n"
        "│   ├── PANDUAN_BOARD_DAN_PINOUT.md      # Panduan Pinout PCB & Upload Arduino IDE\n"
        "│   ├── PRD_SMART_GREENHOUSE.md          # Product Requirements Document (PRD)\n"
        "│   ├── DRAFT_LAPORAN_UAS.md             # Draft Laporan Versi Markdown\n"
        "│   └── Laporan_Project_Akhir_IoT_Smart_Greenhouse.docx\n"
        "└── README.md"
    )

    add_sub_heading(doc, "L.2 Cuplikan Konfigurasi Pinout & Logika Kontrol (smart_greenhouse_esp32.ino)")
    add_code_block(
        doc,
        "// Konfigurasi Pin GPIO Sesuai PCB Trainer Kit ESP32 V4\n"
        "#define PIN_DHT           32   // Sensor DHT11 (Suhu & Kelembapan Udara)\n"
        "#define PIN_LDR           39   // Sensor Cahaya LDR (ADC1)\n"
        "#define PIN_POT_SOIL      35   // Potensiometer / Input Tanah (ADC1)\n"
        "#define PIN_RELAY         19   // Relay Biru Onboard -> Pompa Air Irigasi\n"
        "#define PIN_SERVO         23   // Motor Servo SG90 -> Ventilasi Atap\n"
        "#define PIN_BUZZER        13   // Buzzer Onboard -> Alarm Kritis\n"
        "#define PIN_LED1_RED      4    // LED1 Merah  -> Indikator Alarm Kritis\n"
        "#define PIN_LED2_YELLOW   2    // LED2 Kuning -> Lampu Grow Light\n"
        "#define PIN_LED3_GREEN    26   // LED3 Hijau  -> Indikator Pompa Air\n"
        "#define PIN_LED4_BLUE     27   // LED4 Biru   -> Indikator Ventilasi Servo\n"
        "#define PIN_BTN1_MODE     33   // Button1 (Merah)  -> Mode AUTO / MANUAL\n"
        "#define PIN_BTN2_GROW     25   // Button2 (Kuning) -> Toggle Grow Light\n"
        "#define PIN_BTN3_PUMP     14   // Button3 (Hijau)  -> Toggle Pompa Relay\n"
        "#define PIN_BTN4_FAN      12   // Button4 (Biru)   -> Toggle Ventilasi Servo\n\n"
        "void evaluateSystemLogic() {\n"
        "  bool highTemp   = (temperatureC > threshMaxTemp);\n"
        "  bool drySoil    = (soilMoisture < threshMinSoil);\n"
        "  bool lowLight   = (lightPercent < threshMinLight);\n"
        "  bool severeTemp = (temperatureC >= (threshMaxTemp + 2.0));\n\n"
        "  if (isAutoMode) {\n"
        "    growLightState = lowLight;\n"
        "    fanState       = highTemp;\n"
        "    pumpState      = drySoil;\n"
        "    buzzerState    = (severeTemp || (highTemp && drySoil));\n"
        "  }\n"
        "  applyHardwareOutputs();\n"
        "}"
    )

    doc.save(OUTPUT_DOCX_PATH)
    print(f"[OK] Laporan Word berhasil dibuat: {OUTPUT_DOCX_PATH}")


if __name__ == "__main__":
    normalize_board_photo()
    generate_block_diagram()
    generate_flowchart()
    build_report_docx()
