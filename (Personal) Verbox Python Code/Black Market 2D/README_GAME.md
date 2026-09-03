# Black Market 2D - Underground Trading Simulator

## 🎮 Deskripsi
Game simulasi trading pasar gelap versi 2D dengan interface grafis menggunakan Pygame. 
Fitur utama:
- Interface grafis interaktif dengan mouse
- Background musik otomatis loop
- Sistem trading real-time
- AI organisasi yang aktif berdagang
- Animasi dan efek visual

## 📋 Requirement

### Library yang dibutuhkan:
```bash
pip install pygame
pip install python-vlc
```

### File yang diperlukan:
1. `black_market_2d.py` (file utama game)
2. `bgm.mp3` (file musik background - letakkan di folder yang sama)
3. `data barang black market.json` (otomatis dibuat jika belum ada)
4. `daftar organisasi.json` (otomatis dibuat jika belum ada)
5. `uang.json` (otomatis dibuat jika belum ada)

## 🚀 Cara Menjalankan

### 1. Install dependencies:
```bash
pip install pygame python-vlc
```

### 2. Jalankan game:
```bash
python black_market_2d.py
```

## 🎯 Cara Bermain

### Kontrol:
- **Mouse**: Klik pada button/item untuk memilih
- **Scroll Wheel**: Scroll daftar barang/organisasi
- **Keyboard**: Ketik angka untuk jumlah beli/jual

### Menu Utama:
1. **Beli Barang Illegal** - Beli barang dari pasar
2. **Jual Barang Illegal** - Jual barang yang Anda punya
3. **Lihat Stock Barang** - Cek semua barang dan harga
4. **Daftar Organisasi Underground** - Monitor aktivitas organisasi (live update)
5. **Riwayat Transaksi** - Lihat log transaksi Anda
6. **Keluar** - Tutup game

### Tips:
- Harga berfluktuasi setelah setiap transaksi (5%-95%)
- Beli saat harga rendah, jual saat harga tinggi
- Perhatikan aktivitas organisasi untuk memprediksi harga
- Jual harga = 50% dari harga beli

## 📁 Struktur File JSON

### data barang black market.json
```json
[
    {
        "nama": "AK-47",
        "stok": 100,
        "harga": 5000
    }
]
```

### daftar organisasi.json
```json
[
    "Yakuza",
    "Mafia Rusia",
    "Cartel Mexico"
]
```

### uang.json
```json
{
    "saldo": 10000
}
```

## 🎨 Fitur Tambahan dari Versi Console:

✅ Interface grafis full 2D
✅ Mouse support
✅ Scrolling untuk list panjang
✅ Visual feedback (warna hijau/merah)
✅ Live update organisasi dengan warna indikator
✅ Pesan notifikasi untuk setiap aksi
✅ Design modern dengan border radius dan gradasi warna

## 🐛 Troubleshooting

### Masalah: "ModuleNotFoundError: No module named 'pygame'"
**Solusi**: 
```bash
pip install pygame
```

### Masalah: "ModuleNotFoundError: No module named 'vlc'"
**Solusi**: 
```bash
pip install python-vlc
```

### Masalah: Musik tidak berfungsi
**Solusi**: 
- Pastikan file `bgm.mp3` ada di folder yang sama dengan `black_market_2d.py`
- Install VLC media player di komputer Anda
- Jika tetap tidak berfungsi, game tetap bisa dimainkan tanpa musik

### Masalah: Game lag/patah-patah
**Solusi**: 
- Kurangi FPS di baris `FPS = 60` menjadi `FPS = 30`
- Tutup aplikasi lain yang berat

## 📝 Catatan

- Game ini menyimpan data secara otomatis setiap kali transaksi
- Log transaksi tersimpan di `transaksi_log.txt`
- Log organisasi tersimpan di `transaksi_organisasi_log.txt`
- Organisasi melakukan trading otomatis setiap 20 detik

## 🎮 Screenshot Gameplay
```
┌─────────────────────────────────┐
│     BLACK MARKET               │
│  Underground Trading Simulator  │
│                                 │
│  ┌──────────────────────────┐  │
│  │ Beli Barang Illegal      │  │
│  ├──────────────────────────┤  │
│  │ Jual Barang Illegal      │  │
│  ├──────────────────────────┤  │
│  │ Lihat Stock Barang       │  │
│  ├──────────────────────────┤  │
│  │ Daftar Organisasi        │  │
│  ├──────────────────────────┤  │
│  │ Riwayat Transaksi        │  │
│  ├──────────────────────────┤  │
│  │ Keluar                   │  │
│  └──────────────────────────┘  │
│                                 │
│   Saldo Anda: $10,000          │
└─────────────────────────────────┘
```

Selamat bermain! 🎲💰
