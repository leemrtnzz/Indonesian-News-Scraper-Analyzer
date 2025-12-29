import pandas as pd
from ddgs import DDGS
from newspaper import Article, Config
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
from collections import Counter
from utils.banner import banner
import re
import time
import random
import json
import os
from datetime import datetime
from utils.cleaning import clean_author, extract_kecamatan, extract_warga_sipil, clean_date, clean_content, extract_financial_loss, extract_victim_count, get_hashtags, extract_aid
from utils.visualize import (
    plot_topic_distribution, 
    generate_wordcloud, 
    plot_news_volume_trend, 
    plot_impact_scatter, 
    plot_source_distribution
)


DAFTAR_TOPIK = []

TARGET_JUMLAH_ARTIKEL = 100
OUTPUT_FILENAME = "data_tugas_bi.json"
OUTPUT_CSV_FILENAME = "data_tugas_bi.csv"
RAW_FOLDER = "raw_data"
CLEAN_FOLDER = "clean_data"


def save_to_json(data_list, filename):
    """Menyimpan list of dict ke JSON."""
    if not data_list:
        print("[WARNING] Tidak ada data untuk disimpan!")
        return False
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data_list, f, indent=4, ensure_ascii=False)
        print(f"[SAVED] {len(data_list)} data berhasil disimpan ke {filename}")
        return True
    except Exception as e:
        print(f"[ERROR] Gagal menyimpan JSON: {e}")
        return False

def save_to_csv(data_list, filename):
    """Konversi dan simpan ke CSV dengan kolom terpisah."""
    if not data_list:
        print("[WARNING] Tidak ada data untuk dikonversi!")
        return False
    try:
        df = pd.DataFrame(data_list)
        # Pastikan urutan kolom konsisten
        column_order = ['topik', 'judul', 'konten_berita', 'author', 'tanggal', 
                       'estimasi_kerugian', 'estimasi_bantuan', 'estimasi_korban', 'jumlah_warga', 'kecamatan', 'tag', 'link']
        
        # Reorder kolom jika ada
        existing_cols = [col for col in column_order if col in df.columns]
        df = df[existing_cols]
        
        df.to_csv(filename, index=False, encoding='utf-8-sig', sep=',')
        print(f"[SAVED] Data berhasil dikonversi ke CSV: {filename}")
        print(f"        Total baris: {len(df)}, Total kolom: {len(df.columns)}")
        return True
    except Exception as e:
        print(f"[ERROR] Gagal menyimpan CSV: {e}")
        return False

def scrape_topic(topic, limit=TARGET_JUMLAH_ARTIKEL):
    """Proses utama per topik"""
    print(f"\n[{topic}] Memulai pencarian...")
    
    query = f"{topic} (site:kompas.com OR site:detik.com OR site:cnbcindonesia.com OR site:bisnis.com OR site:kontan.co.id OR site:nu.or.id OR site:BBC.com OR site:ugm.ac.id)"
    
    collected_data = []
    collected_raw_data = [] # Buffer untuk data mentah
    news_config = Config()
    news_config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    news_config.request_timeout = 15
    news_config.fetch_images = False
    news_config.memoize_articles = False
    
    success_count = 0
    full_text_buffer = "" 
    
    try:
        with DDGS() as ddgs:
            search_generator = ddgs.text(query, region='id-id', max_results=limit + 20, safesearch='moderate')
            
            for result in search_generator:
                if success_count >= limit:
                    break
                
                url = result['href']
                try:
                    time.sleep(random.uniform(1.5, 3.0))
                    
                    article = Article(url, language='id', config=news_config)
                    article.download()
                    article.parse()
                    
                    if len(article.text) < 200:
                        continue

                    # --- DATA MENTAH (RAW) ---
                    # Simpan data apa adanya sebelum cleansing
                    raw_item = {
                        "topik": topic,
                        "judul": article.title,
                        "konten_berita": article.text, # Teks asli
                        "author": str(article.authors), # Author asli
                        "tanggal": str(article.publish_date), # Tanggal asli
                        "link": url
                    }
                    collected_raw_data.append(raw_item)
                    
                    # --- CLEANING PROCESS ---
                    cleaned_content = clean_content(article.text)
                    cleaned_author = clean_author(article.authors)
                    cleaned_date = clean_date(article.publish_date)
                    
                    estimasi_rugi = extract_financial_loss(cleaned_content)
                    estimasi_bantuan = extract_aid(cleaned_content)
                    estimasi_korban = extract_victim_count(cleaned_content)
                    kecamatan_found = extract_kecamatan(cleaned_content)
                    warga_found = extract_warga_sipil(cleaned_content)
                    
                    full_text_buffer += cleaned_content + " "
                    
                    item = {
                        "topik": topic,
                        "judul": article.title,
                        "konten_berita": cleaned_content,
                        "author": cleaned_author,
                        "tanggal": cleaned_date,
                        "estimasi_kerugian": estimasi_rugi,
                        "estimasi_bantuan": estimasi_bantuan,
                        "estimasi_korban": estimasi_korban,
                        "jumlah_warga": warga_found, 
                        "kecamatan": kecamatan_found, 
                        "tag": "",
                        "link": url
                    }
                    collected_data.append(item)
                    print(f"   -> [OK] {article.title[:30]}... | Rugi:{estimasi_rugi} | Bantuan:{estimasi_bantuan} | Korban:{estimasi_korban} | Kec:{kecamatan_found}")
                    success_count += 1
                    
                except Exception as e:
                    print(f"[ERROR] Failed to process {url}: {e}")
                    continue
                
    except Exception as e:
        print(f"[{topic}] Error saat searching: {e}")

    if full_text_buffer:
        top_hashtags = get_hashtags(full_text_buffer, 7)
        for data in collected_data:
            data["tag"] = top_hashtags
        # Opsional: tambahkan tag ke raw data juga jika diinginkan, atau biarkan kosong
        for raw in collected_raw_data:
            raw["tag"] = top_hashtags
            
    return collected_data, collected_raw_data

