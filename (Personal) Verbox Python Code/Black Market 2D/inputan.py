import os
import json
import pygame
import threading
import time
import random
import vlc
from datetime import datetime

# Inisialisasi Pygame
pygame.init()

# Konstanta Layar
LEBAR = 1280
TINGGI = 720
FPS = 120

# Warna
HITAM = (0, 0, 0)
PUTIH = (255, 255, 255)
HIJAU = (0, 255, 0)
HIJAU_TUA = (0, 100, 0)
MERAH = (255, 0, 0)
KUNING = (255, 255, 0)
ABU = (128, 128, 128)
HIJAU_NEON = (57, 255, 20)
MERAH_GELAP = (139, 0, 0)

# Setup layar
layar = pygame.display.set_mode((LEBAR, TINGGI))
pygame.display.set_caption("Black Market 2D - Underground Trading")
clock = pygame.time.Clock()

# Font
font_besar = pygame.font.Font(None, 48)
font_sedang = pygame.font.Font(None, 36)
font_kecil = pygame.font.Font(None, 24)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ========== FUNGSI MUSIK ==========
def play_music():
    path = os.path.join(BASE_DIR, "bgm.mp3")
    if os.path.exists(path):
        player = vlc.MediaPlayer(path)
        player.play()
        player.audio_set_volume(50)
        while True:
            state = player.get_state()
            if state == vlc.State.Ended:
                player.stop()
                player.play()
                player.audio_set_volume(50)
            time.sleep(1)

music_thread = threading.Thread(target=play_music, daemon=True)
music_thread.start()

# ========== FUNGSI JSON ==========
def load_json(filename, default_value):
    file_path = os.path.join(BASE_DIR, filename)
    if not os.path.exists(file_path):
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(default_value, f, indent=4)
        return default_value
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(filename, data):
    file_path = os.path.join(BASE_DIR, filename)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# ========== DATA GAME ==========
stock = load_json("data barang black market.json", [])
organisasi = load_json("daftar organisasi.json", [])
saldo_data = load_json("uang.json", {"saldo": 10000})
saldo = saldo_data["saldo"]
aktivitas_organisasi_terakhir = {}

# ========== FUNGSI UTILITAS ==========
def save_stock_and_saldo():
    save_json("data barang black market.json", stock)
    save_json("uang.json", {"saldo": saldo})

def riwayat_transaksi(tipe, nama_barang, jumlah, total, effect=None):
    waktu = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_path = os.path.join(BASE_DIR, "transaksi_log.txt")
    with open(log_path, "a", encoding="utf-8") as log:
        log.write(f"[{waktu}] {tipe} {jumlah}x {nama_barang} - Total: ${total:,}\n")
        if effect:
            log.write(f"    └─ {effect}\n")

def baca_log():
    log_path = os.path.join(BASE_DIR, "transaksi_log.txt")
    if not os.path.exists(log_path):
        return []
    with open(log_path, "r", encoding="utf-8") as f:
        return f.readlines()

def baca_log_organisasi():
    log_path = os.path.join(BASE_DIR, "transaksi_organisasi_log.txt")
    if not os.path.exists(log_path):
        return []
    with open(log_path, "r", encoding="utf-8") as f:
        return f.readlines()

def fluktuasi_harga(produk, tipe):
    persen = random.randint(5, 95)
    if tipe == "beli":
        produk['harga'] = int(produk['harga'] * (1 + persen / 100))
        effect = f"Harga {produk['nama']} naik {persen}% jadi ${produk['harga']:,}!!!"
    elif tipe == "jual":
        produk['harga'] = int(produk['harga'] * (1 - persen / 100))
        if produk['harga'] < 1:
            produk['harga'] = 1
        effect = f"Harga {produk['nama']} turun {persen}% jadi ${produk['harga']:,}!!!"
    else:
        effect = ""
    return effect

def catat_aktivitas_organisasi(org, deskripsi, warna_tipe):
    global aktivitas_organisasi_terakhir
    aktivitas_organisasi_terakhir[org] = {"deskripsi": deskripsi, "warna": warna_tipe}
    log_path = os.path.join(BASE_DIR, "transaksi_organisasi_log.txt")
    waktu = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{waktu}] {org} {deskripsi}\n")

