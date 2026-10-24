# Discord Store Bot

Bot Discord untuk toko Robux dan jasa middleman. Bot ini mengelola panel produk, tiket order, log transaksi, statistik top buyer, testimoni, ulasan pembeli, cek stok, dan beberapa utilitas lain.

## Fitur

- **Panel produk** dengan alur: tombol produk → pricelist → tombol buat tiket.
- **Tiket order** untuk Robux dan Jasa Middleman, serta **tiket Ask** untuk tanya-jawab.
- **Sistem klaim tiket:** staff mengklaim tiket dan bisa melepas klaim. Kalau sudah diklaim, hanya pengklaim, pembeli, atau admin yang bisa menutup tiket.
- **Order log otomatis** dengan status Pending, Success, atau Failed, lengkap dengan foto profil pembeli.
- **Statistik top buyer** dengan panel dan navigasi halaman. Diperbarui otomatis setiap `!done`.
- **Testimoni** (`/testi`) dengan galeri foto bukti.
- **Ulasan (vouch)** dikirim otomatis ke pembeli lewat DM setelah order selesai.
- **Cek stok** dan pengaturan stok oleh admin.
- **Utilitas:** `!ping` (latensi bot), `!roblox` (profil akun Roblox), `!userinfo`, `!botinfo`, dan `!clear`.

## Persyaratan

- Python 3.10 atau lebih baru
- discord.py **2.7.1** atau lebih baru (panel memakai Components V2)
- Akun bot Discord yang sudah ditambahkan ke server dengan izin Administrator, atau minimal: Manage Channels, Manage Roles, Send Messages, Embed Links, Attach Files, dan Read Message History

### Intents yang harus diaktifkan