# ==========================================
# 3. FUNGSI KONVERSI JSON KE CSV
# ==========================================

def json_to_csv_converter():
    """Konversi file JSON ke CSV dengan struktur kolom yang benar"""
    print("\n╭" + " - "*10 + "╮")
    print("┊ KONVERSI JSON KE CSV")
    print("╰" + " - "*10 + "╯")
    folder_output = 'output'
    
    json_file = input(f"Masukkan nama file JSON (default: {os.path.join(CLEAN_FOLDER, "clean_"+OUTPUT_FILENAME)}): ").strip()
    if not json_file:
        json_file = os.path.join(CLEAN_FOLDER, "clean_"+OUTPUT_FILENAME)
    
    if not os.path.exists(json_file):
        print(f"[ERROR] File {json_file} tidak ditemukan!")
        return
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not data:
            print("[ERROR] File JSON kosong!")
            return
        
        print(f"[INFO] Berhasil membaca {len(data)} data dari {json_file}")
        
        csv_file = input("Masukkan nama file CSV output (default: clean_data_tugas_bi.csv): ").strip()
        if not os.path.exists(folder_output):
            os.makedirs(folder_output)
        if not csv_file:
            csv_file = folder_output + "/clean_"+OUTPUT_FILENAME.replace('.json', '.csv')
        
        # Konversi ke DataFrame dengan kolom terpisah
        df = pd.DataFrame(data)
        
        # 1. Cleaning Author ulang
        if 'author' in df.columns:
            print("[INFO] Membersihkan nama author...")
            df['author'] = df['author'].apply(clean_author)

        # 2. Ekstraksi Fitur Baru (jika belum ada atau untuk update)
        if 'konten_berita' in df.columns:
            print("[INFO] Melakukan ekstraksi entitas tambahan (Kecamatan, Warga, Bantuan)...")
            # Pastikan kolom ada, jika belum ada buat baru
            if 'kecamatan' not in df.columns:
                df['kecamatan'] = ""
            if 'jumlah_warga' not in df.columns:
                df['jumlah_warga'] = ""
            if 'estimasi_bantuan' not in df.columns:
                df['estimasi_bantuan'] = ""
            
            # Apply extraction
            df['kecamatan'] = df['konten_berita'].apply(extract_kecamatan)
            df['jumlah_warga'] = df['konten_berita'].apply(extract_warga_sipil)
            # Re-run extraction for aid/loss to ensure updates apply to existing json too
            df['estimasi_bantuan'] = df['konten_berita'].apply(extract_aid)
            df['estimasi_kerugian'] = df['konten_berita'].apply(extract_financial_loss)

        # 3. Reorder Columns agar rapi
        column_order = ['topik', 'judul', 'konten_berita', 'author', 'tanggal', 
                       'estimasi_kerugian', 'estimasi_bantuan', 'estimasi_korban', 'jumlah_warga', 'kecamatan', 'tag', 'link']
        
        # Filter kolom yang benar-benar ada di DataFrame
        existing_cols = [col for col in column_order if col in df.columns]
        # Tambahkan kolom lain yang mungkin tidak ada di list urutan (opsional, biar gak hilang)
        remaining_cols = [col for col in df.columns if col not in existing_cols]
        
        df = df[existing_cols + remaining_cols]
        
        # Tampilkan info struktur
        print(f"\n[INFO] Struktur data:")
        print(f"       Total baris: {len(df)}")
        print(f"       Total kolom: {len(df.columns)}")
        print(f"       Kolom: {', '.join(df.columns.tolist())}")
        
        # Simpan ke CSV
        df.to_csv(csv_file, index=False, encoding='utf-8-sig', sep=',')
        print(f"\n[SUCCESS] Konversi berhasil! File disimpan: {csv_file}")
        print(f"          Setiap atribut sudah dalam kolom terpisah.")
        
    except json.JSONDecodeError as e:
        print(f"[ERROR] File JSON tidak valid: {e}")
    except Exception as e:
        print(f"[ERROR] Gagal konversi: {e}")

