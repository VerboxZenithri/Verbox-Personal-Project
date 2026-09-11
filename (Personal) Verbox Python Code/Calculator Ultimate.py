import pygame
import math
import sys
import json
import os
import time

pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)

# ─── FULLSCREEN SUPPORT ──────────────────────────────────────────────────────
LEBAR_BASE  = 1100
TINGGI_BASE = 720
FPS = 85

_fullscreen = False
_win_size   = (LEBAR_BASE, TINGGI_BASE)

def _make_window():
    global layar, LEBAR, TINGGI, _fullscreen
    flags = pygame.FULLSCREEN | pygame.SCALED if _fullscreen else 0
    layar = pygame.display.set_mode(_win_size, flags)
    LEBAR, TINGGI = layar.get_size()

LEBAR  = LEBAR_BASE
TINGGI = TINGGI_BASE
layar  = pygame.display.set_mode((LEBAR, TINGGI))
pygame.display.set_caption("Calculator Ultimate")
clock = pygame.time.Clock()

def toggle_fullscreen():
    global _fullscreen
    _fullscreen = not _fullscreen
    _make_window()

# ─── COLOURS ────────────────────────────────────────────────────────────────
BG_DARK        = (15, 5, 30)
UNGU_GELAP     = (40, 20, 60)
UNGU_CARD      = (30, 15, 55)
UNGU_SEDANG    = (80, 50, 120)
UNGU_TERANG    = (130, 90, 180)
UNGU_NEON      = (180, 100, 255)
UNGU_GLOW      = (120, 60, 200)
CYAN_ACCENT    = (100, 220, 255)
MAGENTA_ACCENT = (220, 80, 255)
PUTIH          = (255, 255, 255)
ABU            = (180, 180, 180)
HIJAU          = (80, 255, 150)
MERAH          = (255, 80, 80)
KUNING         = (255, 220, 60)
EMAS           = (255, 200, 40)
OVERLAY_BG     = (0, 0, 0)

# ─── FONTS ───────────────────────────────────────────────────────────────────
font_judul  = pygame.font.Font(None, 80)
font_besar  = pygame.font.Font(None, 44)
font_sedang = pygame.font.Font(None, 32)
font_kecil  = pygame.font.Font(None, 24)
font_micro  = pygame.font.Font(None, 20)

# ─── SOUND GENERATOR ────────────────────────────────────────────────────────
def _gen_click_sound():
    sr = 44100; dur = 0.04; n = int(sr * dur)
    buf = bytearray(n * 2)
    for i in range(n):
        t2 = i / sr
        freq = 1200 + 800 * math.exp(-t2 * 60)
        vol  = 0.35 * math.exp(-t2 * 80)
        s    = int(vol * 32767 * math.sin(2 * math.pi * freq * t2))
        s    = max(-32768, min(32767, s))
        buf[i*2]     = s & 0xFF
        buf[i*2 + 1] = (s >> 8) & 0xFF
    snd = pygame.sndarray.make_sound(
        pygame.Surface.__new__(pygame.Surface))
    arr = pygame.sndarray.make_sound(
        pygame.surfarray.map_array(
            pygame.Surface((1,1)), [[0]]))
    # simpler approach
    import array as _arr
    samples = _arr.array('h', [0] * n)
    for i in range(n):
        t2 = i / sr
        freq = 1200 + 800 * math.exp(-t2 * 60)
        vol  = 0.35 * math.exp(-t2 * 80)
        samples[i] = int(vol * 32767 * math.sin(2 * math.pi * freq * t2))
    return pygame.sndarray.make_sound(
        pygame.surfarray.make_surface([[c] for c in samples[:1]]))  # fallback

_click_sound = None

def _build_click():
    global _click_sound
    try:
        sr = 44100; dur = 0.04; n = int(sr * dur)
        import numpy as np
        t  = np.linspace(0, dur, n, False)
        fr = 1200 + 800 * np.exp(-t * 60)
        ph = np.cumsum(fr) / sr
        wave = (0.35 * np.exp(-t * 80) * np.sin(2 * np.pi * ph))
        samples = (wave * 32767).astype(np.int16)
        stereo  = np.column_stack([samples, samples])
        _click_sound = pygame.sndarray.make_sound(stereo)
    except Exception:
        _click_sound = None

_build_click()

def play_click():
    if _click_sound:
        try: _click_sound.play()
        except: pass

# ─── PERSISTENCE: HISTORY & FAVOURITES ───────────────────────────────────────
_DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "calc_data.json")

def _load_data():
    try:
        with open(_DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"history": [], "favourites": []}

