# Data awal stock
stock = [
    {"nama": "Pistol", "stok": 5, "harga": 5000000},
    {"nama": "Granat", "stok": 2, "harga": 2000000},
    {"nama": "Armor", "stok": 3, "harga": 750000},
]

organisasi = ["Shadow Clan", "Black Lotus", "Ghost Syndicate"]

# Saldo user
saldo = 10000000  


def tampilkan_stok():
    print("\n=== Stok Barang ===")
    for i, produk in enumerate(stock, start=1):
        print(f"{i}. {produk['nama']} - Stok: {produk['stok']} - Harga: {produk['harga']}")
    print(f"\nSaldo Anda: {saldo}")


def beli_barang():
    global saldo
    tampilkan_stok()
    pilihan = int(input("\nPilih nomor barang yang ingin dibeli: "))
    if pilihan < 1 or pilihan > len(stock):
        print("Pilihan tidak valid!")
        return

    produk = stock[pilihan - 1]
    jumlah = int(input(f"Masukkan jumlah {produk['nama']} yang ingin dibeli: "))

    total = jumlah * produk['harga']

    if jumlah <= produk['stok']:
        if saldo >= total:
            produk['stok'] -= jumlah
            saldo -= total
            print(f"Anda membeli {jumlah} {produk['nama']} seharga {total}")
            print(f"Sisa saldo: {saldo}")
        else:
            print("[X] Saldo tidak cukup!")
    else:
        print("[X] Stok tidak mencukupi!")


def jual_barang():
    global saldo
    tampilkan_stok()
    pilihan = int(input("\nPilih nomor barang yang ingin dijual: "))
    if pilihan < 1 or pilihan > len(stock):
        print("Pilihan tidak valid!")
        return

    produk = stock[pilihan - 1]
    jumlah = int(input(f"Masukkan jumlah {produk['nama']} yang ingin dijual: "))

    produk['stok'] += jumlah
    total = jumlah * (produk['harga'] // 2)  
    saldo += total
    print(f"Anda menjual {jumlah} {produk['nama']} dan mendapat {total}")
    print(f"Saldo sekarang: {saldo}")


def lihat_organisasi():
    print("\n=== Daftar Organisasi Underground ===")
    for i, org in enumerate(organisasi, start=1):
        print(f"{i}. {org}")


def menu():
    while True:
        print("\n=== Black Market ===")
        print("1. Beli barang")
        print("2. Jual barang")
        print("3. Lihat stock barang")
        print("4. Lihat daftar organisasi 'underground'")
        print("5. Keluar")

        pilihan = input("anda mau kemana? (1/2/3/4/5) pilihan di tangan anda...")

        if pilihan == "1":
            beli_barang()
        elif pilihan == "2":
            jual_barang()
        elif pilihan == "3":
            tampilkan_stok()
        elif pilihan == "4":
            lihat_organisasi()
        elif pilihan == "5":
            print("Anda keluar dari Black Market... sampai jumpa nanti -_o💰")
            break
        else:
            print("[X] Pilihan tidak valid!")

if __name__=="__main__":
    menu()