# ==========================================
# 4. MENU UTAMA
# ==========================================

def tampilkan_menu():
    """Menampilkan menu utama"""
    banner()
    print ("╭ - - - - - - - - - - - - - - - - - - - ╮")
    print ("┊ MENU                                  ┊")
    print ("┊- - - - - - - - - - - - - - - - - - -  ┊")
    print ("┊ [ 1 ] Scraping Berita (Input Topik)   ┊")
    print ("┊ [ 2 ] Konversi JSON ke CSV            ┊")
    print ("┊ [ 3 ] Visualisasi Data                ┊")
    print ("┊ [ 4 ] Keluar                          ┊")
    print ("╰ - - - - - - - - - - - - - - - - - - - ╯")

def jalankan_scraping():
    """Menu untuk scraping dengan input topik dinamis"""
    print("\n╭" + " - "*10 + "╮")
    print("┊ SCRAPING BERITA" + " "*14 + "┊")
    print("╰" + " - "*10 + "╯")
    
    print("\nMasukkan topik yang ingin di-scrape (pisahkan dengan koma):")
    print("Contoh: banjir sumatra, bencana padang, pohon sumatra")
    
    input_topik = input("\nTopik: ").strip()
    
    if not input_topik:
        print("[ERROR] Topik tidak boleh kosong!")
        return
    
    # Split berdasarkan koma dan bersihkan whitespace
    daftar_topik = [topik.strip() for topik in input_topik.split(',') if topik.strip()]
    
    if not daftar_topik:
        print("[ERROR] Tidak ada topik valid yang dimasukkan!")
        return
    
    print(f"\n[INFO] Total topik yang akan di-scrape: {len(daftar_topik)}")
    for i, topik in enumerate(daftar_topik, 1):
        print(f"       {i}. {topik}")
    
    # Konfirmasi
    konfirmasi = input("\nLanjutkan scraping? (y/n): ").strip().lower()
    if konfirmasi != 'y':
        print("[CANCELLED] Scraping dibatalkan.")
        return
    
    # Tanya jumlah artikel per topik
    try:
        jumlah = input(f"\nJumlah artikel per topik (default: {TARGET_JUMLAH_ARTIKEL}): ").strip()
        if jumlah:
            jumlah_artikel = int(jumlah)
        else:
            jumlah_artikel = TARGET_JUMLAH_ARTIKEL
    except ValueError:
        print("[WARNING] Input tidak valid, menggunakan default.")
        jumlah_artikel = TARGET_JUMLAH_ARTIKEL
    
    print(f"\n[START] Memulai scraping {jumlah_artikel} artikel per topik...")
    
    all_clean_buffer = []
    all_raw_buffer = []
    
    # Proses scraping
    for topik in daftar_topik:
        clean_result, raw_result = scrape_topic(topik, jumlah_artikel)
        
        if clean_result:
            all_clean_buffer.extend(clean_result)
            all_raw_buffer.extend(raw_result)
            print(f"[{topik}] Berhasil: {len(clean_result)} artikel.")
        else:
            print(f"[{topik}] Tidak ada artikel yang berhasil di-scrape.")
        
        print("Istirahat 5 detik...")
        time.sleep(5)
    
    # Simpan hasil
    if all_clean_buffer:
        print(f"\n[SAVING] Menyimpan data...")

        # --- PREPARE FOLDERS ---
        if not os.path.exists(RAW_FOLDER):
            os.makedirs(RAW_FOLDER)
        if not os.path.exists(CLEAN_FOLDER):
            os.makedirs(CLEAN_FOLDER)

        # --- SAVE RAW DATA ---
        raw_json_path = os.path.join(RAW_FOLDER, f"raw_{OUTPUT_FILENAME}")
        raw_csv_path = os.path.join(RAW_FOLDER, f"raw_{OUTPUT_CSV_FILENAME}")
        
        print(f"[RAW] Menyimpan data mentah ke folder '{RAW_FOLDER}'...")
        save_to_json(all_raw_buffer, raw_json_path)
        save_to_csv(all_raw_buffer, raw_csv_path)

        # --- SAVE CLEAN DATA ---
        clean_json_path = os.path.join(CLEAN_FOLDER, f"clean_{OUTPUT_FILENAME}")
        clean_csv_path = os.path.join(CLEAN_FOLDER, f"clean_{OUTPUT_CSV_FILENAME}")
        
        print(f"[CLEAN] Menyimpan data bersih ke folder '{CLEAN_FOLDER}'...")
        save_to_json(all_clean_buffer, clean_json_path)
        save_to_csv(all_clean_buffer, clean_csv_path)
        
        print(f"\n[SUCCESS] Scraping selesai!")
    else:
        print("\n[WARNING] Tidak ada data yang berhasil di-scrape!")