def _save_data(d):
    try:
        with open(_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

_app_data = _load_data()

def add_history(module_name: str, inputs_dict: dict, result: str):
    entry = {
        "ts": time.strftime("%H:%M %d/%m"),
        "module": module_name,
        "inputs": inputs_dict,
        "result": result,
    }
    _app_data["history"].insert(0, entry)
    _app_data["history"] = _app_data["history"][:50]
    _save_data(_app_data)

def toggle_favourite(idx: int):
    favs = _app_data["favourites"]
    if idx in favs:
        favs.remove(idx)
    else:
        favs.append(idx)
    _save_data(_app_data)

def is_favourite(idx: int) -> bool:
    return idx in _app_data["favourites"]

# ─── CLIPBOARD ───────────────────────────────────────────────────────────────
def copy_to_clipboard(text: str):
    try:
        pygame.scrap.init()
        pygame.scrap.put(pygame.SCRAP_TEXT, text.encode())
    except Exception:
        pass

# ─── TOOLTIP / INFO DATA ─────────────────────────────────────────────────────
MODULE_INFO = {
    "Operasi Dasar":     "Penjumlahan, pengurangan, perkalian, pembagian, modulus, dan perpangkatan dua bilangan.",
    "Pangkat & Akar":    "Menghitung x², x³, √x, akar-n, dan x^n untuk sembarang bilangan.",
    "Trigonometri":      "sin, cos, tan, sec, csc, cot — input dalam derajat, output desimal.",
    "Logaritma":         "log₁₀(x), ln(x) (log natural), dan logₙ(x) dengan basis sembarang.",
    "Faktorial & Komb.": "n! (faktorial), nPr (permutasi), nCr (kombinasi). Rumus: nCr = n! / (r!(n-r)!)",
    "Persamaan Kuadrat": "ax²+bx+c=0. Solusi: x = (-b ± √(b²-4ac)) / 2a. Diskriminan: D = b²-4ac.",
    "Konversi Suhu":     "Celsius, Fahrenheit, Kelvin, Rankine, Réaumur — konversi antar semua satuan.",
    "Konversi Panjang":  "mm, cm, dm, m, km, inci, kaki, yard, mil — berbasis 1 meter.",
    "Konversi Berat":    "mg, g, kg, ton, lb, oz, stone, karat — berbasis 1 gram.",
    "Sistem Bilangan":   "Konversi antara Desimal, Biner (2), Oktal (8), dan Heksadesimal (16).",
    "Statistik":         "Hitung N, Mean, Median, Variansi, Std Dev, Min, Max dari sekumpulan data.",
    "Matrix 2x2":        "Penjumlahan A+B, perkalian A×B, dan determinan Det(A) = ad-bc untuk matrix 2×2.",
    "Bilangan Prima":    "Cek apakah sebuah bilangan prima, atau tampilkan semua prima hingga batas N.",
    "FPB & KPK":         "FPB (faktor persekutuan terbesar) dan KPK (kelipatan persekutuan terkecil) dua bilangan.",
    "Pythagoras":        "Hitung sisi miring c = √(a²+b²) dari dua sisi siku-siku yang diketahui.",
    "Luas Bangun":       "Luas 10 bangun datar: persegi, segitiga, lingkaran, trapesium, dll.",
    "Volume Bangun":     "Volume 8 bangun ruang: kubus, balok, tabung, kerucut, bola, dll.",
    "Pecahan":           "Operasi penjumlahan, pengurangan, perkalian, pembagian dua pecahan a/b dan c/d.",
    "Persentase":        "Hitung persentase, nilai dari total, atau selisih persentase.",
    "Diskon & Pajak":    "Hitung harga setelah diskon atau total setelah pajak ditambahkan.",
    "Bunga Sederhana":   "I = P × r × t / 100. Menghitung bunga dan total akhir modal.",
    "Fibonacci":         "Deret Fibonacci hingga n suku: 0, 1, 1, 2, 3, 5, 8, 13...",
    "Barisan Aritmatika":"Un = a + (n-1)b. Sn = n/2 × (2a + (n-1)b). Diketahui a dan b.",
    "Aritmatika Lanjutan":"Temukan a dan b dari dua suku sembarang, lalu hitung Un dan Sn.",
    "Barisan Geometri":  "Un = a × rⁿ⁻¹. Sn = a(1-rⁿ)/(1-r). Diketahui a dan rasio r.",
    "Kecepatan & Jarak": "v = s/t, s = v×t, t = s/v. Kalkulator gerak lurus beraturan.",
    "BMI Calculator":    "Body Mass Index = Berat(kg) / Tinggi²(m). Kategori: Kurus < 18.5 < Normal < 25 < Overweight.",
    "Konversi Waktu":    "ms, detik, menit, jam, hari, minggu, bulan, tahun — berbasis 1 detik.",
    "Konversi Data":     "bit, byte, KB, MB, GB, TB, PB — berbasis 1 bit digital.",
    "Bilangan Kompleks": "Operasi bilangan kompleks z = a+bi: penjumlahan, pengurangan, perkalian.",
    "Determinan 3x3":    "Det(A) untuk matrix 3×3 menggunakan ekspansi kofaktor baris pertama.",
}

# ─── HELPERS ─────────────────────────────────────────────────────────────────
def draw_bg(surface):
    surface.fill(BG_DARK)
    for y in range(0, TINGGI, 30):
        pygame.draw.line(surface, (25, 10, 45), (0, y), (LEBAR, y), 1)
    for x in range(0, LEBAR, 40):
        pygame.draw.line(surface, (25, 10, 45), (x, 0), (x, TINGGI), 1)

def draw_watermark(surface):
    wm = font_micro.render("Made By: Dyles Enserval Verbox", True, (90, 60, 130))
    surface.blit(wm, (LEBAR - wm.get_width() - 15, TINGGI - wm.get_height() - 8))

def draw_gradient_title(surface, text, x, y):
    shadow = font_judul.render(text, True, (60, 20, 100))
    surface.blit(shadow, (x - shadow.get_width()//2 + 3, y - shadow.get_height()//2 + 3))
    chars = list(text); total = len(chars)
    cx = x - font_judul.size(text)[0]//2
    for i, ch in enumerate(chars):
        ratio = i / (total - 1) if total > 1 else 0
        r = int(CYAN_ACCENT[0]*(1-ratio) + MAGENTA_ACCENT[0]*ratio)
        g = int(CYAN_ACCENT[1]*(1-ratio) + MAGENTA_ACCENT[1]*ratio)
        b = int(CYAN_ACCENT[2]*(1-ratio) + MAGENTA_ACCENT[2]*ratio)
        r = int(r*0.7 + UNGU_NEON[0]*0.3)
        g = int(g*0.7 + UNGU_NEON[1]*0.3)
        b = int(b*0.7 + UNGU_NEON[2]*0.3)
        surf = font_judul.render(ch, True, (r, g, b))
        surface.blit(surf, (cx, y - surf.get_height()//2))
        cx += surf.get_width()

def draw_scene_header(surface, title):
    pygame.draw.rect(surface, UNGU_CARD, (0, 0, LEBAR, 75))
    pygame.draw.rect(surface, UNGU_NEON, (0, 73, LEBAR, 2))
    sh = font_besar.render(title, True, (60, 20, 100))
    surface.blit(sh, (LEBAR//2 - sh.get_width()//2 + 2, 22))
    txt = font_besar.render(title, True, UNGU_NEON)
    surface.blit(txt, (LEBAR//2 - txt.get_width()//2, 20))
    draw_watermark(surface)

def render_text(text, font, color, x, y, center=False):
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=(x, y)) if center else surf.get_rect(topleft=(x, y))
    layar.blit(surf, rect)

def wrap_text(text, font, max_width):
    if not text:
        return ['']
    words = text.split(' ')
    lines = []; current = ''
    for word in words:
        test = (current + ' ' + word).strip()
        if font.size(test)[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines if lines else ['']

def draw_hasil_box(surface, hasil, y, is_list=False):
    """Draw result box; returns a (y_bottom, result_text) tuple."""
    if not hasil:
        return y
    box_x = 50; box_w = LEBAR - 100; max_tw = box_w - 40
    line_h = 28; pad = 12
    max_h = max(40, TINGGI - y - 88)

    full_text = ""

    if is_list:
        all_lines = []
        for item in hasil:
            all_lines.extend(wrap_text(item, font_kecil, max_tw))
        full_text = "\n".join(hasil) if isinstance(hasil, list) else hasil
        max_visible = (max_h - pad*2) // line_h
        shown = all_lines[:max(1, max_visible)]
        bh = len(shown)*line_h + pad*2
        pygame.draw.rect(surface, (15, 8, 35), (box_x, y, box_w, bh), border_radius=10)
        pygame.draw.rect(surface, UNGU_NEON,   (box_x, y, box_w, bh), 2, border_radius=10)
        for i, line in enumerate(shown):
            c = MERAH if "ERROR" in line else HIJAU
            render_text(line, font_kecil, c, LEBAR//2, y + pad + i*line_h + line_h//2, center=True)
        if len(all_lines) > len(shown):
            more = font_micro.render(f"  ▼ +{len(all_lines)-len(shown)} baris tersembunyi", True, ABU)
            surface.blit(more, (box_x + 10, y + bh - 17))
    else:
        full_text = hasil
        wrapped = wrap_text(hasil, font_sedang, max_tw)
        max_visible = (max_h - pad*2) // line_h
        shown = wrapped[:max(1, max_visible)]
        bh = len(shown)*line_h + pad*2
        pygame.draw.rect(surface, (15, 8, 35), (box_x, y, box_w, bh), border_radius=10)
        pygame.draw.rect(surface, UNGU_NEON,   (box_x, y, box_w, bh), 2, border_radius=10)
        c = MERAH if "ERROR" in hasil else HIJAU
        for i, line in enumerate(shown):
            render_text(line, font_sedang, c, LEBAR//2, y + pad + i*line_h + line_h//2, center=True)

    # Copy button
    copy_btn_rect = pygame.Rect(box_x + box_w - 80, y + 6, 72, 26)
    pygame.draw.rect(surface, UNGU_SEDANG, copy_btn_rect, border_radius=5)
    pygame.draw.rect(surface, CYAN_ACCENT, copy_btn_rect, 1, border_radius=5)
    ct = font_micro.render("⎘ Copy", True, CYAN_ACCENT)
    surface.blit(ct, (copy_btn_rect.x + 8, copy_btn_rect.y + 5))

    return y + bh, copy_btn_rect, full_text

def fmt(n):
    if n == 0: return "0"
    if abs(n) >= 1e13 or (abs(n) < 1e-7 and abs(n) > 0):
        return f"{n:.4e}"
    if n == int(n) and abs(n) < 1e12:
        return str(int(n))
    return f"{n:.8g}"

# ─── SHAPE DRAWING ───────────────────────────────────────────────────────────
def _label(surface, text, x, y, color=None):
    if color is None: color = UNGU_NEON
    font = pygame.font.Font(None, 22)
    surf = font.render(text, True, color)
    surface.blit(surf, (x - surf.get_width()//2, y - surf.get_height()//2))

def _dashed_line(surface, color, start, end, dash=8, gap=4, width=1):
    x0, y0 = start; x1, y1 = end
    dx = x1 - x0; dy = y1 - y0
    length = max(1, math.hypot(dx, dy))
    nx = dx/length; ny = dy/length
    d = 0
    while d < length:
        d2 = min(d + dash, length)
        pygame.draw.line(surface, color,
                         (int(x0+nx*d), int(y0+ny*d)),
                         (int(x0+nx*d2), int(y0+ny*d2)), width)
        d += dash + gap

def _tick(surface, x, y, horizontal=True, color=None, size=6):
    if color is None: color = UNGU_NEON
    if horizontal:
        pygame.draw.line(surface, color, (x-size, y-size), (x+size, y+size), 1)
        pygame.draw.line(surface, color, (x-size+3, y-size), (x+size+3, y+size), 1)
    else:
        pygame.draw.line(surface, color, (x-size, y-size), (x+size, y+size), 1)
        pygame.draw.line(surface, color, (x-size, y-size+3), (x+size, y+size+3), 1)

def draw_shape_preview(surface, shape_name, rect):
    """Draw 2-D shape preview using pygame.draw — no ASCII art."""
    # clip to prevent overflow
    surface.set_clip(rect)

    cx = rect.centerx; cy = rect.centery
    w  = rect.width  - 40; h = rect.height - 40
    col = CYAN_ACCENT; col2 = UNGU_NEON; lw = 2
    name = shape_name.lower()

    if "persegi pjg" in name or "persegi panjang" in name:
        pw = int(w * 0.75); ph = int(h * 0.50)
        r  = pygame.Rect(cx - pw//2, cy - ph//2, pw, ph)
        pygame.draw.rect(surface, col, r, lw, border_radius=3)
        _label(surface, "p", cx, r.top - 10)
        _label(surface, "l", r.right + 12, cy)

    elif "persegi" in name:
        sw = int(min(w, h) * 0.65)
        r  = pygame.Rect(cx - sw//2, cy - sw//2, sw, sw)
        pygame.draw.rect(surface, col, r, lw, border_radius=3)
        _tick(surface, r.centerx, r.top, horizontal=True, color=col2)
        _tick(surface, r.centerx, r.bottom, horizontal=True, color=col2)
        _tick(surface, r.left, r.centery, horizontal=False, color=col2)
        _tick(surface, r.right, r.centery, horizontal=False, color=col2)
        _label(surface, "s", r.right + 12, cy)

    elif "segitiga" in name:
        bw2 = int(w * 0.38); th = int(h * 0.65)
        pts = [(cx, cy - th//2), (cx - bw2, cy + th//2), (cx + bw2, cy + th//2)]
        pygame.draw.polygon(surface, col, pts, lw)
        _dashed_line(surface, col2, (cx, cy - th//2), (cx, cy + th//2), dash=6)
        _label(surface, "a", cx, cy + th//2 + 12)
        _label(surface, "t", cx + 10, cy)

    elif "lingkaran" in name:
        r = int(min(w, h) * 0.35)
        pygame.draw.circle(surface, col, (cx, cy), r, lw)
        pygame.draw.line(surface, col2, (cx, cy), (cx + r, cy), lw)
        pygame.draw.circle(surface, col2, (cx, cy), 3)
        _label(surface, "r", cx + r//2, cy - 12)

    elif "trapesium" in name:
        ab = int(w * 0.72); at = int(w * 0.44); th = int(h * 0.55)
        pts = [(cx-at//2, cy-th//2), (cx+at//2, cy-th//2),
               (cx+ab//2, cy+th//2), (cx-ab//2, cy+th//2)]
        pygame.draw.polygon(surface, col, pts, lw)
        _dashed_line(surface, col2, (cx-at//2, cy-th//2), (cx-ab//2, cy+th//2), dash=5)
        _label(surface, "b", cx, cy - th//2 - 12)
        _label(surface, "a", cx, cy + th//2 + 12)
        _label(surface, "t", cx + ab//2 + 14, cy)

    elif "jajar" in name:
        # FIX: constrain so shape stays inside box
        pw  = int(w * 0.60)
        ph  = int(h * 0.45)
        off = int(pw * 0.25)
        # shift center left so right edge doesn't overflow
        ox  = cx - off//2
        pts = [(ox - pw//2 + off, cy - ph//2),
               (ox + pw//2,       cy - ph//2),
               (ox + pw//2 - off, cy + ph//2),
               (ox - pw//2,       cy + ph//2)]
        pygame.draw.polygon(surface, col, pts, lw)
        _dashed_line(surface, col2,
                     (ox - pw//2 + off, cy - ph//2),
                     (ox - pw//2 + off, cy + ph//2), dash=5)
        _label(surface, "a", ox, cy + ph//2 + 12)
        _label(surface, "t", ox - pw//2 + off - 16, cy)

    elif "ketupat" in name:
        d1h = int(h * 0.40); d2h = int(w * 0.32)
        pts = [(cx, cy-d1h), (cx+d2h, cy), (cx, cy+d1h), (cx-d2h, cy)]
        pygame.draw.polygon(surface, col, pts, lw)
        _dashed_line(surface, col2, (cx-d2h, cy), (cx+d2h, cy), dash=5)
        _dashed_line(surface, col2, (cx, cy-d1h), (cx, cy+d1h), dash=5)
        _label(surface, "d1", cx + d2h + 8, cy)
        _label(surface, "d2", cx, cy - d1h - 14)

    elif "layang" in name:
        d1h_top = int(h * 0.27); d1h_bot = int(h * 0.42); d2h = int(w * 0.30)
        pts = [(cx, cy-d1h_top), (cx+d2h, cy), (cx, cy+d1h_bot), (cx-d2h, cy)]
        pygame.draw.polygon(surface, col, pts, lw)
        _dashed_line(surface, col2, (cx-d2h, cy), (cx+d2h, cy), dash=5)
        _dashed_line(surface, col2, (cx, cy-d1h_top), (cx, cy+d1h_bot), dash=5)
        _label(surface, "d1", cx + d2h + 8, cy)
        _label(surface, "d2", cx, cy - d1h_top - 14)

    elif "elips" in name:
        rx = int(w * 0.38); ry = int(h * 0.30)
        pygame.draw.ellipse(surface, col, pygame.Rect(cx-rx, cy-ry, rx*2, ry*2), lw)
        pygame.draw.line(surface, col2, (cx, cy), (cx+rx, cy), lw)
        pygame.draw.line(surface, col2, (cx, cy), (cx, cy-ry), lw)
        pygame.draw.circle(surface, col2, (cx, cy), 3)
        _label(surface, "a", cx + rx//2, cy - 12)
        _label(surface, "b", cx + 8,     cy - ry//2)

    elif "segi" in name or "heksa" in name:
        r = int(min(w, h) * 0.36)
        pts = []
        for k in range(6):
            angle = math.radians(60*k - 30)
            pts.append((int(cx + r*math.cos(angle)), int(cy + r*math.sin(angle))))
        pygame.draw.polygon(surface, col, pts, lw)
        pygame.draw.line(surface, col2, pts[0], pts[1], lw+1)
        _label(surface, "s", (pts[0][0]+pts[1][0])//2 + 8, (pts[0][1]+pts[1][1])//2 - 8)

    else:
        _label(surface, "?", cx, cy, color=ABU)

    surface.set_clip(None)

# ─── UI CLASSES ──────────────────────────────────────────────────────────────
class Button:
    def __init__(self, x, y, w, h, text, color=(80,50,120), hover=(130,90,180), font=None):
        self.rect       = pygame.Rect(x, y, w, h)
        self.text       = text
        self.base_color = color; self.hover_color = hover
        self.hovered    = False; self.active = False
        self.font       = font or font_kecil
    def draw(self, surface):
        c  = (50,160,200) if self.active else (self.hover_color if self.hovered else self.base_color)
        bc = PUTIH if self.active else (CYAN_ACCENT if self.hovered else UNGU_NEON)
        pygame.draw.rect(surface, c,  self.rect, border_radius=8)
        pygame.draw.rect(surface, bc, self.rect, 2, border_radius=8)
        if self.active or self.hovered:
            pygame.draw.rect(surface, bc,
                pygame.Rect(self.rect.x+2, self.rect.y+1, self.rect.w-4, 2), border_radius=2)
        tc  = BG_DARK if self.active else PUTIH
        txt = self.font.render(self.text, True, tc)
        surface.blit(txt, (self.rect.centerx - txt.get_width()//2,
                           self.rect.centery - txt.get_height()//2))
    def check_hover(self, pos): self.hovered = self.rect.collidepoint(pos)
    def clicked(self, pos, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(pos):
            play_click()
            return True
        return False

class InputBox:
    def __init__(self, x, y, w, h, label=""):
        self.rect   = pygame.Rect(x, y, w, h)
        self.text   = ""; self.active = False; self.label = label
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                return True
            elif len(self.text) < 30:
                self.text += event.unicode
        return False
    def draw(self, surface):
        if self.label:
            lbl = font_kecil.render(self.label, True, ABU)
            surface.blit(lbl, (self.rect.x, self.rect.y - 22))
        bc  = CYAN_ACCENT if self.active else UNGU_NEON
        pygame.draw.rect(surface, (20, 10, 40), self.rect, border_radius=6)
        pygame.draw.rect(surface, bc, self.rect, 2, border_radius=6)
        txt = font_kecil.render(self.text, True, PUTIH)
        surface.blit(txt, (self.rect.x + 8, self.rect.centery - txt.get_height()//2))
        if self.active:
            cx = self.rect.x + 8 + txt.get_width() + 2
            pygame.draw.line(surface, CYAN_ACCENT, (cx, self.rect.centery-8), (cx, self.rect.centery+8), 2)

class Scrollbar:
    def __init__(self, x, y, w, h):
        self.x = x; self.y = y; self.w = w; self.h = h
        self.track = pygame.Rect(x, y, w, h)
        self.thumb = pygame.Rect(x, y, w, 50)
        self.dragging = False; self.drag_off = 0
    def update(self, total, visible, offset, item_h=123):
        if total <= visible: return offset
        ratio       = visible / total
        self.thumb.h = max(30, int(self.h * ratio))
        max_s        = (total - visible) * item_h
        if max_s > 0:
            r = offset / max_s
            self.thumb.y = int(self.y + r * (self.h - self.thumb.h))
        return offset
    def handle(self, event, pos, total, visible, offset, item_h=123):
        if total <= visible: return offset
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.thumb.collidepoint(pos):
                self.dragging = True; self.drag_off = pos[1] - self.thumb.y
            elif self.track.collidepoint(pos):
                r     = (pos[1] - self.y) / self.h
                max_s = (total - visible) * item_h
                offset = max(0, min(max_s, int(r * max_s)))
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            ny    = max(self.y, min(pos[1] - self.drag_off, self.y + self.h - self.thumb.h))
            r     = (ny - self.y) / (self.h - self.thumb.h) if self.h != self.thumb.h else 0
            max_s = (total - visible) * item_h
            offset = max(0, min(max_s, int(r * max_s)))
        return offset
    def draw(self, surface):
        pygame.draw.rect(surface, (40, 40, 40),  self.track, border_radius=5)
        pygame.draw.rect(surface, UNGU_GELAP,    self.track, 1, border_radius=5)
        pygame.draw.rect(surface, UNGU_SEDANG,   self.thumb, border_radius=5)
        pygame.draw.rect(surface, CYAN_ACCENT,   self.thumb, 2, border_radius=5)

# ─── TOOLTIP OVERLAY ─────────────────────────────────────────────────────────
def show_tooltip_overlay(module_name: str):
    """Blocking overlay with module info. Press any key / click to dismiss."""
    info  = MODULE_INFO.get(module_name, "Tidak ada informasi tersedia.")
    lines = wrap_text(info, font_kecil, 560)
    bh    = len(lines) * 26 + 80
    bw    = 600
    bx    = LEBAR//2 - bw//2
    by    = TINGGI//2 - bh//2
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                return
        # dim overlay
        dim = pygame.Surface((LEBAR, TINGGI), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 180))
        layar.blit(dim, (0, 0))
        pygame.draw.rect(layar, (20, 10, 45), (bx, by, bw, bh), border_radius=14)
        pygame.draw.rect(layar, CYAN_ACCENT,  (bx, by, bw, bh), 2, border_radius=14)
        title_s = font_sedang.render(f"ℹ  {module_name}", True, CYAN_ACCENT)
        layar.blit(title_s, (bx + 20, by + 16))
        pygame.draw.line(layar, UNGU_NEON, (bx + 16, by + 46), (bx + bw - 16, by + 46), 1)
        for i, line in enumerate(lines):
            ls = font_kecil.render(line, True, ABU)
            layar.blit(ls, (bx + 20, by + 56 + i * 26))
        hint = font_micro.render("Klik atau tekan tombol apa saja untuk tutup", True, UNGU_SEDANG)
        layar.blit(hint, (bx + bw//2 - hint.get_width()//2, by + bh - 24))
        pygame.display.flip(); clock.tick(FPS)

# ─── HISTORY OVERLAY ─────────────────────────────────────────────────────────
def show_history_overlay():
    """Show calculation history panel."""
    bw = 700; bh = 500; bx = LEBAR//2 - bw//2; by = TINGGI//2 - bh//2
    scroll = 0; item_h = 72
    while True:
        pos = pygame.mouse.get_pos()
        history = _app_data["history"]
        max_scroll = max(0, len(history)*item_h - (bh - 80))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: return
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and not pygame.Rect(bx,by,bw,bh).collidepoint(pos):
                    return
                if event.button == 4: scroll = max(0, scroll - 30)
                if event.button == 5: scroll = min(max_scroll, scroll + 30)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                return

        dim = pygame.Surface((LEBAR, TINGGI), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 180))
        layar.blit(dim, (0, 0))
        pygame.draw.rect(layar, (18, 8, 40), (bx, by, bw, bh), border_radius=14)
        pygame.draw.rect(layar, UNGU_NEON,   (bx, by, bw, bh), 2, border_radius=14)

        title_s = font_sedang.render("📋  Riwayat Perhitungan", True, CYAN_ACCENT)
        layar.blit(title_s, (bx + 20, by + 14))
        pygame.draw.line(layar, UNGU_NEON, (bx+16, by+46), (bx+bw-16, by+46), 1)

        clip_rect = pygame.Rect(bx + 4, by + 50, bw - 8, bh - 60)
        layar.set_clip(clip_rect)

        if not history:
            ns = font_kecil.render("Belum ada riwayat perhitungan.", True, ABU)
            layar.blit(ns, (bx + 20, by + 70))
        else:
            for i, entry in enumerate(history):
                iy = by + 54 + i*item_h - scroll
                if iy + item_h < clip_rect.top or iy > clip_rect.bottom:
                    continue
                row_rect = pygame.Rect(bx + 10, iy, bw - 20, item_h - 4)
                pygame.draw.rect(layar, UNGU_CARD, row_rect, border_radius=8)
                pygame.draw.rect(layar, UNGU_GLOW, row_rect, 1, border_radius=8)
                ts_s  = font_micro.render(entry.get("ts",""), True, ABU)
                mod_s = font_kecil.render(f"[{entry.get('module','')}]", True, UNGU_NEON)
                res_s = font_kecil.render(entry.get("result","")[:80], True, HIJAU)
                layar.blit(ts_s,  (bx + 20, iy + 6))
                layar.blit(mod_s, (bx + 20 + ts_s.get_width() + 10, iy + 4))
                layar.blit(res_s, (bx + 20, iy + 30))

        layar.set_clip(None)
        hint = font_micro.render("Klik di luar / ESC untuk tutup  •  Scroll untuk gulir", True, UNGU_SEDANG)
        layar.blit(hint, (bx + bw//2 - hint.get_width()//2, by + bh - 22))
        pygame.display.flip(); clock.tick(FPS)

# ─── MENU CARD (with star + info button) ─────────────────────────────────────
class MenuCard:
    def __init__(self, x, y, w, h, num, label, idx):
        self.rect    = pygame.Rect(x, y, w, h)
        self.num     = num; self.label = label; self.idx = idx
        self.hovered = False
        self._star_r = pygame.Rect(x + w - 28, y + 4, 22, 22)
        self._info_r = pygame.Rect(x + w - 54, y + 4, 22, 22)
    def draw(self, surface):
        fav = is_favourite(self.idx)
        bg  = UNGU_SEDANG if self.hovered else UNGU_CARD
        bc  = EMAS if fav else (CYAN_ACCENT if self.hovered else UNGU_GLOW)
        pygame.draw.rect(surface, bg, self.rect, border_radius=10)
        pygame.draw.rect(surface, bc, self.rect, 2, border_radius=10)
        if self.hovered:
            pygame.draw.rect(surface, CYAN_ACCENT,
                pygame.Rect(self.rect.x+3, self.rect.y+2, self.rect.w-6, 3), border_radius=2)
        nc = CYAN_ACCENT if self.hovered else UNGU_NEON
        ns = font_sedang.render(self.num, True, nc)
        surface.blit(ns, (self.rect.x + 18, self.rect.y + 15))
        words = self.label.split()
        line1 = " ".join(words[:2]) if len(words) > 2 else self.label
        line2 = " ".join(words[2:]) if len(words) > 2 else ""
        l1 = font_kecil.render(line1, True, PUTIH)
        surface.blit(l1, (self.rect.x + 18, self.rect.y + 50))
        if line2:
            l2 = font_kecil.render(line2, True, PUTIH)
            surface.blit(l2, (self.rect.x + 18, self.rect.y + 70))
        # star button
        sc = EMAS if fav else ABU
        pygame.draw.rect(surface, (0,0,0,0), self._star_r)
        star_s = font_micro.render("*", True, sc)
        surface.blit(star_s, (self._star_r.x + 2, self._star_r.y + 2))
        # info button
        pygame.draw.circle(surface, UNGU_SEDANG,
                           self._info_r.center, 10)
        pygame.draw.circle(surface, CYAN_ACCENT,
                           self._info_r.center, 10, 1)
        info_s = font_micro.render("i", True, CYAN_ACCENT)
        surface.blit(info_s, (self._info_r.centerx - info_s.get_width()//2,
                               self._info_r.centery - info_s.get_height()//2))
    def update_rects(self):
        self._star_r = pygame.Rect(self.rect.x + self.rect.w - 28, self.rect.y + 4, 22, 22)
        self._info_r = pygame.Rect(self.rect.x + self.rect.w - 54, self.rect.y + 4, 22, 22)
    def check_hover(self, pos): self.hovered = self.rect.collidepoint(pos)
    def clicked(self, pos, event):
        return event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(pos)
    def star_clicked(self, pos, event):
        return event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self._star_r.collidepoint(pos)
    def info_clicked(self, pos, event):
        return event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self._info_r.collidepoint(pos)

# ─── SEARCH BAR ──────────────────────────────────────────────────────────────
class SearchBar:
    def __init__(self, x, y, w, h):
        self.rect   = pygame.Rect(x, y, w, h)
        self.text   = ""; self.active = False
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_ESCAPE:
                self.text = ""; self.active = False
            elif len(self.text) < 24:
                self.text += event.unicode
    def draw(self, surface):
        bc = CYAN_ACCENT if self.active else UNGU_NEON
        pygame.draw.rect(surface, (20, 10, 40), self.rect, border_radius=8)
        pygame.draw.rect(surface, bc, self.rect, 2, border_radius=8)
        icon = font_kecil.render("🔍", True, ABU)
        surface.blit(icon, (self.rect.x + 8, self.rect.centery - icon.get_height()//2))
        if self.text:
            ts = font_kecil.render(self.text, True, PUTIH)
        else:
            ts = font_kecil.render("Cari modul...", True, (80, 60, 100))
        surface.blit(ts, (self.rect.x + 34, self.rect.centery - ts.get_height()//2))
        if self.active and self.text:
            cx = self.rect.x + 34 + font_kecil.size(self.text)[0] + 2
            pygame.draw.line(surface, CYAN_ACCENT, (cx, self.rect.centery-8), (cx, self.rect.centery+8), 2)
    def matches(self, label: str) -> bool:
        if not self.text: return True
        return self.text.lower() in label.lower()

# ─── MENU UTAMA ──────────────────────────────────────────────────────────────
def menu_utama():
    all_items = [
        ("01","Operasi Dasar"),("02","Pangkat & Akar"),("03","Trigonometri"),("04","Logaritma"),
        ("05","Faktorial & Kombinasi"),("06","Persamaan Kuadrat"),("07","Konversi Suhu"),
        ("08","Konversi Panjang"),("09","Konversi Berat"),("10","Sistem Bilangan"),
        ("11","Statistik"),("12","Matrix 2x2"),("13","Bilangan Prima"),("14","FPB & KPK"),
        ("15","Pythagoras"),("16","Luas Bangun"),("17","Volume Bangun"),("18","Pecahan"),
        ("19","Persentase"),("20","Diskon & Pajak"),("21","Bunga Sederhana"),("22","Fibonacci"),
        ("23","Barisan Aritmatika"),("24","Aritmatika Lanjutan"),("25","Barisan Geometri"),
        ("26","Kecepatan & Jarak"),("27","BMI Calculator"),("28","Konversi Waktu"),
        ("29","Konversi Data"),("30","Bilangan Kompleks"),("31","Determinan 3x3"),
    ]

    cw, ch = 230, 105; gx, gy = 18, 18; cols = 4
    tw   = cols*cw + (cols-1)*gx
    sx   = (LEBAR - tw)//2; sy = 175
    visible_rows = 4

    search    = SearchBar(sx, 130, tw, 36)
    scroll_off = 0
    btn_keluar = Button(LEBAR//2-90, 640, 180, 50, "[ KELUAR ]", (80,20,30),(140,40,40))
    btn_hist   = Button(LEBAR - 220, 640, 170, 50, "📋 Riwayat", (40,30,70),(80,60,140))
    btn_fs     = Button(40, 640, 160, 50, "⛶ Fullscreen", (40,30,70),(80,60,140))

    while True:
        pos = pygame.mouse.get_pos()
        navigate_to = None

        # Build filtered + sorted item list (favourites first)
        favs   = _app_data["favourites"]
        items  = [(i, num, label) for i, (num, label) in enumerate(all_items)
                  if search.matches(label)]
        items.sort(key=lambda t: (0 if t[0] in favs else 1, t[0]))

        total_rows = (len(items) + cols - 1) // cols
        scrollbar  = Scrollbar(LEBAR-50, sy, 20, visible_rows*(ch+gy)-gy)

        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "keluar"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11: toggle_fullscreen()
                if event.key == pygame.K_ESCAPE: return "keluar"
            scroll_off = scrollbar.handle(event, pos, total_rows, visible_rows, scroll_off, ch+gy)
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4: scroll_off = max(0, scroll_off - 30)
                if event.button == 5: scroll_off = min(max(0,(total_rows-visible_rows)*(ch+gy)), scroll_off+30)
            if btn_keluar.clicked(pos, event): return "keluar"
            if btn_hist.clicked(pos, event):   show_history_overlay()
            if btn_fs.clicked(pos, event):     toggle_fullscreen()
            search.handle_event(event)
            for j, (orig_i, num, label) in enumerate(items):
                col_j = j % cols; row_j = j // cols
                cx2 = sx + col_j*(cw+gx); cy2 = sy + row_j*(ch+gy) - scroll_off
                card = MenuCard(cx2, cy2, cw, ch, num, label, orig_i)
                if card.star_clicked(pos, event):
                    toggle_favourite(orig_i); play_click()
                elif card.info_clicked(pos, event):
                    play_click()
                    show_tooltip_overlay(label)
                elif card.clicked(pos, event):
                    navigate_to = str(orig_i + 1)

        if navigate_to: return navigate_to

        scroll_off = scrollbar.update(total_rows, visible_rows, scroll_off, ch+gy)

        draw_bg(layar)
        draw_gradient_title(layar, "CALCULATOR ULTIMATE", LEBAR//2, 72)
        pygame.draw.line(layar, UNGU_NEON,  (60, 115), (LEBAR-60, 115), 1)
        pygame.draw.line(layar, UNGU_GLOW,  (60, 117), (LEBAR-60, 117), 1)

        # hint line
        hint_t = font_micro.render("* = Pin Favorit  |  i = Info Rumus  |  F11 = Fullscreen  |  Favorit muncul di atas", True, (70,50,100))
        layar.blit(hint_t, (LEBAR//2 - hint_t.get_width()//2, 118))

        search.draw(layar)

        clip = pygame.Rect(sx-10, sy, tw+20, visible_rows*(ch+gy))
        layar.set_clip(clip)
        for j, (orig_i, num, label) in enumerate(items):
            col_j = j % cols; row_j = j // cols
            cx2   = sx + col_j*(cw+gx); cy2 = sy + row_j*(ch+gy) - scroll_off
            if cy2 < sy - ch or cy2 > sy + visible_rows*(ch+gy): continue
            card = MenuCard(cx2, cy2, cw, ch, num, label, orig_i)
            card.check_hover(pos); card.draw(layar)
        layar.set_clip(None)

        if total_rows > visible_rows: scrollbar.draw(layar)
        btn_keluar.check_hover(pos); btn_keluar.draw(layar)
        btn_hist.check_hover(pos);   btn_hist.draw(layar)
        btn_fs.check_hover(pos);     btn_fs.draw(layar)
        draw_watermark(layar)
        pygame.display.flip(); clock.tick(FPS)

# ─── GENERIC KONVERSI ────────────────────────────────────────────────────────
def scene_konversi_satuan(judul, units, factors, unit_names=None):
    if unit_names is None: unit_names = {u: u for u in units}
    n       = len(units)
    per_row = 5 if n > 5 else n
    rows_c  = (n + per_row - 1) // per_row
    bw      = (LEBAR - 100) // per_row - 8
    unit_btns = [Button(50+i%per_row*(bw+8), 155+i//per_row*52, bw, 44, unit_names[u])
                 for i, u in enumerate(units)]
    btn_y    = 155 + rows_c*52 + 12
    input1   = InputBox(LEBAR//2-160, 100, 320, 40, "Nilai:")
    btn_hit  = Button(LEBAR//2-85, btn_y, 170, 45, "KONVERSI")
    btn_back = Button(40, 640, 160, 50, "[ KEMBALI ]", (80,20,30),(140,40,40))
    selected = 0; hasil = []; copy_info = None

    while True:
        pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "keluar"
            if btn_back.clicked(pos, event): return "menu"
            input1.handle_event(event)
            for i, btn in enumerate(unit_btns):
                if btn.clicked(pos, event): selected = i; hasil = []
            if btn_hit.clicked(pos, event):
                try:
                    val  = float(input1.text)
                    base = val * factors[units[selected]]
                    hasil = [f"{val} {unit_names[units[selected]]}  =  {fmt(base/factors[u])} {unit_names[u]}"
                             for u in units if u != units[selected]]
                    add_history(judul, {"nilai": input1.text, "satuan": unit_names[units[selected]]},
                                hasil[0] if hasil else "")
                except: hasil = ["ERROR: Input tidak valid"]
            if copy_info:
                _, cbr, ct = copy_info
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and cbr.collidepoint(pos):
                    copy_to_clipboard(ct); play_click()

        draw_bg(layar); draw_scene_header(layar, judul)
        input1.draw(layar)
        render_text("Pilih satuan asal:", font_kecil, ABU, 50, 143)
        for i, btn in enumerate(unit_btns):
            btn.active = (i == selected); btn.check_hover(pos); btn.draw(layar)
        btn_hit.check_hover(pos); btn_hit.draw(layar)
        if hasil:
            copy_info = draw_hasil_box(layar, hasil, btn_y+60, is_list=True)
        btn_back.check_hover(pos); btn_back.draw(layar)
        pygame.display.flip(); clock.tick(FPS)

# ─── GENERIC SHAPE CALC ──────────────────────────────────────────────────────
def scene_shape_calc(judul, shapes, per_row=5):
    rows_c   = (len(shapes) + per_row - 1) // per_row
    bw       = (LEBAR - 100) // per_row - 8
    shape_btns = []
    for i, sd in enumerate(shapes):
        col = i % per_row; row = i // per_row
        shape_btns.append(Button(50+col*(bw+8), 90+row*52, bw, 44, sd[0], font=font_micro))

    sep_y      = 90 + rows_c*52 + 8
    max_inp    = max(len(s[1]) for s in shapes)
    inputs     = [InputBox(55, 0, 320, 40, "") for _ in range(max_inp)]
    btn_hitung = Button(130, 0, 170, 45, "HITUNG")
    btn_clear  = Button(315, 0, 90, 45, "✕ Clear", (80,20,30),(140,40,40))
    btn_back   = Button(40, 640, 160, 50, "[ KEMBALI ]", (80,20,30),(140,40,40))
    selected   = 0; hasil = ""; copy_info = None

    PREVIEW_X = 450; PREVIEW_W = LEBAR - PREVIEW_X - 50

    while True:
        pos     = pygame.mouse.get_pos()
        sd      = shapes[selected]
        name_s  = sd[0]; labels_s = sd[1]; fn_s = sd[2]
        rumus_s = sd[3] if len(sd) > 3 else ""
        active_count = len(labels_s)
        inp_start    = sep_y + 28
        for j in range(active_count):
            inputs[j].rect.y = inp_start + j*70
        btn_hitung.rect.y = inp_start + active_count*70 + 8
        btn_clear.rect.y  = btn_hitung.rect.y

        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "keluar"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                toggle_fullscreen()
            if btn_back.clicked(pos, event): return "menu"
            if btn_clear.clicked(pos, event):
                for inp in inputs: inp.text = ""; inp.active = False
                hasil = ""
            for i, btn in enumerate(shape_btns):
                if btn.clicked(pos, event) and i != selected:
                    selected = i
                    for inp in inputs: inp.text = ""; inp.active = False
                    hasil = ""
            for j in range(active_count):
                inputs[j].handle_event(event)
            if btn_hitung.clicked(pos, event):
                try:
                    vals  = [float(inputs[j].text) for j in range(active_count)]
                    hasil = fn_s(vals)
                    inp_dict = {labels_s[j]: inputs[j].text for j in range(active_count)}
                    add_history(judul, inp_dict, hasil)
                except: hasil = "ERROR: Input tidak valid"
            if copy_info:
                _, cbr, ct = copy_info
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and cbr.collidepoint(pos):
                    copy_to_clipboard(ct); play_click()

        draw_bg(layar); draw_scene_header(layar, judul)
        for i, btn in enumerate(shape_btns):
            btn.active = (i == selected); btn.check_hover(pos); btn.draw(layar)
        pygame.draw.line(layar, UNGU_NEON, (50, sep_y), (LEBAR-50, sep_y), 1)
        render_text(f"Input — {name_s}:", font_kecil, CYAN_ACCENT, 55, sep_y+8)
        for j in range(active_count):
            inputs[j].label = labels_s[j]; inputs[j].draw(layar)
        btn_hitung.check_hover(pos); btn_hitung.draw(layar)
        btn_clear.check_hover(pos);  btn_clear.draw(layar)

        # preview
        prev_top = sep_y + 20; prev_bot = btn_hitung.rect.bottom
        prev_h   = max(60, prev_bot - prev_top)
        prev_r   = pygame.Rect(PREVIEW_X, prev_top, PREVIEW_W, prev_h)
        pygame.draw.rect(layar, UNGU_CARD, prev_r, border_radius=10)
        pygame.draw.rect(layar, UNGU_GLOW, prev_r, 2, border_radius=10)
        draw_area = pygame.Rect(prev_r.x, prev_r.y, prev_r.w, prev_r.h - (50 if rumus_s else 0))
        draw_shape_preview(layar, name_s, draw_area)
        if rumus_s:
            lbl  = font_micro.render("Rumus:", True, ABU)
            rtxt = font_sedang.render(rumus_s, True, HIJAU)
            layar.blit(lbl,  (prev_r.x + 20, prev_r.bottom - 48))
            layar.blit(rtxt, (prev_r.x + 20, prev_r.bottom - 32))

        if hasil:
            copy_info = draw_hasil_box(layar, hasil, btn_hitung.rect.bottom + 20)
        btn_back.check_hover(pos); btn_back.draw(layar)
        pygame.display.flip(); clock.tick(FPS)

# ─── GENERIC SCENE HELPER (adds history + copy + clear to any scene) ─────────
def _make_generic_scene(title, inputs_cfg, buttons_cfg, compute_map, is_list_result=False):
    """
    inputs_cfg  : [(x,y,w,h,label), ...]
    buttons_cfg : [(x,y,w,h,text), ...]
    compute_map : {btn_index: fn(input_texts) -> str or list}
    """
    inputs    = [InputBox(c[0],c[1],c[2],c[3],c[4]) for c in inputs_cfg]
    btns      = [Button(c[0],c[1],c[2],c[3],c[4])   for c in buttons_cfg]
    btn_back  = Button(40, 640, 160, 50, "[ KEMBALI ]", (80,20,30),(140,40,40))
    btn_clear = Button(LEBAR-210, 640, 160, 50, "✕ Clear", (60,20,30),(120,40,40))
    hasil = "" if not is_list_result else []
    copy_info = None

    while True:
        pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "keluar"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                toggle_fullscreen()
            if btn_back.clicked(pos, event):  return "menu"
            if btn_clear.clicked(pos, event):
                for inp in inputs: inp.text = ""
                hasil = "" if not is_list_result else []
            for inp in inputs: inp.handle_event(event)
            for i, btn in enumerate(btns):
                if btn.clicked(pos, event) and i in compute_map:
                    try:
                        texts = [inp.text for inp in inputs]
                        hasil = compute_map[i](texts)
                        flat  = "\n".join(hasil) if isinstance(hasil, list) else hasil
                        add_history(title, {f"inp{j}": t for j,t in enumerate(texts)}, flat)
                    except: hasil = ["ERROR: Input tidak valid"] if is_list_result else "ERROR: Input tidak valid"
            if copy_info:
                _, cbr, ct = copy_info
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and cbr.collidepoint(pos):
                    copy_to_clipboard(ct); play_click()
        return (inputs, btns, btn_back, btn_clear, hasil, copy_info, pos)

# ─── SCENES 1-15 (refactored with clear + copy + history) ───────────────────
def _scene_base(draw_fn):
    """Wrapper: draw_fn yields one frame, returns nav string when done."""
    pass  # individual scenes handle their own loops for flexibility

def scene_operasi_dasar():
    inputs   = [InputBox(LEBAR//2-160,130,320,40,"Angka 1:"),
                InputBox(LEBAR//2-160,205,320,40,"Angka 2:")]
    btns     = [Button(80+i*155,285,140,50,op) for i,op in enumerate(["+","-","x","÷","%","^"])]
    btn_back = Button(40,640,160,50,"[ KEMBALI ]",(80,20,30),(140,40,40))
    btn_clr  = Button(LEBAR-210,640,160,50,"✕ Clear",(60,20,30),(120,40,40))
    hasil    = ""; copy_info = None
    while True:
        pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type==pygame.QUIT: return "keluar"
            if event.type==pygame.KEYDOWN and event.key==pygame.K_F11: toggle_fullscreen()
            if btn_back.clicked(pos,event): return "menu"
            if btn_clr.clicked(pos,event):
                for inp in inputs: inp.text=""
                hasil=""
            for inp in inputs: inp.handle_event(event)
            for i,btn in enumerate(btns):
                if btn.clicked(pos,event):
                    try:
                        a=float(inputs[0].text); b=float(inputs[1].text)
                        ops=[f"{a}+{b}={a+b}",f"{a}-{b}={a-b}",f"{a}×{b}={a*b}",
                             "ERROR: Tidak bisa bagi 0" if b==0 else f"{a}÷{b}={a/b}",
                             f"{a}%{b}={a%b}",f"{a}^{b}={a**b}"]
                        hasil=ops[i]
                        add_history("Operasi Dasar",{"a":inputs[0].text,"b":inputs[1].text},hasil)
                    except: hasil="ERROR: Input tidak valid"
            if copy_info:
                _,cbr,ct=copy_info
                if event.type==pygame.MOUSEBUTTONDOWN and event.button==1 and cbr.collidepoint(pos):
                    copy_to_clipboard(ct); play_click()
        draw_bg(layar); draw_scene_header(layar,"OPERASI DASAR")
        for inp in inputs: inp.draw(layar)
        for btn in btns: btn.check_hover(pos); btn.draw(layar)
        if hasil: copy_info=draw_hasil_box(layar,hasil,365)
        btn_back.check_hover(pos); btn_back.draw(layar)
        btn_clr.check_hover(pos);  btn_clr.draw(layar)
        pygame.display.flip(); clock.tick(FPS)

def scene_pangkat_akar():
    i1=InputBox(LEBAR//2-160,130,320,40,"Angka:")
    i2=InputBox(LEBAR//2-160,205,320,40,"n (akar/pangkat n):")
    btns=[Button(100+i*195,285,180,50,lb) for i,lb in enumerate(["x²","x³","√x","ⁿ√x","xⁿ"])]
    btn_back=Button(40,640,160,50,"[ KEMBALI ]",(80,20,30),(140,40,40))
    btn_clr=Button(LEBAR-210,640,160,50,"✕ Clear",(60,20,30),(120,40,40))
    hasil=""; copy_info=None
    while True:
        pos=pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type==pygame.QUIT: return "keluar"
            if event.type==pygame.KEYDOWN and event.key==pygame.K_F11: toggle_fullscreen()
            if btn_back.clicked(pos,event): return "menu"
            if btn_clr.clicked(pos,event): i1.text=""; i2.text=""; hasil=""
            i1.handle_event(event); i2.handle_event(event)
            for i,btn in enumerate(btns):
                if btn.clicked(pos,event):
                    try:
                        x=float(i1.text)
                        if i==0: hasil=f"{x}² = {x**2}"
                        elif i==1: hasil=f"{x}³ = {x**3}"
                        elif i==2: hasil="ERROR: Akar bilangan negatif" if x<0 else f"√{x} = {math.sqrt(x):.6f}"
                        elif i==3:
                            n=int(i2.text); hasil="ERROR: n tidak boleh 0" if n==0 else f"{n}√{x} = {x**(1/n):.6f}"
                        elif i==4: n=float(i2.text); hasil=f"{x}^{n} = {x**n}"
                        add_history("Pangkat & Akar",{"x":i1.text},hasil)
                    except: hasil="ERROR: Input tidak valid"
            if copy_info:
                _,cbr,ct=copy_info
                if event.type==pygame.MOUSEBUTTONDOWN and event.button==1 and cbr.collidepoint(pos):
                    copy_to_clipboard(ct); play_click()
        draw_bg(layar); draw_scene_header(layar,"PANGKAT & AKAR")
        i1.draw(layar); i2.draw(layar)
        for btn in btns: btn.check_hover(pos); btn.draw(layar)
        if hasil: copy_info=draw_hasil_box(layar,hasil,375)
        btn_back.check_hover(pos); btn_back.draw(layar)
        btn_clr.check_hover(pos); btn_clr.draw(layar)
        pygame.display.flip(); clock.tick(FPS)

def scene_trigonometri():
    i1=InputBox(LEBAR//2-160,130,320,40,"Sudut (derajat):")
    btns=[Button(80+i*165,210,150,50,f) for i,f in enumerate(["sin","cos","tan","sec","csc","cot"])]
    btn_back=Button(40,640,160,50,"[ KEMBALI ]",(80,20,30),(140,40,40))
    btn_clr=Button(LEBAR-210,640,160,50,"✕ Clear",(60,20,30),(120,40,40))
    hasil=""; copy_info=None
    while True:
        pos=pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type==pygame.QUIT: return "keluar"
            if event.type==pygame.KEYDOWN and event.key==pygame.K_F11: toggle_fullscreen()
            if btn_back.clicked(pos,event): return "menu"
            if btn_clr.clicked(pos,event): i1.text=""; hasil=""
            i1.handle_event(event)
            for i,btn in enumerate(btns):
                if btn.clicked(pos,event):
                    try:
                        deg=float(i1.text); rad=math.radians(deg)
                        fns=["sin","cos","tan","sec","csc","cot"]
                        vs=[math.sin(rad),math.cos(rad),math.tan(rad),
                            None if abs(math.cos(rad))<1e-10 else 1/math.cos(rad),
                            None if abs(math.sin(rad))<1e-10 else 1/math.sin(rad),
                            None if abs(math.tan(rad))<1e-10 else 1/math.tan(rad)]
                        hasil=f"ERROR: {fns[i]} undefined" if vs[i] is None else f"{fns[i]}({deg}°) = {vs[i]:.6f}"
                        add_history("Trigonometri",{"sudut":i1.text},hasil)
                    except: hasil="ERROR: Input tidak valid"
            if copy_info:
                _,cbr,ct=copy_info
                if event.type==pygame.MOUSEBUTTONDOWN and event.button==1 and cbr.collidepoint(pos):
                    copy_to_clipboard(ct); play_click()
        draw_bg(layar); draw_scene_header(layar,"TRIGONOMETRI")
        i1.draw(layar)
        for btn in btns: btn.check_hover(pos); btn.draw(layar)
        if hasil: copy_info=draw_hasil_box(layar,hasil,295)
        btn_back.check_hover(pos); btn_back.draw(layar)
        btn_clr.check_hover(pos); btn_clr.draw(layar)
        pygame.display.flip(); clock.tick(FPS)

def scene_logaritma():
    i1=InputBox(LEBAR//2-160,130,320,40,"Angka:")
    i2=InputBox(LEBAR//2-160,205,320,40,"Base (log_n):")
    btns=[Button(330+i*160,290,140,50,lb) for i,lb in enumerate(["log₁₀","ln","logₙ"])]
    btn_back=Button(40,640,160,50,"[ KEMBALI ]",(80,20,30),(140,40,40))
    btn_clr=Button(LEBAR-210,640,160,50,"✕ Clear",(60,20,30),(120,40,40))
    hasil=""; copy_info=None
    while True:
        pos=pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type==pygame.QUIT: return "keluar"
            if event.type==pygame.KEYDOWN and event.key==pygame.K_F11: toggle_fullscreen()
            if btn_back.clicked(pos,event): return "menu"
            if btn_clr.clicked(pos,event): i1.text=""; i2.text=""; hasil=""
            i1.handle_event(event); i2.handle_event(event)
            for i,btn in enumerate(btns):
                if btn.clicked(pos,event):
                    try:
                        x=float(i1.text)
                        if x<=0: hasil="ERROR: Log hanya untuk x > 0"; continue
                        if i==0: hasil=f"log₁₀({x}) = {math.log10(x):.6f}"
                        elif i==1: hasil=f"ln({x}) = {math.log(x):.6f}"
                        elif i==2:
                            base=float(i2.text)
                            hasil="ERROR: Base harus > 0 dan ≠ 1" if base<=0 or base==1 else f"log_{base}({x}) = {math.log(x,base):.6f}"
                        add_history("Logaritma",{"x":i1.text},hasil)
                    except: hasil="ERROR: Input tidak valid"
            if copy_info:
                _,cbr,ct=copy_info
                if event.type==pygame.MOUSEBUTTONDOWN and event.button==1 and cbr.collidepoint(pos):
                    copy_to_clipboard(ct); play_click()
        draw_bg(layar); draw_scene_header(layar,"LOGARITMA")
        i1.draw(layar); i2.draw(layar)
        for btn in btns: btn.check_hover(pos); btn.draw(layar)
        if hasil: copy_info=draw_hasil_box(layar,hasil,370)
        btn_back.check_hover(pos); btn_back.draw(layar)
        btn_clr.check_hover(pos); btn_clr.draw(layar)
        pygame.display.flip(); clock.tick(FPS)

def scene_faktorial():
    i1=InputBox(LEBAR//2-160,130,320,40,"n:")
    i2=InputBox(LEBAR//2-160,205,320,40,"r (nPr/nCr):")
    btns=[Button(330+i*160,290,140,50,lb) for i,lb in enumerate(["n!","nPr","nCr"])]
    btn_back=Button(40,640,160,50,"[ KEMBALI ]",(80,20,30),(140,40,40))
    btn_clr=Button(LEBAR-210,640,160,50,"✕ Clear",(60,20,30),(120,40,40))
    hasil=""; copy_info=None
    while True:
        pos=pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type==pygame.QUIT: return "keluar"
            if event.type==pygame.KEYDOWN and event.key==pygame.K_F11: toggle_fullscreen()
            if btn_back.clicked(pos,event): return "menu"
            if btn_clr.clicked(pos,event): i1.text=""; i2.text=""; hasil=""
            i1.handle_event(event); i2.handle_event(event)
            for i,btn in enumerate(btns):
                if btn.clicked(pos,event):
                    try:
                        n=int(i1.text)
                        if n<0: hasil="ERROR: n ≥ 0"; continue
                        if i==0: hasil=f"{n}! = {math.factorial(n)}"
                        else:
                            r=int(i2.text)
                            if r<0 or r>n: hasil="ERROR: 0 ≤ r ≤ n"; continue
                            hasil=f"P({n},{r})={math.perm(n,r)}" if i==1 else f"C({n},{r})={math.comb(n,r)}"
                        add_history("Faktorial",{"n":i1.text,"r":i2.text},hasil)
                    except: hasil="ERROR: Input tidak valid"
            if copy_info:
                _,cbr,ct=copy_info
                if event.type==pygame.MOUSEBUTTONDOWN and event.button==1 and cbr.collidepoint(pos):
                    copy_to_clipboard(ct); play_click()
        draw_bg(layar); draw_scene_header(layar,"FAKTORIAL & KOMBINASI")
        i1.draw(layar); i2.draw(layar)
        for btn in btns: btn.check_hover(pos); btn.draw(layar)
        if hasil: copy_info=draw_hasil_box(layar,hasil,370)
        btn_back.check_hover(pos); btn_back.draw(layar)
        btn_clr.check_hover(pos); btn_clr.draw(layar)
        pygame.display.flip(); clock.tick(FPS)

def scene_persamaan_kuadrat():
    inputs=[InputBox(LEBAR//2-160,110+i*75,320,40,lb)
            for i,lb in enumerate(["a (koefisien x²):","b (koefisien x):","c (konstanta):"])]
    btn_hit=Button(LEBAR//2-85,340,170,50,"HITUNG")
    btn_back=Button(40,640,160,50,"[ KEMBALI ]",(80,20,30),(140,40,40))
    btn_clr=Button(LEBAR-210,640,160,50,"✕ Clear",(60,20,30),(120,40,40))
    hasil=[]; copy_info=None
    while True:
        pos=pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type==pygame.QUIT: return "keluar"
            if event.type==pygame.KEYDOWN and event.key==pygame.K_F11: toggle_fullscreen()
            if btn_back.clicked(pos,event): return "menu"
            if btn_clr.clicked(pos,event):
                for inp in inputs: inp.text=""
                hasil=[]
            for inp in inputs: inp.handle_event(event)
            if btn_hit.clicked(pos,event):
                try:
                    a=float(inputs[0].text); b=float(inputs[1].text); c=float(inputs[2].text)
                    if a==0: hasil=["ERROR: a tidak boleh 0"]; continue
                    D=b**2-4*a*c; hasil=[f"D = {D:.4f}"]
                    if D>0:
                        x1=(-b+math.sqrt(D))/(2*a); x2=(-b-math.sqrt(D))/(2*a)
                        hasil+=[f"x₁ = {x1:.6f}", f"x₂ = {x2:.6f}"]
                    elif D==0: hasil.append(f"x₁ = x₂ = {-b/(2*a):.6f}")
                    else:
                        re=-b/(2*a); im=math.sqrt(abs(D))/(2*a)
                        hasil+=[f"x₁ = {re:.4f} + {im:.4f}i", f"x₂ = {re:.4f} - {im:.4f}i"]
                    add_history("Persamaan Kuadrat",{"a":inputs[0].text,"b":inputs[1].text,"c":inputs[2].text},
                                " | ".join(hasil))
                except: hasil=["ERROR: Input tidak valid"]
            if copy_info:
                _,cbr,ct=copy_info
                if event.type==pygame.MOUSEBUTTONDOWN and event.button==1 and cbr.collidepoint(pos):
                    copy_to_clipboard(ct); play_click()
        draw_bg(layar); draw_scene_header(layar,"PERSAMAAN KUADRAT (ax²+bx+c=0)")
        for inp in inputs: inp.draw(layar)
        btn_hit.check_hover(pos); btn_hit.draw(layar)
        if hasil: copy_info=draw_hasil_box(layar,hasil,415,is_list=True)
        btn_back.check_hover(pos); btn_back.draw(layar)
        btn_clr.check_hover(pos); btn_clr.draw(layar)
        pygame.display.flip(); clock.tick(FPS)

def scene_sistem_bilangan():
    i1=InputBox(LEBAR//2-160,130,320,40,"Nilai:")
    labels=["Dec→Bin","Dec→Oct","Dec→Hex","Bin→Dec","Oct→Dec","Hex→Dec"]
    btns=[Button(80+(i%3)*320,210+(i//3)*70,300,55,lb) for i,lb in enumerate(labels)]
    btn_back=Button(40,640,160,50,"[ KEMBALI ]",(80,20,30),(140,40,40))
    btn_clr=Button(LEBAR-210,640,160,50,"✕ Clear",(60,20,30),(120,40,40))
    hasil=""; copy_info=None
    while True:
        pos=pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type==pygame.QUIT: return "keluar"
            if event.type==pygame.KEYDOWN and event.key==pygame.K_F11: toggle_fullscreen()
            if btn_back.clicked(pos,event): return "menu"
            if btn_clr.clicked(pos,event): i1.text=""; hasil=""
            i1.handle_event(event)
            for i,btn in enumerate(btns):
                if btn.clicked(pos,event):
                    try:
                        v=int(i1.text) if i<3 else i1.text
                        r=[f"{v}(10)={bin(v)[2:]}(2)",f"{v}(10)={oct(v)[2:]}(8)",
                           f"{v}(10)={hex(v)[2:].upper()}(16)",f"{v}(2)={int(v,2)}(10)",
                           f"{v}(8)={int(v,8)}(10)",f"{v}(16)={int(v,16)}(10)"]
                        hasil=r[i]
                        add_history("Sistem Bilangan",{"nilai":i1.text},hasil)
                    except: hasil="ERROR: Input tidak valid"
            if copy_info:
                _,cbr,ct=copy_info
                if event.type==pygame.MOUSEBUTTONDOWN and event.button==1 and cbr.collidepoint(pos):
                    copy_to_clipboard(ct); play_click()
        draw_bg(layar); draw_scene_header(layar,"SISTEM BILANGAN")
        i1.draw(layar)
        for btn in btns: btn.check_hover(pos); btn.draw(layar)
        if hasil: copy_info=draw_hasil_box(layar,hasil,365)
        btn_back.check_hover(pos); btn_back.draw(layar)
        btn_clr.check_hover(pos); btn_clr.draw(layar)
        pygame.display.flip(); clock.tick(FPS)

def scene_statistik():
    i1=InputBox(60,130,LEBAR-120,40,"Data (pisahkan spasi):")
    btn_hit=Button(LEBAR//2-85,195,170,50,"HITUNG")
    btn_back=Button(40,640,160,50,"[ KEMBALI ]",(80,20,30),(140,40,40))
    btn_clr=Button(LEBAR-210,640,160,50,"✕ Clear",(60,20,30),(120,40,40))
    hasil=[]; copy_info=None
    while True:
        pos=pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type==pygame.QUIT: return "keluar"
            if event.type==pygame.KEYDOWN and event.key==pygame.K_F11: toggle_fullscreen()
            if btn_back.clicked(pos,event): return "menu"
            if btn_clr.clicked(pos,event): i1.text=""; hasil=[]
            i1.handle_event(event)
            if btn_hit.clicked(pos,event):
                try:
                    data=list(map(float,i1.text.split()))
                    if not data: hasil=["ERROR: Data kosong"]; continue
                    n=len(data); mean=sum(data)/n; ds=sorted(data)
                    median=(ds[n//2-1]+ds[n//2])/2 if n%2==0 else ds[n//2]
                    var=sum((x-mean)**2 for x in data)/n; std=math.sqrt(var)
                    hasil=[f"N={n}  Mean={mean:.4f}",f"Median={median:.4f}  Variansi={var:.4f}",
                           f"StdDev={std:.4f}  Min={min(data):.2f}  Max={max(data):.2f}"]
                    add_history("Statistik",{"data":i1.text[:40]}," | ".join(hasil))
                except: hasil=["ERROR: Input tidak valid"]
            if copy_info:
                _,cbr,ct=copy_info
                if event.type==pygame.MOUSEBUTTONDOWN and event.button==1 and cbr.collidepoint(pos):
                    copy_to_clipboard(ct); play_click()
        draw_bg(layar); draw_scene_header(layar,"STATISTIK")
        i1.draw(layar); btn_hit.check_hover(pos); btn_hit.draw(layar)
        if hasil: copy_info=draw_hasil_box(layar,hasil,270,is_list=True)
        btn_back.check_hover(pos); btn_back.draw(layar)
        btn_clr.check_hover(pos); btn_clr.draw(layar)
        pygame.display.flip(); clock.tick(FPS)

def scene_matrix():
    ax,ay=200,100; bx,by=650,100
    ia=[InputBox(ax+(i%2)*130,ay+30+(i//2)*65,115,38,f"a{i//2+1}{i%2+1}:") for i in range(4)]
    ib=[InputBox(bx+(i%2)*130,by+30+(i//2)*65,115,38,f"b{i//2+1}{i%2+1}:") for i in range(4)]
    btns=[Button(250+i*200,270,180,50,lb) for i,lb in enumerate(["A+B","A×B","Det(A)"])]
    btn_back=Button(40,640,160,50,"[ KEMBALI ]",(80,20,30),(140,40,40))
    btn_clr=Button(LEBAR-210,640,160,50,"✕ Clear",(60,20,30),(120,40,40))
    hasil=[]; copy_info=None
    while True:
        pos=pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type==pygame.QUIT: return "keluar"
            if event.type==pygame.KEYDOWN and event.key==pygame.K_F11: toggle_fullscreen()
            if btn_back.clicked(pos,event): return "menu"
            if btn_clr.clicked(pos,event):
                for inp in ia+ib: inp.text=""
                hasil=[]
            for inp in ia+ib: inp.handle_event(event)
            for i,btn in enumerate(btns):
                if btn.clicked(pos,event):
                    try:
                        a11=float(ia[0].text); a12=float(ia[1].text)
                        a21=float(ia[2].text); a22=float(ia[3].text)
                        if i==0:
                            b11=float(ib[0].text); b12=float(ib[1].text)
                            b21=float(ib[2].text); b22=float(ib[3].text)
                            hasil=["A+B:",f"[{a11+b11:.2f}  {a12+b12:.2f}]",f"[{a21+b21:.2f}  {a22+b22:.2f}]"]
                        elif i==1:
                            b11=float(ib[0].text); b12=float(ib[1].text)
                            b21=float(ib[2].text); b22=float(ib[3].text)
                            hasil=["A×B:",
                                   f"[{a11*b11+a12*b21:.2f}  {a11*b12+a12*b22:.2f}]",
                                   f"[{a21*b11+a22*b21:.2f}  {a21*b12+a22*b22:.2f}]"]
                        elif i==2: hasil=[f"Det(A) = {a11*a22-a12*a21:.6f}"]
                        add_history("Matrix 2x2",{}," | ".join(hasil))
                    except: hasil=["ERROR: Input tidak valid"]
            if copy_info:
                _,cbr,ct=copy_info
                if event.type==pygame.MOUSEBUTTONDOWN and event.button==1 and cbr.collidepoint(pos):
                    copy_to_clipboard(ct); play_click()
        draw_bg(layar); draw_scene_header(layar,"MATRIX 2x2")
        render_text("Matrix A",font_kecil,CYAN_ACCENT,ax,ay-10)
        render_text("Matrix B",font_kecil,CYAN_ACCENT,bx,by-10)
        for inp in ia+ib: inp.draw(layar)
        for btn in btns: btn.check_hover(pos); btn.draw(layar)
        if hasil: copy_info=draw_hasil_box(layar,hasil,350,is_list=True)
        btn_back.check_hover(pos); btn_back.draw(layar)
        btn_clr.check_hover(pos); btn_clr.draw(layar)
        pygame.display.flip(); clock.tick(FPS)

def scene_bilangan_prima():
    i1=InputBox(LEBAR//2-160,150,320,40,"Angka:")
    btn_cek=Button(LEBAR//2-150,220,140,50,"Cek Prima")
    btn_lst=Button(LEBAR//2+10,220,140,50,"List Prima")
    btn_back=Button(40,640,160,50,"[ KEMBALI ]",(80,20,30),(140,40,40))
    btn_clr=Button(LEBAR-210,640,160,50,"✕ Clear",(60,20,30),(120,40,40))
    hasil=""; copy_info=None
    while True:
        pos=pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type==pygame.QUIT: return "keluar"
            if event.type==pygame.KEYDOWN and event.key==pygame.K_F11: toggle_fullscreen()
            if btn_back.clicked(pos,event): return "menu"
            if btn_clr.clicked(pos,event): i1.text=""; hasil=""
            i1.handle_event(event)
            if btn_cek.clicked(pos,event):
                try:
                    n=int(i1.text)
                    p=all(n%i!=0 for i in range(2,int(n**0.5)+1)) and n>=2
                    hasil=f"{n} adalah bilangan prima!" if p else f"{n} bukan bilangan prima"
                    add_history("Bilangan Prima",{"n":i1.text},hasil)
                except: hasil="ERROR: Input tidak valid"
            if btn_lst.clicked(pos,event):
                try:
                    lim=int(i1.text)
                    if lim>1000: hasil="ERROR: Maks 1000"; continue
                    ps=[n for n in range(2,lim+1) if all(n%i!=0 for i in range(2,int(n**0.5)+1))]
                    hasil=f"Prima ≤ {lim}: {', '.join(map(str,ps[:40]))}"+ ("…" if len(ps)>40 else "")
                    add_history("Bilangan Prima",{"limit":i1.text},hasil[:60])
                except: hasil="ERROR: Input tidak valid"
            if copy_info:
                _,cbr,ct=copy_info
                if event.type==pygame.MOUSEBUTTONDOWN and event.button==1 and cbr.collidepoint(pos):
                    copy_to_clipboard(ct); play_click()
        draw_bg(layar); draw_scene_header(layar,"BILANGAN PRIMA")
        i1.draw(layar)
        btn_cek.check_hover(pos); btn_cek.draw(layar)
        btn_lst.check_hover(pos); btn_lst.draw(layar)
        if hasil: copy_info=draw_hasil_box(layar,hasil,300)
        btn_back.check_hover(pos); btn_back.draw(layar)
        btn_clr.check_hover(pos); btn_clr.draw(layar)
        pygame.display.flip(); clock.tick(FPS)

def scene_fpb_kpk():
    inputs=[InputBox(LEBAR//2-160,130,320,40,"Angka 1:"),
            InputBox(LEBAR//2-160,205,320,40,"Angka 2:")]
    btn_fpb=Button(LEBAR//2-150,280,140,50,"FPB")
    btn_kpk=Button(LEBAR//2+10,280,140,50,"KPK")
    btn_back=Button(40,640,160,50,"[ KEMBALI ]",(80,20,30),(140,40,40))
    btn_clr=Button(LEBAR-210,640,160,50,"✕ Clear",(60,20,30),(120,40,40))
    hasil=""; copy_info=None
    while True:
        pos=pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type==pygame.QUIT: return "keluar"
            if event.type==pygame.KEYDOWN and event.key==pygame.K_F11: toggle_fullscreen()
            if btn_back.clicked(pos,event): return "menu"
            if btn_clr.clicked(pos,event):
                for inp in inputs: inp.text=""
                hasil=""
            for inp in inputs: inp.handle_event(event)
            if btn_fpb.clicked(pos,event):
                try:
                    a=int(inputs[0].text); b=int(inputs[1].text)
                    hasil=f"FPB({a},{b}) = {math.gcd(a,b)}"
                    add_history("FPB & KPK",{"a":inputs[0].text,"b":inputs[1].text},hasil)
                except: hasil="ERROR: Input tidak valid"
            if btn_kpk.clicked(pos,event):
                try:
                    a=int(inputs[0].text); b=int(inputs[1].text)
                    hasil=f"KPK({a},{b}) = {(a*b)//math.gcd(a,b)}"
                    add_history("FPB & KPK",{"a":inputs[0].text,"b":inputs[1].text},hasil)
                except: hasil="ERROR: Input tidak valid"
            if copy_info:
                _,cbr,ct=copy_info
                if event.type==pygame.MOUSEBUTTONDOWN and event.button==1 and cbr.collidepoint(pos):
                    copy_to_clipboard(ct); play_click()
        draw_bg(layar); draw_scene_header(layar,"FPB & KPK")
        for inp in inputs: inp.draw(layar)
        btn_fpb.check_hover(pos); btn_fpb.draw(layar)
        btn_kpk.check_hover(pos); btn_kpk.draw(layar)
        if hasil: copy_info=draw_hasil_box(layar,hasil,360)
        btn_back.check_hover(pos); btn_back.draw(layar)
        btn_clr.check_hover(pos); btn_clr.draw(layar)
        pygame.display.flip(); clock.tick(FPS)

def scene_pythagoras():
    inputs=[InputBox(LEBAR//2-160,130,320,40,"Sisi a:"),
            InputBox(LEBAR//2-160,205,320,40,"Sisi b:")]
    btn_hit=Button(LEBAR//2-85,280,170,50,"Hitung c")
    btn_back=Button(40,640,160,50,"[ KEMBALI ]",(80,20,30),(140,40,40))
    btn_clr=Button(LEBAR-210,640,160,50,"✕ Clear",(60,20,30),(120,40,40))
    hasil=""; copy_info=None
    while True:
        pos=pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type==pygame.QUIT: return "keluar"
            if event.type==pygame.KEYDOWN and event.key==pygame.K_F11: toggle_fullscreen()
            if btn_back.clicked(pos,event): return "menu"
            if btn_clr.clicked(pos,event):
                for inp in inputs: inp.text=""
                hasil=""
            for inp in inputs: inp.handle_event(event)
            if btn_hit.clicked(pos,event):
                try:
                    a=float(inputs[0].text); b=float(inputs[1].text)
                    c=math.sqrt(a**2+b**2)
                    hasil=f"c = √({a}²+{b}²) = {c:.6f}"
                    add_history("Pythagoras",{"a":inputs[0].text,"b":inputs[1].text},hasil)
                except: hasil="ERROR: Input tidak valid"
            if copy_info:
                _,cbr,ct=copy_info
                if event.type==pygame.MOUSEBUTTONDOWN and event.button==1 and cbr.collidepoint(pos):
                    copy_to_clipboard(ct); play_click()
        draw_bg(layar); draw_scene_header(layar,"PYTHAGORAS  (c²=a²+b²)")
        for inp in inputs: inp.draw(layar)
        btn_hit.check_hover(pos); btn_hit.draw(layar)
        if hasil: copy_info=draw_hasil_box(layar,hasil,360)
        btn_back.check_hover(pos); btn_back.draw(layar)
        btn_clr.check_hover(pos); btn_clr.draw(layar)
        pygame.display.flip(); clock.tick(FPS)

# ─── SCENE 16: LUAS BANGUN ───────────────────────────────────────────────────
def scene_luas_bangun():
    shapes = [
        ("Persegi Pjg",  ["Panjang:", "Lebar:"],
         lambda v: f"L = p×l = {v[0]}×{v[1]} = {v[0]*v[1]:.4f} satuan²", "L = p × l"),
        ("Persegi",      ["Sisi (s):"],
         lambda v: f"L = s² = {v[0]}² = {v[0]**2:.4f} satuan²", "L = s²"),
        ("Segitiga",     ["Alas:", "Tinggi:"],
         lambda v: f"L = ½×a×t = ½×{v[0]}×{v[1]} = {0.5*v[0]*v[1]:.4f} satuan²", "L = ½ × a × t"),
        ("Lingkaran",    ["Jari-jari (r):"],
         lambda v: f"L = π×r² = {math.pi*v[0]**2:.4f} satuan²", "L = π × r²"),
        ("Trapesium",    ["Alas 1 (a):", "Alas 2 (b):", "Tinggi:"],
         lambda v: f"L = ½(a+b)×t = {0.5*(v[0]+v[1])*v[2]:.4f} satuan²", "L = ½(a+b)×t"),
        ("Jajargenjang", ["Alas:", "Tinggi:"],
         lambda v: f"L = a×t = {v[0]*v[1]:.4f} satuan²", "L = a × t"),
        ("Blh Ketupat",  ["Diag 1 (d1):", "Diag 2 (d2):"],
         lambda v: f"L = ½×d1×d2 = {0.5*v[0]*v[1]:.4f} satuan²", "L = ½ × d1 × d2"),
        ("Layang²",      ["Diag 1 (d1):", "Diag 2 (d2):"],
         lambda v: f"L = ½×d1×d2 = {0.5*v[0]*v[1]:.4f} satuan²", "L = ½ × d1 × d2"),
        ("Elips",        ["Sumbu a:", "Sumbu b:"],
         lambda v: f"L = π×a×b = {math.pi*v[0]*v[1]:.4f} satuan²", "L = π × a × b"),
        ("Segi-6 Brtran",["Sisi (s):"],
         lambda v: f"L = (3√3/2)×s² = {(3*math.sqrt(3)/2)*v[0]**2:.4f} satuan²", "L = (3√3/2)×s²"),
    ]
    return scene_shape_calc("LUAS BANGUN DATAR", shapes, per_row=5)

# ─── SCENE 17: VOLUME BANGUN ─────────────────────────────────────────────────
def scene_volume_bangun():
    shapes = [
        ("Kubus",       ["Sisi (s):"],
         lambda v: f"V = s³ = {v[0]**3:.4f} satuan³"),
        ("Balok",       ["Panjang:", "Lebar:", "Tinggi:"],
         lambda v: f"V = p×l×t = {v[0]*v[1]*v[2]:.4f} satuan³"),
        ("Tabung",      ["Jari-jari:", "Tinggi:"],
         lambda v: f"V = π×r²×t = {math.pi*v[0]**2*v[1]:.4f} satuan³"),
        ("Kerucut",     ["Jari-jari:", "Tinggi:"],
         lambda v: f"V = ⅓π×r²×t = {(1/3)*math.pi*v[0]**2*v[1]:.4f} satuan³"),
        ("Bola",        ["Jari-jari:"],
         lambda v: f"V = (4/3)π×r³ = {(4/3)*math.pi*v[0]**3:.4f} satuan³"),
        ("Limas Segi4", ["Sisi Alas:", "Tinggi:"],
         lambda v: f"V = ⅓×a²×t = {(1/3)*v[0]**2*v[1]:.4f} satuan³"),
        ("Prisma Segi3",["Alas Δ:", "Tinggi Δ:", "Tinggi Prisma:"],
         lambda v: f"V = ½×a×t_Δ×T = {0.5*v[0]*v[1]*v[2]:.4f} satuan³"),
        ("½ Bola",      ["Jari-jari:"],
         lambda v: f"V = (2/3)π×r³ = {(2/3)*math.pi*v[0]**3:.4f} satuan³"),
    ]
    return scene_shape_calc("VOLUME BANGUN RUANG", shapes, per_row=4)

# ─── KONVERSI SUHU ───────────────────────────────────────────────────────────
def scene_konversi_suhu():
    units = ['°C','°F','K','°Ra','°Re']
    def to_c(v, u):
        return {
            '°C': v, '°F': (v-32)*5/9, 'K': v-273.15,
            '°Ra': (v-491.67)*5/9, '°Re': v*5/4
        }[u]
    def from_c(c, u):
        return {
            '°C': c, '°F': c*9/5+32, 'K': c+273.15,
            '°Ra': (c+273.15)*9/5, '°Re': c*4/5
        }[u]
    per_row = 5; bw = (LEBAR-100)//per_row - 8
    unit_btns = [Button(50+i*(bw+8),155,bw,44,u) for i,u in enumerate(units)]
    i1 = InputBox(LEBAR//2-160,100,320,40,"Nilai:")
    btn_hit  = Button(LEBAR//2-85,215,170,45,"KONVERSI")
    btn_back = Button(40,640,160,50,"[ KEMBALI ]",(80,20,30),(140,40,40))
    btn_clr  = Button(LEBAR-210,640,160,50,"✕ Clear",(60,20,30),(120,40,40))
    selected = 0; hasil = []; copy_info = None
    while True:
        pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type==pygame.QUIT: return "keluar"
            if event.type==pygame.KEYDOWN and event.key==pygame.K_F11: toggle_fullscreen()
            if btn_back.clicked(pos,event): return "menu"
            if btn_clr.clicked(pos,event): i1.text=""; hasil=[]
            i1.handle_event(event)
            for i,btn in enumerate(unit_btns):
                if btn.clicked(pos,event): selected=i; hasil=[]
            if btn_hit.clicked(pos,event):
                try:
                    val=float(i1.text); c=to_c(val,units[selected])
                    hasil=[f"{val} {units[selected]} = {from_c(c,u):.4f} {u}"
                           for u in units if u!=units[selected]]
                    add_history("Konversi Suhu",{"nilai":i1.text,"dari":units[selected]},hasil[0])
                except: hasil=["ERROR: Input tidak valid"]
            if copy_info:
                _,cbr,ct=copy_info
                if event.type==pygame.MOUSEBUTTONDOWN and event.button==1 and cbr.collidepoint(pos):
                    copy_to_clipboard(ct); play_click()
        draw_bg(layar); draw_scene_header(layar,"KONVERSI SUHU")
        i1.draw(layar)
        render_text("Pilih satuan ( °C | °F | K | °Ra=Rankine | °Re=Réaumur )",
                    font_micro,ABU,50,142)
        for i,btn in enumerate(unit_btns):
            btn.active=(i==selected); btn.check_hover(pos); btn.draw(layar)
        btn_hit.check_hover(pos); btn_hit.draw(layar)
        if hasil: copy_info=draw_hasil_box(layar,hasil,285,is_list=True)
        btn_back.check_hover(pos); btn_back.draw(layar)
        btn_clr.check_hover(pos); btn_clr.draw(layar)
        pygame.display.flip(); clock.tick(FPS)

def scene_konversi_panjang():
    units=['mm','cm','dm','m','km','inci','kaki','yard','mil']
    factors={'mm':0.001,'cm':0.01,'dm':0.1,'m':1,'km':1000,
             'inci':0.0254,'kaki':0.3048,'yard':0.9144,'mil':1609.344}
    return scene_konversi_satuan("KONVERSI PANJANG",units,factors)

def scene_konversi_berat():
    units=['mg','g','kg','ton','lb','oz','stone','karat']
    factors={'mg':0.001,'g':1,'kg':1000,'ton':1_000_000,
             'lb':453.592,'oz':28.3495,'stone':6350.29,'karat':0.2}
    return scene_konversi_satuan("KONVERSI BERAT",units,factors)

# ─── SCENES 18-25 ────────────────────────────────────────────────────────────
def scene_pecahan():
    inputs=[InputBox(100,130,180,40,f"Pecahan {i+1}:") for i in range(4)]
    for i,inp in enumerate(inputs):
        inp.rect.x=100+(i%2)*500; inp.rect.y=130+(i//2)*90
    btns=[Button(LEBAR//2-210+i*140,310,130,50,op) for i,op in enumerate(["+","-","×","/"])]
    btn_back=Button(40,640,160,50,"[ KEMBALI ]",(80,20,30),(140,40,40))
    btn_clr=Button(LEBAR-210,640,160,50,"✕ Clear",(60,20,30),(120,40,40))
    hasil=""; copy_info=None
    while True:
        pos=pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type==pygame.QUIT: return "keluar"
            if event.type==pygame.KEYDOWN and event.key==pygame.K_F11: toggle_fullscreen()
            if btn_back.clicked(pos,event): return "menu"
            if btn_clr.clicked(pos,event):
                for inp in inputs: inp.text=""
                hasil=""
            for inp in inputs: inp.handle_event(event)
            for i,btn in enumerate(btns):
                if btn.clicked(pos,event):
                    try:
                        a=int(inputs[0].text); b=int(inputs[1].text)
                        c=int(inputs[2].text); d=int(inputs[3].text)
                        if b==0 or d==0: hasil="ERROR: Penyebut ≠ 0"; continue
                        ops=[(a*d+c*b,b*d),(a*d-c*b,b*d),(a*c,b*d),(a*d,b*c)]
                        num,den=ops[i]
                        g=math.gcd(abs(num),abs(den))
                        hasil=f"Hasil: {num//g}/{den//g}"
                        add_history("Pecahan",{"a/b":f"{a}/{b}","c/d":f"{c}/{d}"},hasil)
                    except: hasil="ERROR: Input tidak valid"
            if copy_info:
                _,cbr,ct=copy_info
                if event.type==pygame.MOUSEBUTTONDOWN and event.button==1 and cbr.collidepoint(pos):
                    copy_to_clipboard(ct); play_click()
        draw_bg(layar); draw_scene_header(layar,"OPERASI PECAHAN  (a/b op c/d)")
        render_text("a:",font_kecil,ABU,100,110); render_text("b:",font_kecil,ABU,600,110)
        render_text("c:",font_kecil,ABU,100,200); render_text("d:",font_kecil,ABU,600,200)
        for inp in inputs: inp.draw(layar)
        for btn in btns: btn.check_hover(pos); btn.draw(layar)
        if hasil: copy_info=draw_hasil_box(layar,hasil,390)
        btn_back.check_hover(pos); btn_back.draw(layar)
        btn_clr.check_hover(pos); btn_clr.draw(layar)
        pygame.display.flip(); clock.tick(FPS)

def scene_persentase():
    inputs=[InputBox(LEBAR//2-160,130,320,40,"Nilai:"),
            InputBox(LEBAR//2-160,205,320,40,"Persen (%):")]
    btns=[Button(250+i*220,280,200,50,lb) for i,lb in enumerate(["Hitung %","Dari Total","Beda %"])]
    btn_back=Button(40,640,160,50,"[ KEMBALI ]",(80,20,30),(140,40,40))
    btn_clr=Button(LEBAR-210,640,160,50,"✕ Clear",(60,20,30),(120,40,40))
    hasil=""; copy_info=None
    while True:
        pos=pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type==pygame.QUIT: return "keluar"
            if event.type==pygame.KEYDOWN and event.key==pygame.K_F11: toggle_fullscreen()
            if btn_back.clicked(pos,event): return "menu"
            if btn_clr.clicked(pos,event):
                for inp in inputs: inp.text=""
                hasil=""
            for inp in inputs: inp.handle_event(event)
            for i,btn in enumerate(btns):
                if btn.clicked(pos,event):
                    try:
                        val=float(inputs[0].text); pct=float(inputs[1].text)
                        rs=[f"{pct}% dari {val} = {val*pct/100:.4f}",
                            f"{val} adalah {pct}% dari {val*100/pct:.4f}",
                            f"Selisih {pct}% dari {val} = {val*pct/100:.4f}"]
                        hasil=rs[i]
                        add_history("Persentase",{"nilai":inputs[0].text,"pct":inputs[1].text},hasil)
                    except: hasil="ERROR: Input tidak valid"
            if copy_info:
                _,cbr,ct=copy_info
                if event.type==pygame.MOUSEBUTTONDOWN and event.button==1 and cbr.collidepoint(pos):
                    copy_to_clipboard(ct); play_click()
        draw_bg(layar); draw_scene_header(layar,"KALKULATOR PERSENTASE")
        for inp in inputs: inp.draw(layar)
        for btn in btns: btn.check_hover(pos); btn.draw(layar)
        if hasil: copy_info=draw_hasil_box(layar,hasil,360)
        btn_back.check_hover(pos); btn_back.draw(layar)
        btn_clr.check_hover(pos); btn_clr.draw(layar)
        pygame.display.flip(); clock.tick(FPS)

def scene_diskon_pajak():
    inputs=[InputBox(LEBAR//2-160,130,320,40,"Harga Awal:"),
            InputBox(LEBAR//2-160,205,320,40,"Diskon/Pajak (%):")]
    btns=[Button(300+i*250,280,200,50,lb) for i,lb in enumerate(["Hitung Diskon","Hitung Pajak"])]
    btn_back=Button(40,640,160,50,"[ KEMBALI ]",(80,20,30),(140,40,40))
    btn_clr=Button(LEBAR-210,640,160,50,"✕ Clear",(60,20,30),(120,40,40))
    hasil=""; copy_info=None
    while True:
        pos=pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type==pygame.QUIT: return "keluar"
            if event.type==pygame.KEYDOWN and event.key==pygame.K_F11: toggle_fullscreen()
            if btn_back.clicked(pos,event): return "menu"
            if btn_clr.clicked(pos,event):
                for inp in inputs: inp.text=""
                hasil=""
            for inp in inputs: inp.handle_event(event)
            for i,btn in enumerate(btns):
                if btn.clicked(pos,event):
                    try:
                        h=float(inputs[0].text); p=float(inputs[1].text)
                        val=h*p/100
                        hasil=(f"Diskon {p}% = {val:.2f}  →  Bayar: {h-val:.2f}" if i==0
                               else f"Pajak {p}% = {val:.2f}  →  Total: {h+val:.2f}")
                        add_history("Diskon & Pajak",{"harga":inputs[0].text,"pct":inputs[1].text},hasil)
                    except: hasil="ERROR: Input tidak valid"
            if copy_info:
                _,cbr,ct=copy_info
                if event.type==pygame.MOUSEBUTTONDOWN and event.button==1 and cbr.collidepoint(pos):
                    copy_to_clipboard(ct); play_click()
        draw_bg(layar); draw_scene_header(layar,"DISKON & PAJAK")
        for inp in inputs: inp.draw(layar)
        for btn in btns: btn.check_hover(pos); btn.draw(layar)
        if hasil: copy_info=draw_hasil_box(layar,hasil,360)
        btn_back.check_hover(pos); btn_back.draw(layar)
        btn_clr.check_hover(pos); btn_clr.draw(layar)
        pygame.display.flip(); clock.tick(FPS)

def scene_bunga_sederhana():
    inputs=[InputBox(LEBAR//2-160,100+i*70,320,40,lb)
            for i,lb in enumerate(["Modal:","Bunga (%/tahun):","Waktu (tahun):"])]
    btn_hit=Button(LEBAR//2-85,310,170,50,"HITUNG")
    btn_back=Button(40,640,160,50,"[ KEMBALI ]",(80,20,30),(140,40,40))
    btn_clr=Button(LEBAR-210,640,160,50,"✕ Clear",(60,20,30),(120,40,40))
    hasil=[]; copy_info=None
    while True:
        pos=pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type==pygame.QUIT: return "keluar"
            if event.type==pygame.KEYDOWN and event.key==pygame.K_F11: toggle_fullscreen()
            if btn_back.clicked(pos,event): return "menu"
            if btn_clr.clicked(pos,event):
                for inp in inputs: inp.text=""
                hasil=[]
            for inp in inputs: inp.handle_event(event)
            if btn_hit.clicked(pos,event):
                try:
                    p=float(inputs[0].text); r=float(inputs[1].text); t=float(inputs[2].text)
                    b=p*r*t/100
                    hasil=[f"Modal awal  : {p:.2f}",f"Bunga total : {b:.2f}",f"Total akhir : {p+b:.2f}"]
                    add_history("Bunga Sederhana",{"modal":inputs[0].text}," | ".join(hasil))
                except: hasil=["ERROR: Input tidak valid"]
            if copy_info:
                _,cbr,ct=copy_info
                if event.type==pygame.MOUSEBUTTONDOWN and event.button==1 and cbr.collidepoint(pos):
                    copy_to_clipboard(ct); play_click()
        draw_bg(layar); draw_scene_header(layar,"BUNGA SEDERHANA")
        for inp in inputs: inp.draw(layar)
        btn_hit.check_hover(pos); btn_hit.draw(layar)
        if hasil: copy_info=draw_hasil_box(layar,hasil,380,is_list=True)
        btn_back.check_hover(pos); btn_back.draw(layar)
        btn_clr.check_hover(pos); btn_clr.draw(layar)
        pygame.display.flip(); clock.tick(FPS)

def scene_fibonacci():
    i1=InputBox(LEBAR//2-160,150,320,40,"Jumlah suku (n):")
    btn_hit=Button(LEBAR//2-85,230,170,50,"HITUNG")
    btn_back=Button(40,640,160,50,"[ KEMBALI ]",(80,20,30),(140,40,40))
    btn_clr=Button(LEBAR-210,640,160,50,"✕ Clear",(60,20,30),(120,40,40))
    hasil=""; copy_info=None
    while True:
        pos=pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type==pygame.QUIT: return "keluar"
            if event.type==pygame.KEYDOWN and event.key==pygame.K_F11: toggle_fullscreen()
            if btn_back.clicked(pos,event): return "menu"
            if btn_clr.clicked(pos,event): i1.text=""; hasil=""
            i1.handle_event(event)
            if btn_hit.clicked(pos,event):
                try:
                    n=int(i1.text)
                    if n>60: hasil="ERROR: Maks 60 suku"; continue
                    if n<=0: hasil="ERROR: n > 0"; continue
                    fib=[0,1]
                    for _ in range(2,n): fib.append(fib[-1]+fib[-2])
                    hasil=f"Fibonacci ({n} suku): {', '.join(map(str,fib[:n]))}"
                    add_history("Fibonacci",{"n":i1.text},hasil[:60])
                except: hasil="ERROR: Input tidak valid"
            if copy_info:
                _,cbr,ct=copy_info
                if event.type==pygame.MOUSEBUTTONDOWN and event.button==1 and cbr.collidepoint(pos):
                    copy_to_clipboard(ct); play_click()
        draw_bg(layar); draw_scene_header(layar,"DERET FIBONACCI")
        i1.draw(layar); btn_hit.check_hover(pos); btn_hit.draw(layar)
        if hasil: copy_info=draw_hasil_box(layar,hasil,310)
        btn_back.check_hover(pos); btn_back.draw(layar)
        btn_clr.check_hover(pos); btn_clr.draw(layar)
        pygame.display.flip(); clock.tick(FPS)

def scene_barisan_aritmatika():
    labels=["Suku pertama (a):","Beda (b):","Cari Suku ke- (n):","Cari Jumlah Sn:"]
    inputs=[InputBox(LEBAR//2-160,100+i*60,320,40,lb) for i,lb in enumerate(labels)]
    btn_hit=Button(LEBAR//2-85,350,170,50,"HITUNG")
    btn_back=Button(40,640,160,50,"[ KEMBALI ]",(80,20,30),(140,40,40))
    btn_clr=Button(LEBAR-210,640,160,50,"✕ Clear",(60,20,30),(120,40,40))
    hasil=[]; copy_info=None
    while True:
        pos=pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type==pygame.QUIT: return "keluar"
            if event.type==pygame.KEYDOWN and event.key==pygame.K_F11: toggle_fullscreen()
            if btn_back.clicked(pos,event): return "menu"
            if btn_clr.clicked(pos,event):
                for inp in inputs: inp.text=""
                hasil=[]
            for inp in inputs: inp.handle_event(event)
            if btn_hit.clicked(pos,event):
                try:
                    a=float(inputs[0].text); b=float(inputs[1].text)
                    nu=int(inputs[2].text) if inputs[2].text else 0
                    ns=int(inputs[3].text) if inputs[3].text else 0
                    hasil=[]
                    if nu>0:
                        un=a+(nu-1)*b; hasil.append(f"U{nu} = {un:.4f}")
                    if ns>0:
                        sn=ns*(2*a+(ns-1)*b)/2; hasil.append(f"S{ns} = {sn:.4f}")
                    seq=[a+i*b for i in range(10)]
                    hasil.append(f"Preview: {', '.join(str(round(x,4)) for x in seq)}, ...")
                    add_history("Barisan Aritmatika",{"a":inputs[0].text,"b":inputs[1].text}," | ".join(hasil))
                except: hasil=["ERROR: Input tidak valid"]
            if copy_info:
                _,cbr,ct=copy_info
                if event.type==pygame.MOUSEBUTTONDOWN and event.button==1 and cbr.collidepoint(pos):
                    copy_to_clipboard(ct); play_click()
        draw_bg(layar); draw_scene_header(layar,"BARISAN ARITMATIKA")
        for inp in inputs: inp.draw(layar)
        btn_hit.check_hover(pos); btn_hit.draw(layar)
        if hasil: copy_info=draw_hasil_box(layar,hasil,420,is_list=True)
        btn_back.check_hover(pos); btn_back.draw(layar)
        btn_clr.check_hover(pos); btn_clr.draw(layar)
        pygame.display.flip(); clock.tick(FPS)

def scene_aritmatika_lanjutan():
    labels=["Suku ke- (n1):","Nilai Suku ke-n1:","Suku ke- (n2):","Nilai Suku ke-n2:","Target n:"]
    inputs=[InputBox(LEBAR//2-160,100+i*55,320,35,lb) for i,lb in enumerate(labels)]
    btn_hit=Button(LEBAR//2-85,385,170,45,"HITUNG")
    btn_back=Button(40,640,160,50,"[ KEMBALI ]",(80,20,30),(140,40,40))
    btn_clr=Button(LEBAR-210,640,160,50,"✕ Clear",(60,20,30),(120,40,40))
    hasil=[]; copy_info=None
    while True:
        pos=pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type==pygame.QUIT: return "keluar"
            if event.type==pygame.KEYDOWN and event.key==pygame.K_F11: toggle_fullscreen()
            if btn_back.clicked(pos,event): return "menu"
            if btn_clr.clicked(pos,event):
                for inp in inputs: inp.text=""
                hasil=[]
            for inp in inputs: inp.handle_event(event)
            if btn_hit.clicked(pos,event):
                try:
                    n1=int(inputs[0].text); un1=float(inputs[1].text)
                    n2=int(inputs[2].text); un2=float(inputs[3].text)
                    nt=int(inputs[4].text)
                    if n1==n2: hasil=["ERROR: n1 ≠ n2"]; continue
                    b=(un1-un2)/(n1-n2); a=un1-(n1-1)*b
                    ut=a+(nt-1)*b; st=nt*(2*a+(nt-1)*b)/2
                    hasil=[f"b = {b:.4f}  a = {a:.4f}",f"U{nt} = {ut:.4f}",f"S{nt} = {st:.4f}"]
                    add_history("Aritmatika Lanjutan",{}," | ".join(hasil))
                except: hasil=["ERROR: Masukkan angka valid"]
            if copy_info:
                _,cbr,ct=copy_info
                if event.type==pygame.MOUSEBUTTONDOWN and event.button==1 and cbr.collidepoint(pos):
                    copy_to_clipboard(ct); play_click()
        draw_bg(layar); draw_scene_header(layar,"ARITMATIKA (DIKETAHUI 2 SUKU)")
        for inp in inputs: inp.draw(layar)
        btn_hit.check_hover(pos); btn_hit.draw(layar)
        if hasil: copy_info=draw_hasil_box(layar,hasil,445,is_list=True)
        btn_back.check_hover(pos); btn_back.draw(layar)
        btn_clr.check_hover(pos); btn_clr.draw(layar)
        pygame.display.flip(); clock.tick(FPS)

def scene_barisan_geometri():
    labels=["Suku pertama (a):","Rasio (r):","Cari Suku ke- (n):","Cari Jumlah Sn:"]
    inputs=[InputBox(LEBAR//2-160,100+i*60,320,40,lb) for i,lb in enumerate(labels)]
    btn_hit=Button(LEBAR//2-85,350,170,50,"HITUNG")
    btn_back=Button(40,640,160,50,"[ KEMBALI ]",(80,20,30),(140,40,40))
    btn_clr=Button(LEBAR-210,640,160,50,"✕ Clear",(60,20,30),(120,40,40))
    hasil=[]; copy_info=None
    while True:
        pos=pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type==pygame.QUIT: return "keluar"
            if event.type==pygame.KEYDOWN and event.key==pygame.K_F11: toggle_fullscreen()
            if btn_back.clicked(pos,event): return "menu"
            if btn_clr.clicked(pos,event):
                for inp in inputs: inp.text=""
                hasil=[]
            for inp in inputs: inp.handle_event(event)
            if btn_hit.clicked(pos,event):
                try:
                    a=float(inputs[0].text); r=float(inputs[1].text)
                    nu=int(inputs[2].text) if inputs[2].text else 0
                    ns=int(inputs[3].text) if inputs[3].text else 0
                    if nu>250 or ns>250: hasil=["ERROR: n maks 250"]; continue
                    hasil=[]
                    if nu>0: hasil.append(f"U{nu} = {a*(r**(nu-1)):.4f}")
                    if ns>0:
                        sn=a*ns if r==1 else a*(1-r**ns)/(1-r)
                        hasil.append(f"S{ns} = {sn:.4f}")
                    seq=[a*(r**i) for i in range(10)]
                    hasil.append(f"Preview: {', '.join(f'{x:.4g}' for x in seq)}, ...")
                    add_history("Barisan Geometri",{"a":inputs[0].text,"r":inputs[1].text}," | ".join(hasil))
                except OverflowError: hasil=["ERROR: Overflow — angka terlalu besar"]
                except: hasil=["ERROR: Input tidak valid"]
            if copy_info:
                _,cbr,ct=copy_info
                if event.type==pygame.MOUSEBUTTONDOWN and event.button==1 and cbr.collidepoint(pos):
                    copy_to_clipboard(ct); play_click()
        draw_bg(layar); draw_scene_header(layar,"BARISAN GEOMETRI")
        for inp in inputs: inp.draw(layar)
        btn_hit.check_hover(pos); btn_hit.draw(layar)
        if hasil: copy_info=draw_hasil_box(layar,hasil,420,is_list=True)
        btn_back.check_hover(pos); btn_back.draw(layar)
        btn_clr.check_hover(pos); btn_clr.draw(layar)
        pygame.display.flip(); clock.tick(FPS)

def scene_kecepatan_jarak():
    inputs=[InputBox(LEBAR//2-160,130,320,40,"Nilai 1 (s/v):"),
            InputBox(LEBAR//2-160,205,320,40,"Nilai 2 (t/t):")]
    btns=[Button(180+i*245,280,225,50,lb) for i,lb in enumerate(["Kecepatan (s/t)","Jarak (v×t)","Waktu (s/v)"])]
    btn_back=Button(40,640,160,50,"[ KEMBALI ]",(80,20,30),(140,40,40))
    btn_clr=Button(LEBAR-210,640,160,50,"✕ Clear",(60,20,30),(120,40,40))
    hasil=""; copy_info=None
    while True:
        pos=pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type==pygame.QUIT: return "keluar"
            if event.type==pygame.KEYDOWN and event.key==pygame.K_F11: toggle_fullscreen()
            if btn_back.clicked(pos,event): return "menu"
            if btn_clr.clicked(pos,event):
                for inp in inputs: inp.text=""
                hasil=""
            for inp in inputs: inp.handle_event(event)
            for i,btn in enumerate(btns):
                if btn.clicked(pos,event):
                    try:
                        v1=float(inputs[0].text); v2=float(inputs[1].text)
                        rs=["ERROR: t≠0" if v2==0 else f"v=s/t={v1/v2:.4f}",
                            f"s=v×t={v1*v2:.4f}",
                            "ERROR: v≠0" if v2==0 else f"t=s/v={v1/v2:.4f}"]
                        hasil=rs[i]
                        add_history("Kecepatan & Jarak",{"v1":inputs[0].text,"v2":inputs[1].text},hasil)
                    except: hasil="ERROR: Input tidak valid"
            if copy_info:
                _,cbr,ct=copy_info
                if event.type==pygame.MOUSEBUTTONDOWN and event.button==1 and cbr.collidepoint(pos):
                    copy_to_clipboard(ct); play_click()
        draw_bg(layar); draw_scene_header(layar,"KECEPATAN, JARAK & WAKTU")
        for inp in inputs: inp.draw(layar)
        for btn in btns: btn.check_hover(pos); btn.draw(layar)
        if hasil: copy_info=draw_hasil_box(layar,hasil,360)
        btn_back.check_hover(pos); btn_back.draw(layar)
        btn_clr.check_hover(pos); btn_clr.draw(layar)
        pygame.display.flip(); clock.tick(FPS)

def scene_bmi():
    inputs=[InputBox(LEBAR//2-160,150,320,40,"Berat (kg):"),
            InputBox(LEBAR//2-160,225,320,40,"Tinggi (cm):")]
    btn_hit=Button(LEBAR//2-85,300,170,50,"HITUNG")
    btn_back=Button(40,640,160,50,"[ KEMBALI ]",(80,20,30),(140,40,40))
    btn_clr=Button(LEBAR-210,640,160,50,"✕ Clear",(60,20,30),(120,40,40))
    hasil=[]; copy_info=None
    while True:
        pos=pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type==pygame.QUIT: return "keluar"
            if event.type==pygame.KEYDOWN and event.key==pygame.K_F11: toggle_fullscreen()
            if btn_back.clicked(pos,event): return "menu"
            if btn_clr.clicked(pos,event):
                for inp in inputs: inp.text=""
                hasil=[]
            for inp in inputs: inp.handle_event(event)
            if btn_hit.clicked(pos,event):
                try:
                    bb=float(inputs[0].text); tb=float(inputs[1].text)/100
                    bmi=bb/tb**2
                    kat=("Kurus (Underweight)" if bmi<18.5 else
                         "Normal (Healthy)" if bmi<25 else
                         "Gemuk (Overweight)" if bmi<30 else "Obesitas")
                    hasil=[f"BMI = {bmi:.2f}", f"Kategori: {kat}"]
                    add_history("BMI",{"berat":inputs[0].text,"tinggi":inputs[1].text}," | ".join(hasil))
                except: hasil=["ERROR: Input tidak valid"]
            if copy_info:
                _,cbr,ct=copy_info
                if event.type==pygame.MOUSEBUTTONDOWN and event.button==1 and cbr.collidepoint(pos):
                    copy_to_clipboard(ct); play_click()
        draw_bg(layar); draw_scene_header(layar,"BMI CALCULATOR")
        for inp in inputs: inp.draw(layar)
        btn_hit.check_hover(pos); btn_hit.draw(layar)
        if hasil: copy_info=draw_hasil_box(layar,hasil,380,is_list=True)
        btn_back.check_hover(pos); btn_back.draw(layar)
        btn_clr.check_hover(pos); btn_clr.draw(layar)
        pygame.display.flip(); clock.tick(FPS)

def scene_konversi_waktu():
    units=['ms','detik','menit','jam','hari','minggu','bulan','tahun']
    factors={'ms':0.001,'detik':1,'menit':60,'jam':3600,
             'hari':86400,'minggu':604800,'bulan':2592000,'tahun':31536000}
    return scene_konversi_satuan("KONVERSI WAKTU",units,factors)

def scene_konversi_data():
    units=['bit','byte','KB','MB','GB','TB','PB']
    factors={'bit':1,'byte':8,'KB':8192,'MB':8_388_608,
             'GB':8_589_934_592,'TB':8_796_093_022_208,'PB':9_007_199_254_740_992}
    return scene_konversi_satuan("KONVERSI DATA (DIGITAL)",units,factors)

def scene_bilangan_kompleks():
    inputs=[InputBox(150+(i%2)*450,100+(i//2)*80,200,40,f"{lb}:")
            for i,lb in enumerate(["a1","b1","a2","b2"])]
    btns=[Button(250+i*200,280,180,50,op) for i,op in enumerate(["Tambah","Kurang","Kali"])]
    btn_back=Button(40,640,160,50,"[ KEMBALI ]",(80,20,30),(140,40,40))
    btn_clr=Button(LEBAR-210,640,160,50,"✕ Clear",(60,20,30),(120,40,40))
    hasil=""; copy_info=None
    while True:
        pos=pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type==pygame.QUIT: return "keluar"
            if event.type==pygame.KEYDOWN and event.key==pygame.K_F11: toggle_fullscreen()
            if btn_back.clicked(pos,event): return "menu"
            if btn_clr.clicked(pos,event):
                for inp in inputs: inp.text=""
                hasil=""
            for inp in inputs: inp.handle_event(event)
            for i,btn in enumerate(btns):
                if btn.clicked(pos,event):
                    try:
                        a1=float(inputs[0].text); b1=float(inputs[1].text)
                        a2=float(inputs[2].text); b2=float(inputs[3].text)
                        if i==0: hasil=f"({a1}+{b1}i)+({a2}+{b2}i) = {a1+a2}+{b1+b2}i"
                        elif i==1: hasil=f"({a1}+{b1}i)-({a2}+{b2}i) = {a1-a2}+{b1-b2}i"
                        elif i==2:
                            re=a1*a2-b1*b2; im=a1*b2+b1*a2
                            hasil=f"({a1}+{b1}i)×({a2}+{b2}i) = {re}+{im}i"
                        add_history("Bilangan Kompleks",{},hasil)
                    except: hasil="ERROR: Input tidak valid"
            if copy_info:
                _,cbr,ct=copy_info
                if event.type==pygame.MOUSEBUTTONDOWN and event.button==1 and cbr.collidepoint(pos):
                    copy_to_clipboard(ct); play_click()
        draw_bg(layar); draw_scene_header(layar,"BILANGAN KOMPLEKS (a+bi)")
        render_text("Z1:",font_kecil,CYAN_ACCENT,80,100)
        render_text("Z2:",font_kecil,CYAN_ACCENT,80,180)
        for inp in inputs: inp.draw(layar)
        for btn in btns: btn.check_hover(pos); btn.draw(layar)
        if hasil: copy_info=draw_hasil_box(layar,hasil,360)
        btn_back.check_hover(pos); btn_back.draw(layar)
        btn_clr.check_hover(pos); btn_clr.draw(layar)
        pygame.display.flip(); clock.tick(FPS)

def scene_determinan_3x3():
    inputs=[InputBox(50+j*180,100+i*70,150,40,f"a{i+1}{j+1}:")
            for i in range(3) for j in range(3)]
    btn_hit=Button(LEBAR//2-85,340,170,50,"HITUNG")
    btn_back=Button(40,640,160,50,"[ KEMBALI ]",(80,20,30),(140,40,40))
    btn_clr=Button(LEBAR-210,640,160,50,"✕ Clear",(60,20,30),(120,40,40))
    hasil=""; copy_info=None
    while True:
        pos=pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type==pygame.QUIT: return "keluar"
            if event.type==pygame.KEYDOWN and event.key==pygame.K_F11: toggle_fullscreen()
            if btn_back.clicked(pos,event): return "menu"
            if btn_clr.clicked(pos,event):
                for inp in inputs: inp.text=""
                hasil=""
            for inp in inputs: inp.handle_event(event)
            if btn_hit.clicked(pos,event):
                try:
                    m=[[float(inputs[i*3+j].text) for j in range(3)] for i in range(3)]
                    det=(m[0][0]*(m[1][1]*m[2][2]-m[1][2]*m[2][1])
                        -m[0][1]*(m[1][0]*m[2][2]-m[1][2]*m[2][0])
                        +m[0][2]*(m[1][0]*m[2][1]-m[1][1]*m[2][0]))
                    hasil=f"Det(A) = {det:.6f}"
                    add_history("Determinan 3x3",{},hasil)
                except: hasil="ERROR: Input tidak valid"
            if copy_info:
                _,cbr,ct=copy_info
                if event.type==pygame.MOUSEBUTTONDOWN and event.button==1 and cbr.collidepoint(pos):
                    copy_to_clipboard(ct); play_click()
        draw_bg(layar); draw_scene_header(layar,"DETERMINAN MATRIX 3x3")
        for inp in inputs: inp.draw(layar)
        btn_hit.check_hover(pos); btn_hit.draw(layar)
        if hasil: copy_info=draw_hasil_box(layar,hasil,415)
        btn_back.check_hover(pos); btn_back.draw(layar)
        btn_clr.check_hover(pos); btn_clr.draw(layar)
        pygame.display.flip(); clock.tick(FPS)

# ─── MAIN ────────────────────────────────────────────────────────────────────
def main():
    scene = "menu"
    scenes = {str(i): f for i, f in enumerate([
        scene_operasi_dasar, scene_pangkat_akar, scene_trigonometri, scene_logaritma,
        scene_faktorial, scene_persamaan_kuadrat, scene_konversi_suhu, scene_konversi_panjang,
        scene_konversi_berat, scene_sistem_bilangan, scene_statistik, scene_matrix,
        scene_bilangan_prima, scene_fpb_kpk, scene_pythagoras, scene_luas_bangun,
        scene_volume_bangun, scene_pecahan, scene_persentase, scene_diskon_pajak,
        scene_bunga_sederhana, scene_fibonacci, scene_barisan_aritmatika, scene_aritmatika_lanjutan,
        scene_barisan_geometri, scene_kecepatan_jarak, scene_bmi, scene_konversi_waktu,
        scene_konversi_data, scene_bilangan_kompleks, scene_determinan_3x3,
    ], 1)}
    while True:
        if scene == "menu":
            scene = menu_utama()
        elif scene in scenes:
            scene = scenes[scene]()
        elif scene == "keluar":
            break
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()