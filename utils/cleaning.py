# ==========================================
# 2. FUNGSI PENDUKUNG (Scraping & Cleaning)
# ==========================================

import re
from datetime import datetime
from collections import Counter
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory

def get_clean_text(text):
    """Membersihkan teks mentah"""
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text.lower()

def clean_content(text):
    """
    Membersihkan body artikel dari noise/iklan.
    """
    if not text:
        return ""
    
    noise_patterns = [
        r"SCROLL TO CONTINUE WITH CONTENT",
        r"ADVERTISEMENT",
        r"Baca juga:.*?\n",
        r"Baca juga:.*",
        r"Simak Video:.*?\n",
        r"Simak Video:.*",
        r"Simak berita lainnya.*",
        r"Halaman selanjutnya.*",
        r"Saksikan video di bawah ini:.*",
        r"Lihat juga video:.*"
    ]
    
    cleaned_text = text
    for pattern in noise_patterns:
        cleaned_text = re.sub(pattern, " ", cleaned_text, flags=re.IGNORECASE)
        
    cleaned_text = re.sub(r'\n\s*\n', '\n\n', cleaned_text)
    cleaned_text = re.sub(r' +', ' ', cleaned_text)
    return cleaned_text.strip()

def clean_author(authors_list):
    """Membersihkan nama penulis dari URL, duplikat, dan karakter sampah."""
    if not authors_list:
        return "Unknown"
        
    # 1. Standardisasi input ke string tunggal
    if isinstance(authors_list, list):
        author_str = ", ".join(authors_list)
    else:
        author_str = str(authors_list)
    
    # 2. Hapus URL lengkap & Domain
    author_str = re.sub(r'https?://[^\s,]+', '', author_str, flags=re.IGNORECASE)
    author_str = re.sub(r'www\.[^\s,]+', '', author_str, flags=re.IGNORECASE)
    author_str = re.sub(r'\S+\.com', '', author_str, flags=re.IGNORECASE)
    author_str = re.sub(r'\S+\.co\.id', '', author_str, flags=re.IGNORECASE)
    author_str = re.sub(r'\S+\.net', '', author_str, flags=re.IGNORECASE)
    
    # 3. Hapus keyword sampah specific
    trash_words = [
        r'\bhttp\b', r'\bhttps\b', r'\bcom\b', r'\bco\b', r'\bid\b', 
        r'\bwww\b', r'\bhtml\b', r'\beditor\b', r'\bpenulis\b', 
        r'\bnews\b', r'\bwartawan\b', r'\breporter\b', r'\bhalaman\b', r'\bbaca\b'
    ]
    for pattern in trash_words:
        author_str = re.sub(pattern, '', author_str, flags=re.IGNORECASE)

    # 4. Bersihkan karakter non-huruf (kecuali koma, titik, spasi)
    author_str = re.sub(r'[^a-zA-Z,\.\s]', ' ', author_str)
    
    # 5. Normalisasi spasi
    author_str = re.sub(r'\s+', ' ', author_str).strip()
    
    # 6. Dedup nama & Validasi
    if not author_str:
        return "Unknown"
        
    # Split by comma, cleanup items
    names = [name.strip() for name in author_str.split(',') if name.strip()]
    unique_names = []
    seen = set()
    
    for name in names:
        # Hapus titik/spasi di ujung
        name_clean = name.strip(' .')
        if len(name_clean) < 3: # Skip nama terlalu pendek
            continue
        # Cek duplikasi (case-insensitive)
        if name_clean.lower() not in seen:
            unique_names.append(name_clean)
            seen.add(name_clean.lower())
    
    if not unique_names:
        return "Unknown"
        
    return ", ".join(unique_names)

def clean_date(date_obj):
    """Normalisasi tanggal ke string standard."""
    if not date_obj:
        return ""
    if isinstance(date_obj, datetime):
        return date_obj.strftime("%Y-%m-%d %H:%M:%S")
    return str(date_obj)