def jalankan_visualisasi():
    """Menu untuk visualisasi data"""
    print("\n╭" + " - "*15 + "╮")
    print("┊ VISUALISASI DATA" + " "*28 + "┊")
    print("┊" + " - "*15 + "┊")
    # 1. Pilih File
    if not os.path.exists(CLEAN_FOLDER):
        print(f"[ERROR] Folder {CLEAN_FOLDER} belum ada.")
        return

    files = [f for f in os.listdir(CLEAN_FOLDER) if f.endswith('.json')]
    if not files:
        print(f"[ERROR] Tidak ada file JSON di {CLEAN_FOLDER}.")
        return

    print("┊ Pilih file data untuk divisualisasikan:" + " "*5 + "┊")
    for i, f in enumerate(files, 1):
        print(f"┊ [{i}]. {f}")
    print("╰" + " - "*15 + "╯")
    
    try:
        choice = int(input("\nPilihan (nomor): ").strip())
        if 1 <= choice <= len(files):
            filename = os.path.join(CLEAN_FOLDER, files[choice-1])
        else:
            print("[ERROR] Pilihan tidak valid.")
            return
    except ValueError:
        print("[ERROR] Input harus angka.")
        return

    # 2. Load Data
    try:
        print(f"\n[INFO] Membaca data dari {filename}...")
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        df = pd.DataFrame(data)
        print(f"[INFO] Data berhasil dimuat: {len(df)} baris.")
    except Exception as e:
        print(f"[ERROR] Gagal membaca data: {e}")
        return

    # 3. Menu Visualisasi
    while True:
        print("\n╭" + " - "*15 + "╮")
        print("┊ MENU VISUALISASI" + " "*28 + "┊")
        print("┊" + " - "*15 + "┊")
        print("┊ [ 1 ]. Distribusi Topik (Bar Chart)         ┊")
        print("┊ [ 2 ]. Word Cloud Isu Dominan               ┊")
        print("┊ [ 3 ]. Tren Volume Berita (Line Chart)      ┊")
        print("┊ [ 4 ]. Scatter Plot: Kerugian vs Korban     ┊")
        print("┊ [ 5 ]. Distribusi Sumber Berita (Pie Chart) ┊")
        print("┊ [ 6 ]. Kembali ke Menu Utama                ┊")
        print("╰" + " - "*15 + "╯")

        
        viz_choice = input("\nPilih visualisasi (1-6): ").strip()
        
        if viz_choice == '1':
            plot_topic_distribution(df)
        elif viz_choice == '2':
            generate_wordcloud(df)
        elif viz_choice == '3':
            plot_news_volume_trend(df)
        elif viz_choice == '4':
            plot_impact_scatter(df)
        elif viz_choice == '5':
            plot_source_distribution(df)
        elif viz_choice == '6':
            break
        else:
            print("Pilihan tidak valid.")

def main():
    """Fungsi utama untuk menjalankan program"""
    while True:
        tampilkan_menu()
        
        pilihan = input("\nPilih menu (1-3): ").strip()
        
        if pilihan == '1':
            jalankan_scraping()
        elif pilihan == '2':
            json_to_csv_converter()
        elif pilihan == '3':
            jalankan_visualisasi()
        elif pilihan == '4':
            print("\n[EXIT] Terima kasih! Program selesai.")
            break
        else:
            print("\n[ERROR] Pilihan tidak valid! Silakan pilih 1-4.")
        
        # Jeda sebelum kembali ke menu
        input("\nTekan Enter untuk kembali ke menu...")

# ==========================================
# 5. EKSEKUSI PROGRAM
# ==========================================

if __name__ == "__main__":
    main()