Buka [Discord Developer Portal](https://discord.com/developers/applications), pilih aplikasi bot, lalu buka **Bot → Privileged Gateway Intents**. Aktifkan:

- **Server Members Intent** (untuk mencari anggota dan memberi role)
- **Message Content Intent** (untuk command berawalan `!`)

## Instalasi

```bash
# 1. Clone repo
git clone https://github.com/USERNAME/discord-bot-store-indonesia.git
cd discord-bot-store-indonesia

# 2. Buat virtual environment (disarankan)
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux / macOS:
source venv/bin/activate

# 3. Pasang library
pip install -r requirements.txt

# 4. Buat file .env dari contoh, lalu isi token bot
cp .env.example .env
```

Isi file `.env`:

```env
DISCORD_TOKEN=token_bot_kamu
```

Jalankan bot:

```bash
python bot_discord.py
```

## Konfigurasi

Sebelum dipakai di server, ubah ID berikut di bagian atas `bot_discord.py` sesuai server kamu:

| Konstanta | Fungsi |
|---|---|
| `GUILD_ID` | ID server Discord |
| `CATEGORY_MARKET_ID` | Kategori tempat tiket dibuat |
| `ORDER_CHANNEL_ID` | Channel order (ditampilkan di `!stock`) |
| `ORDER_LOG_CHANNEL_ID` | Channel log order (history) |
| `VOUCH_CHANNEL_ID` | Channel ulasan / vouch |
| `TESTIMONY_CHANNEL_ID` | Channel tujuan `/testi` |

Role **Verified Buyer** dibuat otomatis oleh bot saat pertama kali `!done` dijalankan.

### Emoji custom

Bot memakai emoji custom. Upload emoji berikut ke server kamu, lalu ganti ID-nya di kode dengan ID emoji dari server kamu.

| Nama | Dipakai untuk |
|---|---|
| `robux`, `middleman`, `ask` | Tombol produk dan judul panel |
| `ewallet` | Keterangan QRIS di pricelist middleman |
| `pricelist`, `price`, `product`, `status`, `category`, `user`, `rating`, `star` | Ikon di dalam panel |
| `centang`, `sparkles`, `klaim`, `tutup`, `seru`, `pasir`, `gembok` | Notifikasi, tombol, dan status tiket |
| `stock_box`, `stock_ready`, `stock_empty`, `rate_tag` | Panel stok |
| `topbuyer`, `stats`, `totalorder`, `totalprofit`, `buyertotal` | Panel statistik |
| `success`, `pending`, `failed` | **Emoji animasi (GIF)**, dipakai di log order |
| `refresh` | **Emoji animasi (GIF)**, dipakai di `!setstock` |

Emoji animasi harus memakai format `<a:nama:id>`, bukan `<:nama:id>`. Kalau mengganti emoji, pastikan formatnya sesuai.

## Daftar Perintah

### Admin

| Perintah | Fungsi |
|---|---|
| `!setuptiket` | Memasang panel produk di channel |
| `!setupstats` | Membuat pesan statistik top buyer yang diperbarui otomatis |
| `!done <nominal>` | Menandai order di tiket sebagai Success, menghitung statistik, dan memberi role Verified Buyer. Contoh: `!done 16.000` |
| `!addstock <jumlah>` | Menambah stok |
| `!removestock <jumlah>` | Mengurangi stok (alias: `!minstock`, `!delstock`) |
| `!setstock <jumlah>` | Mengatur stok langsung |
| `!middleman` | Menampilkan info jasa middleman |
| `!clear <jumlah>` | Menghapus pesan di channel (alias: `!purge`) |

### Umum

| Perintah | Fungsi |
|---|---|
| `!stock` | Menampilkan status stok dan rate |
| `!stock <nominal>` | Mengecek apakah stok cukup untuk nominal tertentu |
| `!stats` | Menampilkan panel top buyer |
| `!officiallink` | Menampilkan link resmi toko |
| `!rbx` | Menghitung pajak Robux |
| `!roblox <username>` | Menampilkan profil akun Roblox |
| `!ping` | Menampilkan latensi bot |
| `!userinfo [@user]` | Menampilkan info pengguna (alias: `!ui`, `!user`) |
| `!botinfo` | Menampilkan info bot |
| `/testi` | Mengirim testimoni dengan foto bukti (slash command) |

## Alur Order

1. Pembeli menekan tombol produk di panel → melihat pricelist.
2. Pembeli menekan **Buat Tiket** → bot membuat channel tiket dan mencatat log dengan status **Pending**.
3. Staff menekan **Klaim Tiket**. Status tiket menampilkan siapa yang menangani.
4. Setelah transaksi selesai, admin menjalankan `!done <nominal>` di channel tiket.
   - Statistik dihitung dan panel top buyer diperbarui.
   - Log berubah menjadi **Success**.
   - Pembeli mendapat role **Verified Buyer**.
5. Tiket ditutup. Untuk tiket order, pembeli menerima DM berisi tombol untuk memberi ulasan.

Order yang sama tidak bisa di-`!done` dua kali.

## File Data

Bot menyimpan data dalam file JSON di folder tempat bot dijalankan. File ini dibuat otomatis:

| File | Isi |
|---|---|
| `stock_data.json` | Stok |
| `stats_data.json` | Statistik dan data pembeli untuk top buyer |
| `active_orders.json` | Order yang sedang berjalan |
| `order_log_counter.json` | Nomor urut log order |
| `ticket_claims.json` | Data tiket: pembeli, jenis, dan pengklaim |
| `testi_data.json` | Nomor urut testimoni |
| `vouch_counter.json` | Nomor urut ulasan |

File-file ini berisi data pembeli dan transaksi. **Jangan di-commit ke GitHub.** `.gitignore` sudah mengecualikannya. Simpan backup secara berkala jika data penting.

## Keamanan

- **Jangan pernah menulis token di kode atau mengunggahnya ke GitHub.** Simpan di file `.env` atau environment variable.
- Kalau token pernah terlihat publik, segera **Reset Token** di Developer Portal (Bot → Reset Token), lalu perbarui `.env`.
- Jika kode berisi ID atau data yang tidak ingin dibagikan, gunakan repo **Private**.

## Catatan

- Panel yang sudah terpasang di channel tidak berubah otomatis. Setelah update, jalankan ulang `!setuptiket` atau `!setupstats`.
- Tombol navigasi halaman top buyer hanya aktif selama bot berjalan. Setelah restart, panel diperbarui lewat `!done` atau `!stats`.
- Tiket yang dibuat sebelum sistem klaim diperbarui tidak punya data klaim, sehingga tombol klaimnya tidak bekerja. Tutup tiket seperti ini secara manual.

## Struktur Repo

```
discord-bot-store-indonesia/
├── bot_discord.py      # Kode utama bot
├── requirements.txt    # Daftar library
├── .env.example        # Contoh file konfigurasi token
├── .gitignore          # File yang tidak boleh di-commit
├── LICENSE             # Lisensi MIT
└── README.md           # Dokumentasi ini
```

## Lisensi

Proyek ini dilisensikan di bawah [MIT License](LICENSE).