# ========== AKTIVITAS ORGANISASI (THREAD) ==========
def aktivitas_organisasi():
    while True:
        time.sleep(20)
        if not organisasi or not stock:
            continue
        
        org = random.choice(organisasi)
        produk = random.choice(stock)
        aksi = random.choice(["beli", "jual"])
        jumlah = random.randint(50, 1250)
        
        if aksi == "beli":
            produk_cocok = None
            for p in stock:
                if p["stok"] >= jumlah:
                    produk_cocok = p
                    break
            if not produk_cocok:
                continue
            produk = produk_cocok
            produk["stok"] -= jumlah
            total = produk["harga"] * jumlah
            deskripsi = f"membeli {jumlah:,} unit {produk['nama']} total: ${total:,}"
            warna_tipe = "hijau"
        else:
            produk["stok"] += jumlah
            total = (produk["harga"] // 2) * jumlah
            deskripsi = f"menjual {jumlah:,} unit {produk['nama']} total: ${total:,}"
            warna_tipe = "merah"
        
        save_json("data barang black market.json", stock)
        catat_aktivitas_organisasi(org, deskripsi, warna_tipe)

org_thread = threading.Thread(target=aktivitas_organisasi, daemon=True)
org_thread.start()

# ========== KELAS BUTTON ==========
class Button:
    def __init__(self, x, y, lebar, tinggi, teks, warna, warna_hover):
        self.rect = pygame.Rect(x, y, lebar, tinggi)
        self.teks = teks
        self.warna = warna
        self.warna_hover = warna_hover
        self.is_hovered = False
    
    def draw(self, surface):
        warna = self.warna_hover if self.is_hovered else self.warna
        pygame.draw.rect(surface, warna, self.rect, border_radius=10)
        pygame.draw.rect(surface, HIJAU_NEON, self.rect, 2, border_radius=10)
        
        teks_surf = font_kecil.render(self.teks, True, PUTIH)
        teks_rect = teks_surf.get_rect(center=self.rect.center)
        surface.blit(teks_surf, teks_rect)
    
    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
    
    def is_clicked(self, pos, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(pos)
        return False

# ========== KELAS SCROLLBAR ==========
class Scrollbar:
    def __init__(self, x, y, lebar, tinggi):
        self.x = x
        self.y = y
        self.lebar = lebar
        self.tinggi = tinggi
        self.track_rect = pygame.Rect(x, y, lebar, tinggi)
        self.thumb_rect = pygame.Rect(x, y, lebar, 50)
        self.dragging = False
        self.drag_offset = 0
    
    def update(self, total_items, visible_items, scroll_offset, item_height=80):
        if total_items <= visible_items:
            return scroll_offset
        
        # Calculate thumb size and position
        thumb_ratio = visible_items / total_items
        self.thumb_rect.height = max(30, int(self.tinggi * thumb_ratio))
        
        max_scroll = (total_items - visible_items) * item_height
        if max_scroll > 0:
            scroll_ratio = scroll_offset / max_scroll
            max_thumb_y = self.y + self.tinggi - self.thumb_rect.height
            self.thumb_rect.y = int(self.y + scroll_ratio * (self.tinggi - self.thumb_rect.height))
        
        return scroll_offset
    
    def handle_event(self, event, pos, total_items, visible_items, scroll_offset, item_height=80):
        if total_items <= visible_items:
            return scroll_offset
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.thumb_rect.collidepoint(pos):
                self.dragging = True
                self.drag_offset = pos[1] - self.thumb_rect.y
            elif self.track_rect.collidepoint(pos):
                # Click on track - jump to position
                rel_y = pos[1] - self.y
                scroll_ratio = rel_y / self.tinggi
                max_scroll = (total_items - visible_items) * item_height
                scroll_offset = int(scroll_ratio * max_scroll)
                scroll_offset = max(0, min(max_scroll, scroll_offset))
        
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            new_y = pos[1] - self.drag_offset
            new_y = max(self.y, min(new_y, self.y + self.tinggi - self.thumb_rect.height))
            
            scroll_ratio = (new_y - self.y) / (self.tinggi - self.thumb_rect.height)
            max_scroll = (total_items - visible_items) * item_height
            scroll_offset = int(scroll_ratio * max_scroll)
            scroll_offset = max(0, min(max_scroll, scroll_offset))
        
        return scroll_offset
    
    def draw(self, surface):
        # Draw track
        pygame.draw.rect(surface, (40, 40, 40), self.track_rect, border_radius=5)
        pygame.draw.rect(surface, HIJAU_TUA, self.track_rect, 1, border_radius=5)
        
        # Draw thumb
        pygame.draw.rect(surface, HIJAU_TUA, self.thumb_rect, border_radius=5)
        pygame.draw.rect(surface, HIJAU_NEON, self.thumb_rect, 2, border_radius=5)

# ========== FUNGSI RENDER TEKS ==========
def render_teks(teks, font, warna, x, y, center=False):
    surf = font.render(teks, True, warna)
    if center:
        rect = surf.get_rect(center=(x, y))
    else:
        rect = surf.get_rect(topleft=(x, y))
    layar.blit(surf, rect)

# ========== SCENE MENU UTAMA ==========
def menu_utama():
    buttons = [
        Button(LEBAR//2 - 200, 180, 400, 60, "Beli Barang Illegal", HIJAU_TUA, HIJAU),
        Button(LEBAR//2 - 200, 250, 400, 60, "Jual Barang Illegal", HIJAU_TUA, HIJAU),
        Button(LEBAR//2 - 200, 320, 400, 60, "Lihat Stock Barang", HIJAU_TUA, HIJAU),
        Button(LEBAR//2 - 200, 390, 400, 60, "Daftar Organisasi Underground", HIJAU_TUA, HIJAU),
        Button(LEBAR//2 - 200, 460, 400, 60, "Riwayat Transaksi Anda", HIJAU_TUA, HIJAU),
        Button(LEBAR//2 - 200, 530, 400, 60, "Riwayat Transaksi Organisasi", HIJAU_TUA, HIJAU),
        Button(LEBAR//2 - 200, 600, 400, 60, "Keluar", MERAH_GELAP, MERAH),
    ]
    
    # Particle effect (optional stars background)
    particles = []
    for _ in range(50):
        particles.append({
            'x': random.randint(0, LEBAR),
            'y': random.randint(0, TINGGI),
            'speed': random.uniform(0.1, 0.5)
        })
    
    while True:
        pos_mouse = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "keluar"
            
            for i, btn in enumerate(buttons):
                if btn.is_clicked(pos_mouse, event):
                    if i == 0: return "beli"
                    elif i == 1: return "jual"
                    elif i == 2: return "stock"
                    elif i == 3: return "organisasi"
                    elif i == 4: return "riwayat"
                    elif i == 5: return "riwayat_org"
                    elif i == 6: return "keluar"
        
        # Update particles
        for p in particles:
            p['y'] += p['speed']
            if p['y'] > TINGGI:
                p['y'] = 0
                p['x'] = random.randint(0, LEBAR)
        
        # Render
        layar.fill(HITAM)
        
        # Draw particles (stars)
        for p in particles:
            pygame.draw.circle(layar, (100, 100, 100), (int(p['x']), int(p['y'])), 1)
        
        # Border frame
        pygame.draw.rect(layar, HIJAU_NEON, (20, 20, LEBAR-40, TINGGI-40), 3, border_radius=15)
        pygame.draw.rect(layar, HIJAU_TUA, (25, 25, LEBAR-50, TINGGI-50), 1, border_radius=15)
        
        # Title with shadow effect
        render_teks("BLACK MARKET", font_besar, (0, 80, 0), LEBAR//2 + 3, 83, center=True)
        render_teks("BLACK MARKET", font_besar, HIJAU_NEON, LEBAR//2, 80, center=True)
        
        # Subtitle
        render_teks("Underground Trading Simulator", font_kecil, HIJAU, LEBAR//2, 130, center=True)
        render_teks("Pilihan di tangan anda", font_kecil, ABU, LEBAR//2, 155, center=True)
        
        # Saldo box
        saldo_rect = pygame.Rect(LEBAR - 390, 30, 360, 50)
        pygame.draw.rect(layar, HIJAU_TUA, saldo_rect, border_radius=10)
        pygame.draw.rect(layar, KUNING, saldo_rect, 2, border_radius=10)
        render_teks(f"Saldo Anda: ${saldo:,}", font_sedang, KUNING, LEBAR - 210, 55, center=True)
        
        # Buttons
        for btn in buttons:
            btn.check_hover(pos_mouse)
            btn.draw(layar)
        
        pygame.display.flip()
        clock.tick(FPS)

# ========== SCENE BELI BARANG ==========
def scene_beli():
    global saldo
    scroll_offset = 0
    selected_item = None
    jumlah_input = ""
    pesan = ""
    pesan_timer = 0
    
    btn_kembali = Button(50, TINGGI - 80, 150, 50, "Kembali", MERAH_GELAP, MERAH)
    btn_beli = Button(LEBAR - 200, TINGGI - 80, 150, 50, "Beli", HIJAU_TUA, HIJAU)
    scrollbar = Scrollbar(LEBAR - 70, 120, 20, TINGGI - 240)
    
    while True:
        pos_mouse = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "keluar"
            if btn_kembali.is_clicked(pos_mouse, event):
                return "menu"
            
            # Handle scrollbar
            visible_items = (TINGGI - 200) // 80
            scroll_offset = scrollbar.handle_event(event, pos_mouse, len(stock), visible_items, scroll_offset)
            
            if btn_beli.is_clicked(pos_mouse, event) and selected_item is not None and jumlah_input.isdigit():
                jumlah = int(jumlah_input)
                produk = stock[selected_item]
                total = jumlah * produk['harga']
                
                if jumlah <= produk['stok']:
                    if saldo >= total:
                        produk['stok'] -= jumlah
                        saldo -= total
                        effect = fluktuasi_harga(produk, "beli")
                        save_stock_and_saldo()
                        riwayat_transaksi("beli", produk['nama'], jumlah, total, effect)
                        pesan = f"[OK] Berhasil beli {jumlah}x {produk['nama']}! {effect}"
                        pesan_timer = 180
                        jumlah_input = ""
                    else:
                        pesan = "[X] Saldo tidak cukup!"
                        pesan_timer = 120
                else:
                    pesan = "[X] Stok tidak mencukupi!"
                    pesan_timer = 120
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    scroll_offset = max(0, scroll_offset - 30)
                elif event.button == 5:
                    scroll_offset = min(max(0, len(stock) * 80 - (TINGGI - 200)), scroll_offset + 30)
                
                for i in range(len(stock)):
                    item_rect = pygame.Rect(50, 150 + i * 80 - scroll_offset, LEBAR - 120, 70)
                    if item_rect.collidepoint(pos_mouse) and item_rect.top > 100 and item_rect.bottom < TINGGI - 100:
                        selected_item = i
            
            if event.type == pygame.KEYDOWN:
                if selected_item is not None:
                    if event.key == pygame.K_BACKSPACE:
                        jumlah_input = jumlah_input[:-1]
                    elif event.unicode.isdigit():
                        jumlah_input += event.unicode
        
        # Update scrollbar position
        visible_items = (TINGGI - 200) // 80
        scroll_offset = scrollbar.update(len(stock), visible_items, scroll_offset)
        
        layar.fill(HITAM)
        
        # Border
        pygame.draw.rect(layar, HIJAU_NEON, (20, 20, LEBAR-40, TINGGI-40), 3, border_radius=15)
        
        render_teks("BELI BARANG ILLEGAL", font_besar, HIJAU_NEON, LEBAR//2, 50, center=True)
        pygame.draw.line(layar, HIJAU, (100, 90), (LEBAR-100, 90), 2)
        render_teks(f"Saldo: ${saldo:,}", font_sedang, KUNING, LEBAR - 220, 50)
        
        # List barang
        for i, produk in enumerate(stock):
            y_pos = 150 + i * 80 - scroll_offset
            if y_pos < 100 or y_pos > TINGGI - 100:
                continue
            
            warna_bg = HIJAU_TUA if i == selected_item else (30, 30, 30)
            pygame.draw.rect(layar, warna_bg, (50, y_pos, LEBAR - 120, 70), border_radius=8)
            pygame.draw.rect(layar, HIJAU_NEON if i == selected_item else HIJAU_TUA, (50, y_pos, LEBAR - 120, 70), 2, border_radius=8)
            
            render_teks(f"{produk['nama']}", font_sedang, PUTIH, 70, y_pos + 10)
            render_teks(f"Stok: {produk['stok']:,} | Harga: ${produk['harga']:,}", font_kecil, HIJAU, 70, y_pos + 45)
        
        # Draw scrollbar
        if len(stock) > visible_items:
            scrollbar.draw(layar)
        
        # Input jumlah
        if selected_item is not None:
            input_rect = pygame.Rect(LEBAR//2 - 150, TINGGI - 150, 300, 40)
            pygame.draw.rect(layar, HIJAU_TUA, input_rect, border_radius=8)
            pygame.draw.rect(layar, KUNING, input_rect, 2, border_radius=8)
            render_teks(f"Jumlah: {jumlah_input}_", font_sedang, KUNING, LEBAR//2, TINGGI - 130, center=True)
        
        # Pesan
        if pesan_timer > 0:
            warna_pesan = HIJAU if "[OK]" in pesan else MERAH
            render_teks(pesan, font_kecil, warna_pesan, LEBAR//2, TINGGI - 180, center=True)
            pesan_timer -= 1
        
        btn_kembali.check_hover(pos_mouse)
        btn_kembali.draw(layar)
        btn_beli.check_hover(pos_mouse)
        btn_beli.draw(layar)
        
        pygame.display.flip()
        clock.tick(FPS)

# ========== SCENE JUAL BARANG ==========
def scene_jual():
    global saldo
    scroll_offset = 0
    selected_item = None
    jumlah_input = ""
    pesan = ""
    pesan_timer = 0
    
    btn_kembali = Button(50, TINGGI - 80, 150, 50, "Kembali", MERAH_GELAP, MERAH)
    btn_jual = Button(LEBAR - 200, TINGGI - 80, 150, 50, "Jual", HIJAU_TUA, HIJAU)
    scrollbar = Scrollbar(LEBAR - 70, 120, 20, TINGGI - 240)
    
    while True:
        pos_mouse = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "keluar"
            if btn_kembali.is_clicked(pos_mouse, event):
                return "menu"
            
            # Handle scrollbar
            visible_items = (TINGGI - 200) // 80
            scroll_offset = scrollbar.handle_event(event, pos_mouse, len(stock), visible_items, scroll_offset)
            
            if btn_jual.is_clicked(pos_mouse, event) and selected_item is not None and jumlah_input.isdigit():
                jumlah = int(jumlah_input)
                produk = stock[selected_item]
                produk['stok'] += jumlah
                total = jumlah * (produk['harga'] // 2)
                saldo += total
                effect = fluktuasi_harga(produk, "jual")
                save_stock_and_saldo()
                riwayat_transaksi("jual", produk['nama'], jumlah, total, effect)
                pesan = f"[OK] Berhasil jual {jumlah}x {produk['nama']} dapat ${total:,}! {effect}"
                pesan_timer = 180
                jumlah_input = ""
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    scroll_offset = max(0, scroll_offset - 30)
                elif event.button == 5:
                    scroll_offset = min(max(0, len(stock) * 80 - (TINGGI - 200)), scroll_offset + 30)
                
                for i in range(len(stock)):
                    item_rect = pygame.Rect(50, 150 + i * 80 - scroll_offset, LEBAR - 120, 70)
                    if item_rect.collidepoint(pos_mouse) and item_rect.top > 100 and item_rect.bottom < TINGGI - 100:
                        selected_item = i
            
            if event.type == pygame.KEYDOWN:
                if selected_item is not None:
                    if event.key == pygame.K_BACKSPACE:
                        jumlah_input = jumlah_input[:-1]
                    elif event.unicode.isdigit():
                        jumlah_input += event.unicode
        
        # Update scrollbar position
        visible_items = (TINGGI - 200) // 80
        scroll_offset = scrollbar.update(len(stock), visible_items, scroll_offset)
        
        layar.fill(HITAM)
        
        # Border
        pygame.draw.rect(layar, HIJAU_NEON, (20, 20, LEBAR-40, TINGGI-40), 3, border_radius=15)
        
        render_teks("JUAL BARANG ILLEGAL", font_besar, HIJAU_NEON, LEBAR//2, 50, center=True)
        pygame.draw.line(layar, HIJAU, (100, 90), (LEBAR-100, 90), 2)
        render_teks(f"Saldo: ${saldo:,}", font_sedang, KUNING, LEBAR - 220, 50)
        
        for i, produk in enumerate(stock):
            y_pos = 150 + i * 80 - scroll_offset
            if y_pos < 100 or y_pos > TINGGI - 100:
                continue
            
            warna_bg = HIJAU_TUA if i == selected_item else (30, 30, 30)
            pygame.draw.rect(layar, warna_bg, (50, y_pos, LEBAR - 120, 70), border_radius=8)
            pygame.draw.rect(layar, HIJAU_NEON if i == selected_item else HIJAU_TUA, (50, y_pos, LEBAR - 120, 70), 2, border_radius=8)
            
            render_teks(f"{produk['nama']}", font_sedang, PUTIH, 70, y_pos + 10)
            render_teks(f"Harga jual: ${produk['harga']//2:,} (50% dari harga pasar)", font_kecil, KUNING, 70, y_pos + 45)
        
        # Draw scrollbar
        if len(stock) > visible_items:
            scrollbar.draw(layar)
        
        if selected_item is not None:
            input_rect = pygame.Rect(LEBAR//2 - 150, TINGGI - 150, 300, 40)
            pygame.draw.rect(layar, HIJAU_TUA, input_rect, border_radius=8)
            pygame.draw.rect(layar, KUNING, input_rect, 2, border_radius=8)
            render_teks(f"Jumlah: {jumlah_input}_", font_sedang, KUNING, LEBAR//2, TINGGI - 130, center=True)
        
        if pesan_timer > 0:
            render_teks(pesan, font_kecil, HIJAU, LEBAR//2, TINGGI - 180, center=True)
            pesan_timer -= 1
        
        btn_kembali.check_hover(pos_mouse)
        btn_kembali.draw(layar)
        btn_jual.check_hover(pos_mouse)
        btn_jual.draw(layar)
        
        pygame.display.flip()
        clock.tick(FPS)

# ========== SCENE LIHAT STOCK ==========
def scene_stock():
    scroll_offset = 0
    btn_kembali = Button(LEBAR//2 - 75, TINGGI - 80, 150, 50, "Kembali", MERAH_GELAP, MERAH)
    scrollbar = Scrollbar(LEBAR - 70, 140, 20, TINGGI - 250)
    
    while True:
        pos_mouse = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "keluar"
            if btn_kembali.is_clicked(pos_mouse, event):
                return "menu"
            
            # Handle scrollbar
            visible_items = (TINGGI - 250) // 80
            scroll_offset = scrollbar.handle_event(event, pos_mouse, len(stock), visible_items, scroll_offset)
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    scroll_offset = max(0, scroll_offset - 30)
                elif event.button == 5:
                    scroll_offset = min(max(0, len(stock) * 80 - (TINGGI - 250)), scroll_offset + 30)
        
        # Update scrollbar position
        visible_items = (TINGGI - 250) // 80
        scroll_offset = scrollbar.update(len(stock), visible_items, scroll_offset)
        
        layar.fill(HITAM)
        
        # Border
        pygame.draw.rect(layar, HIJAU_NEON, (20, 20, LEBAR-40, TINGGI-40), 3, border_radius=15)
        
        render_teks("STOCK BARANG ILLEGAL", font_besar, HIJAU_NEON, LEBAR//2, 50, center=True)
        pygame.draw.line(layar, HIJAU, (100, 90), (LEBAR-100, 90), 2)
        render_teks(f"Saldo Anda: ${saldo:,}", font_sedang, KUNING, LEBAR//2, 105, center=True)
        
        for i, produk in enumerate(stock):
            y_pos = 150 + i * 80 - scroll_offset
            if y_pos < 140 or y_pos > TINGGI - 100:
                continue
            
            pygame.draw.rect(layar, (30, 30, 30), (50, y_pos, LEBAR - 120, 70), border_radius=8)
            pygame.draw.rect(layar, HIJAU_TUA, (50, y_pos, LEBAR - 120, 70), 2, border_radius=8)
            
            render_teks(f"{i+1}. {produk['nama']}", font_sedang, PUTIH, 70, y_pos + 10)
            render_teks(f"Stok: {produk['stok']:,} unit | Harga: ${produk['harga']:,}", font_kecil, HIJAU, 70, y_pos + 45)
        
        # Draw scrollbar
        if len(stock) > visible_items:
            scrollbar.draw(layar)
        
        btn_kembali.check_hover(pos_mouse)
        btn_kembali.draw(layar)
        
        pygame.display.flip()
        clock.tick(FPS)

# ========== SCENE ORGANISASI ==========
def scene_organisasi():
    scroll_offset = 0
    btn_kembali = Button(LEBAR//2 - 75, TINGGI - 80, 150, 50, "Kembali", MERAH_GELAP, MERAH)
    scrollbar = Scrollbar(LEBAR - 70, 130, 20, TINGGI - 240)
    
    while True:
        pos_mouse = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "keluar"
            if btn_kembali.is_clicked(pos_mouse, event):
                return "menu"
            
            # Handle scrollbar (90 is item height for organisasi)
            visible_items = (TINGGI - 240) // 90
            scroll_offset = scrollbar.handle_event(event, pos_mouse, len(organisasi), visible_items, scroll_offset, item_height=90)
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    scroll_offset = max(0, scroll_offset - 30)
                elif event.button == 5:
                    scroll_offset = min(max(0, len(organisasi) * 90 - (TINGGI - 240)), scroll_offset + 30)
        
        # Update scrollbar position
        visible_items = (TINGGI - 240) // 90
        scroll_offset = scrollbar.update(len(organisasi), visible_items, scroll_offset, item_height=90)
        
        layar.fill(HITAM)
        
        # Border
        pygame.draw.rect(layar, HIJAU_NEON, (20, 20, LEBAR-40, TINGGI-40), 3, border_radius=15)
        
        render_teks("ORGANISASI UNDERGROUND", font_besar, HIJAU_NEON, LEBAR//2, 50, center=True)
        pygame.draw.line(layar, HIJAU, (100, 90), (LEBAR-100, 90), 2)
        render_teks("LIVE - Aktivitas Real-Time", font_kecil, MERAH, LEBAR//2, 105, center=True)
        
        for i, org in enumerate(organisasi):
            y_pos = 140 + i * 90 - scroll_offset
            if y_pos < 130 or y_pos > TINGGI - 100:
                continue
            
            pygame.draw.rect(layar, (30, 30, 30), (50, y_pos, LEBAR - 120, 80), border_radius=8)
            pygame.draw.rect(layar, HIJAU_TUA, (50, y_pos, LEBAR - 120, 80), 2, border_radius=8)
            
            render_teks(f"{i+1}. {org}", font_sedang, PUTIH, 70, y_pos + 10)
            
            if org in aktivitas_organisasi_terakhir:
                aktivitas = aktivitas_organisasi_terakhir[org]
                warna = HIJAU if aktivitas["warna"] == "hijau" else MERAH
                icon = "[BELI]" if aktivitas["warna"] == "hijau" else "[JUAL]"
                render_teks(f"{icon} {aktivitas['deskripsi']}", font_kecil, warna, 70, y_pos + 50)
            else:
                render_teks("Belum ada aktivitas terbaru", font_kecil, ABU, 70, y_pos + 50)
        
        # Draw scrollbar
        if len(organisasi) > visible_items:
            scrollbar.draw(layar)
        
        btn_kembali.check_hover(pos_mouse)
        btn_kembali.draw(layar)
        
        pygame.display.flip()
        clock.tick(FPS)

# ========== SCENE RIWAYAT ==========
def scene_riwayat():
    btn_kembali = Button(LEBAR//2 - 75, TINGGI - 80, 150, 50, "Kembali", MERAH_GELAP, MERAH)
    scroll_offset = 0
    scrollbar = Scrollbar(LEBAR - 70, 110, 20, TINGGI - 220)
    
    log_path = os.path.join(BASE_DIR, "transaksi_log.txt")
    logs = []
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as f:
            logs = f.readlines()
    
    while True:
        pos_mouse = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "keluar"
            if btn_kembali.is_clicked(pos_mouse, event):
                return "menu"
            
            # Handle scrollbar (25 is item height for logs)
            visible_items = (TINGGI - 220) // 25
            scroll_offset = scrollbar.handle_event(event, pos_mouse, len(logs), visible_items, scroll_offset, item_height=25)
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    scroll_offset = max(0, scroll_offset - 20)
                elif event.button == 5:
                    scroll_offset = min(max(0, len(logs) * 25 - (TINGGI - 220)), scroll_offset + 20)
        
        # Update scrollbar position
        visible_items = (TINGGI - 220) // 25
        scroll_offset = scrollbar.update(len(logs), visible_items, scroll_offset, item_height=25)
        
        layar.fill(HITAM)
        
        # Border
        pygame.draw.rect(layar, HIJAU_NEON, (20, 20, LEBAR-40, TINGGI-40), 3, border_radius=15)
        
        # Title
        render_teks("RIWAYAT TRANSAKSI ANDA", font_besar, HIJAU_NEON, LEBAR//2, 50, center=True)
        pygame.draw.line(layar, HIJAU, (100, 90), (LEBAR-100, 90), 2)
        
        # Content box
        content_rect = pygame.Rect(50, 110, LEBAR-120, TINGGI-220)
        pygame.draw.rect(layar, (20, 20, 20), content_rect, border_radius=10)
        pygame.draw.rect(layar, HIJAU_TUA, content_rect, 2, border_radius=10)
        
        if logs:
            for i, log in enumerate(logs):
                y_pos = 130 + i * 25 - scroll_offset
                if y_pos < 110 or y_pos > TINGGI - 110:
                    continue
                
                # Color code based on transaction type
                if "beli" in log.lower():
                    warna = HIJAU
                elif "jual" in log.lower():
                    warna = KUNING
                else:
                    warna = PUTIH
                
                render_teks(log.strip(), font_kecil, warna, 70, y_pos)
        else:
            render_teks("Belum ada transaksi tercatat.", font_sedang, ABU, LEBAR//2, TINGGI//2, center=True)
            render_teks("Mulai berdagang untuk melihat riwayat!", font_kecil, HIJAU_TUA, LEBAR//2, TINGGI//2 + 40, center=True)
        
        # Draw scrollbar
        if len(logs) > visible_items:
            scrollbar.draw(layar)
        
        btn_kembali.check_hover(pos_mouse)
        btn_kembali.draw(layar)
        
        pygame.display.flip()
        clock.tick(FPS)

# ========== SCENE RIWAYAT ORGANISASI ==========
def scene_riwayat_organisasi():
    btn_kembali = Button(LEBAR//2 - 75, TINGGI - 80, 150, 50, "Kembali", MERAH_GELAP, MERAH)
    scroll_offset = 0
    scrollbar = Scrollbar(LEBAR - 70, 120, 20, TINGGI - 230)
    
    logs = baca_log_organisasi()
    
    while True:
        pos_mouse = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "keluar"
            if btn_kembali.is_clicked(pos_mouse, event):
                return "menu"
            
            # Handle scrollbar (25 is item height for logs)
            visible_items = (TINGGI - 230) // 25
            scroll_offset = scrollbar.handle_event(event, pos_mouse, len(logs), visible_items, scroll_offset, item_height=25)
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    scroll_offset = max(0, scroll_offset - 20)
                elif event.button == 5:
                    scroll_offset = min(max(0, len(logs) * 25 - (TINGGI - 230)), scroll_offset + 20)
        
        # Update scrollbar position
        visible_items = (TINGGI - 230) // 25
        scroll_offset = scrollbar.update(len(logs), visible_items, scroll_offset, item_height=25)
        
        layar.fill(HITAM)
        
        # Border
        pygame.draw.rect(layar, HIJAU_NEON, (20, 20, LEBAR-40, TINGGI-40), 3, border_radius=15)
        
        # Title
        render_teks("RIWAYAT TRANSAKSI ORGANISASI", font_besar, HIJAU_NEON, LEBAR//2, 50, center=True)
        pygame.draw.line(layar, HIJAU, (100, 90), (LEBAR-100, 90), 2)
        
        # Subtitle
        render_teks("Aktivitas Underground Market", font_kecil, HIJAU, LEBAR//2, 100, center=True)
        
        # Content box
        content_rect = pygame.Rect(50, 120, LEBAR-120, TINGGI-230)
        pygame.draw.rect(layar, (20, 20, 20), content_rect, border_radius=10)
        pygame.draw.rect(layar, HIJAU_TUA, content_rect, 2, border_radius=10)
        
        if logs:
            for i, log in enumerate(logs):
                y_pos = 140 + i * 25 - scroll_offset
                if y_pos < 120 or y_pos > TINGGI - 110:
                    continue
                
                # Color code based on transaction type
                if "membeli" in log.lower():
                    warna = HIJAU
                    icon = "[BELI]"
                elif "menjual" in log.lower():
                    warna = MERAH
                    icon = "[JUAL]"
                else:
                    warna = PUTIH
                    icon = ""
                
                render_teks(f"{icon} {log.strip()}", font_kecil, warna, 70, y_pos)
        else:
            render_teks("Belum ada aktivitas organisasi tercatat.", font_sedang, ABU, LEBAR//2, TINGGI//2, center=True)
            render_teks("Tunggu beberapa saat untuk melihat pergerakan market!", font_kecil, HIJAU_TUA, LEBAR//2, TINGGI//2 + 40, center=True)
        
        # Draw scrollbar
        if len(logs) > visible_items:
            scrollbar.draw(layar)
        
        btn_kembali.check_hover(pos_mouse)
        btn_kembali.draw(layar)
        
        pygame.display.flip()
        clock.tick(FPS)

# ========== MAIN LOOP ==========
def main():
    scene = "menu"
    
    while True:
        if scene == "menu":
            scene = menu_utama()
        elif scene == "beli":
            scene = scene_beli()
        elif scene == "jual":
            scene = scene_jual()
        elif scene == "stock":
            scene = scene_stock()
        elif scene == "organisasi":
            scene = scene_organisasi()
        elif scene == "riwayat":
            scene = scene_riwayat()
        elif scene == "riwayat_org":
            scene = scene_riwayat_organisasi()
        elif scene == "keluar":
            break
    
    pygame.quit()

if __name__ == "__main__":
    main()