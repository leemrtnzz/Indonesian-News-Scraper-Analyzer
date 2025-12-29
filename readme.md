# 📰 Indonesian News Scraper & Analyzer

Aplikasi berbasis Python untuk melakukan *scraping* (pengambilan data) berita dari berbagai portal berita Indonesia, membersihkan data, mengekstraksi informasi penting (seperti estimasi kerugian, jumlah korban, lokasi), dan memvisualisasikan hasilnya.

Proyek ini dirancang untuk kebutuhan analisis data berita, tugas Business Intelligence (BI), atau pemantauan isu terkini.
> **⚠️ DISCLAIMER:** > Proyek ini dibuat hanya untuk tujuan **edukasi dan tugas kuliah**. Segala bentuk penyalahgunaan alat ini yang melanggar hukum atau merugikan pihak lain adalah tanggung jawab penuh pengguna. Penulis tidak bertanggung jawab atas dampak penggunaan alat ini. Gunakan dengan bijak dan etis.

## ✨ Fitur Utama

* **Multi-Source Scraping**: Mengambil berita dari berbagai sumber terpercaya (Kompas, Detik, CNBC, Bisnis, Kontan, NU Online, BBC, UGM).
* **Smart Cleaning & Extraction**:
* Pembersihan teks artikel.
* **Ekstraksi Entitas**: Otomatis mendeteksi estimasi kerugian finansial, jumlah korban, nama kecamatan, dan warga sipil.
* Pembersihan nama penulis dan format tanggal.


* **Data Export**: Menyimpan data dalam format **JSON** dan **CSV** (terpisah antara data mentah/raw dan data bersih/clean).
* **Auto Tagging**: Menghasilkan *hashtag* otomatis berdasarkan konten berita.
* **Visualisasi Data Interaktif**:
* Distribusi Topik (Bar Chart)
* Word Cloud (Isu Dominan)
* Tren Volume Berita (Line Chart)
* Scatter Plot (Hubungan Kerugian vs Korban)
* Distribusi Sumber Berita (Pie Chart)


* **CLI User Friendly**: Antarmuka berbasis menu terminal yang mudah digunakan.

## 📂 Struktur Proyek

Pastikan struktur folder proyek Anda seperti berikut agar kode berjalan lancar:

```text
.
├── clean_data/             # Folder output data bersih (dibuat otomatis)
├── raw_data/               # Folder output data mentah (dibuat otomatis)
├── output/                 # Folder output konversi CSV manual
├── utils/                  # Modul utilitas
│   ├── __init__.py
│   ├── banner.py           # Tampilan banner CLI
│   ├── cleaning.py         # Logika pembersihan & ekstraksi teks
│   └── visualize.py        # Logika pembuatan grafik (matplotlib/seaborn)
├── index.py                # File utama (Main Program)
├── requirements.txt        # Daftar library dependency
└── README.md               # Dokumentasi proyek

```

## 🚀 Instalasi & Persiapan

### Prasyarat

* Python 3.8 atau lebih baru.
* Koneksi internet (untuk scraping dan download artikel).

### Langkah Instalasi

1. **Clone repositori ini** (atau unduh file):
```bash
git clone https://github.com/leemrtnzz/Indonesian-News-Scraper-Analyzer.git
cd Indonesian-News-Scraper-Analyzer

```


2. **Buat Virtual Environment (Opsional tapi disarankan):**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

```


3. **Install Library yang Dibutuhkan:**
Gunakan file `requirements.txt` yang telah disediakan.
```bash
pip install -r requirements.txt

```



## 🛠️ Cara Penggunaan

Jalankan file utama menggunakan Python:

```bash
python index.py

```

Setelah program berjalan, Anda akan melihat menu utama:

### 1. Scraping Berita

* Pilih menu `1`.
* Masukkan kata kunci/topik yang ingin dicari (bisa lebih dari satu, pisahkan dengan koma).
* *Contoh:* `banjir demak, gempa cianjur, tanah longsor`


* Masukkan jumlah artikel yang ingin diambil per topik.
* Tunggu proses scraping selesai. Data akan otomatis tersimpan di folder `raw_data` dan `clean_data`.

### 2. Konversi JSON ke CSV (opsional)

* Pilih menu `2`.
* Menu ini berguna jika Anda ingin merapikan ulang atau mengubah file JSON hasil scraping menjadi format CSV yang siap diolah di Excel/Spreadsheet.
* Program akan mengekstraksi ulang kolom seperti `kecamatan` dan `jumlah_warga` jika belum ada.

### 3. Visualisasi Data

* Pilih menu `3`.
* Pilih file JSON yang ada di folder `clean_data`.
* Pilih jenis grafik yang ingin ditampilkan (WordCloud, Bar Chart, dll).

## 📊 Format Data Output

Data yang dihasilkan (CSV/JSON) akan memiliki kolom-kolom berikut:

| Kolom | Deskripsi |
| --- | --- |
| `topik` | Kata kunci pencarian. |
| `judul` | Judul artikel berita. |
| `konten_berita` | Isi berita yang sudah dibersihkan. |
| `author` | Penulis artikel. |
| `tanggal` | Tanggal publikasi. |
| `estimasi_kerugian` | Nilai kerugian (jika ditemukan dalam teks). |
| `estimasi_korban` | Jumlah korban jiwa/luka (jika ditemukan). |
| `jumlah_warga` | Jumlah warga terdampak (jika ditemukan). |
| `kecamatan` | Nama kecamatan yang disebut. |
| `tag` | Hashtag relevan yang diekstrak dari teks. |
| `link` | URL sumber berita. |

## ⚠️ Catatan

* **Rate Limiting**: Program menggunakan `time.sleep(random)` untuk menghindari pemblokiran IP oleh server berita. Jangan menghapus delay ini.
* **Akurasi Ekstraksi**: Ekstraksi (uang, korban, lokasi) menggunakan Regex dan NLP sederhana. Mungkin tidak 100% akurat untuk kalimat yang kompleks.

## 🤝 Kontribusi

Pull request dipersilakan. Untuk perubahan besar, harap buka *issue* terlebih dahulu untuk mendiskusikan apa yang ingin Anda ubah

## 📄 Lisensi

[MIT License](https://github.com/leemrtnzz/Indonesian-News-Scraper-Analyzer/blob/main/LICENSE).