def extract_financial_loss(text):
    """
    Ekstraksi entitas estimasi kerugian (Rupiah).
    Mencari pola: Rp X Triliun/Miliar/Juta.
    MENGABAIKAN jika konteksnya adalah DONASI/BANTUAN.
    """
    if not text:
        return ""
    
    # 1. Definisi Pola Angka & Satuan (Support singkatan M, T, Jt)
    #    Contoh: Rp 10,3 M, Rp 100 Juta, 1.5 Triliun
    number_pattern = r"(?:Rp\.?|Rupiah)\s*([\d\.,]+)\s*(Triliun|Miliar|Juta|Ribu|T|M|Jt|K)"
    
    # 2. Definisi Keyword yang MENANDAKAN BANTUAN (Blacklist untuk Kerugian)
    donation_keywords = [
        "bantuan", "donasi", "sumbangan", "mengumpulkan", "kumpulkan", 
        "terkumpul", "galang", "penggalangan", "dana", "menyalurkan", 
        "salurkan", "alokasi", "anggaran", "biaya", "investasi"
    ]
    
    matches = re.finditer(number_pattern, text, re.IGNORECASE)
    
    candidates = []
    
    for match in matches:
        value_str = match.group(0) # Full match "Rp 10 M"
        start_pos = match.start()
        
        # 3. Cek Konteks (misal 50 karakter sebelumnya)
        context_start = max(0, start_pos - 70)
        context = text[context_start:start_pos].lower()
        
        # Jika ada kata keyword donasi di dekat angka, SKIP (bukan kerugian)
        if any(keyword in context for keyword in donation_keywords):
            continue
            
        # Jika lolos filter, anggap ini kandidat kerugian
        candidates.append(f"{match.group(1)} {match.group(2)}")
        
    if candidates:
        # Prioritas: Kalau ada kata "rugi" atau "kerugian" di dekatnya lebih valid,
        # tapi untuk sekarang kita ambil yang pertama lolos filter donasi.
        return candidates[0]
        
    return ""

def extract_aid(text):
    """
    Ekstraksi entitas estimasi BANTUAN/DONASI.
    Kebalikan dari loss: Hanya ambil jika ada indikasi bantuan.
    """
    if not text:
        return ""
        
    number_pattern = r"(?:Rp\.?|Rupiah)\s*([\d\.,]+)\s*(Triliun|Miliar|Juta|Ribu|T|M|Jt|K)"
    
    # Keyword yang memvalidasi ini adalah bantuan
    aid_keywords = [
        "bantuan", "donasi", "sumbangan", "mengumpulkan", "terkumpul", 
        "galang", "dana", "menyalurkan", "salurkan", "peduli", "kasih",
        "menembus", "capai", "mencapai" # Konteks: "Donasi menembus Rp X"
    ]
    
    matches = re.finditer(number_pattern, text, re.IGNORECASE)
    
    for match in matches:
        start_pos = match.start()
        
        # Cek Konteks Sebelum (preceding text)
        context_start = max(0, start_pos - 70)
        context = text[context_start:start_pos].lower()
        
        # Harus ada keyword bantuan
        if any(keyword in context for keyword in aid_keywords):
            return f"{match.group(1)} {match.group(2)}"
            
    return ""

def extract_victim_count(text):
    """
    Ekstraksi entitas jumlah korban.
    Mencari angka dekat kata 'tewas', 'meninggal', 'korban'.
    """
    if not text:
        return ""
    # Pola: <angka> orang tewas/meninggal
    pattern = r"(\d+)\s*(?:orang|jiwa)?\s*(?:tewas|meninggal|wafat)"
    matches = re.findall(pattern, text, re.IGNORECASE)
    
    if matches:
        return matches[0]
    
    # Pola alternatif: <angka> korban
    pattern_alt = r"(\d+)\s*korban"
    matches_alt = re.findall(pattern_alt, text, re.IGNORECASE)
    if matches_alt:
        return matches_alt[0]
        
    return ""

def extract_kecamatan(text):
    """Ekstraksi nama Kecamatan."""
    if not text:
        return ""
    # Pola: Kecamatan <Nama> (Huruf kapital awal, bisa 1-2 kata)
    pattern = r"Kecamatan\s+([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)"
    matches = re.findall(pattern, text)
    if matches:
        return ", ".join(list(set(matches))[:3]) # Ambil max 3 unik
    return ""

def extract_warga_sipil(text):
    """Ekstraksi jumlah warga/sipil yang terdampak/disebut."""
    if not text:
        return ""
    # Pola: <angka> warga/sipil/kk
    pattern = r"(\d+(?:\.|,\d+)?)\s*(?:jiwa|orang)?\s*(?:warga|sipil|penduduk|KK|kepala keluarga)"
    matches = re.findall(pattern, text, re.IGNORECASE)
    if matches:
        # Kembalikan string (misal: "50 warga") -> di sini cuma angka yg dicapture
        # Kita return angka pertama yg ditemukan + konteks suffixnya manual
        return matches[0] 
    return ""

def get_hashtags(text_content, top_n=7):
    """Menghasilkan hashtag dari teks"""
    factory = StopWordRemoverFactory()
    stopword_remover = factory.create_stop_word_remover()
    
    clean_txt = get_clean_text(text_content)
    clean_txt = stopword_remover.remove(clean_txt)
    words = clean_txt.split()
    
    blacklist = ['foto', 'baca', 'halaman', 'komentar', 'editor', 'jakarta', 'penulis', 'news', 'juga', 'akan', 'pada', 'untuk', 'yang', 'dengan', 'ini', 'dari']
    filtered_words = [w for w in words if len(w) > 3 and w not in blacklist]
    
    counter = Counter(filtered_words)
    hashtags = [f"#{word}" for word, count in counter.most_common(top_n)]
    return " ".join(hashtags)
