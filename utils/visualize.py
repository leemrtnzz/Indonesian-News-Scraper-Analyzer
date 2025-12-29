import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
from collections import Counter
import re
from urllib.parse import urlparse
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory

# Set style
sns.set_theme(style="whitegrid")

def parse_currency(value_str):
    """
    Konversi string estimasi kerugian ke angka (Rupiah).
    Contoh: "Rp 10 Miliar" -> 10,000,000,000
    """
    if not isinstance(value_str, str) or not value_str:
        return 0
    
    value_str = value_str.lower().replace(',', '.').replace('rp', '').strip()
    
    multiplier = 1
    if 'triliun' in value_str:
        multiplier = 1_000_000_000_000
        value_str = value_str.replace('triliun', '')
    elif 'miliar' in value_str:
        multiplier = 1_000_000_000
        value_str = value_str.replace('miliar', '')
    elif 'juta' in value_str:
        multiplier = 1_000_000
        value_str = value_str.replace('juta', '')
    elif 'ribu' in value_str:
        multiplier = 1_000
        value_str = value_str.replace('ribu', '')
        
    try:
        # Ambil angka pertama yang valid
        number = float(re.findall(r"[\d\.]+", value_str)[0])
        return number * multiplier
    except:
        return 0

def parse_people(value_str):
    """
    Konversi string jumlah korban/warga ke angka.
    Contoh: "50 orang" -> 50
    """
    if not isinstance(value_str, str) or not value_str:
        return 0
    try:
        # Ambil angka pertama
        return int(re.findall(r"\d+", value_str)[0])
    except:
        return 0

def plot_topic_distribution(df):
    """1. Bar Chart: Distribusi Topik Berita"""
    if 'topik' not in df.columns:
        print("[SKIP] Kolom 'topik' tidak ditemukan.")
        return

    plt.figure(figsize=(10, 6))
    ax = sns.countplot(y='topik', data=df, order=df['topik'].value_counts().index, palette='viridis', hue='topik', legend=False)
    
    plt.title('Distribusi Topik Berita', fontsize=15)
    plt.xlabel('Jumlah Artikel', fontsize=12)
    plt.ylabel('Topik', fontsize=12)
    
    # Add labels
    for container in ax.containers:
        ax.bar_label(container)
        
    plt.tight_layout()
    plt.show()

def generate_wordcloud(df):
    """2. Word Cloud: Isu Dominan"""
    if 'konten_berita' not in df.columns:
        print("[SKIP] Kolom 'konten_berita' tidak ditemukan.")
        return

    text = " ".join(val for val in df.konten_berita.dropna().astype(str))
    
    # Hapus stopwords menggunakan Sastrawi
    factory = StopWordRemoverFactory()
    stopword_remover = factory.create_stop_word_remover()
    text = stopword_remover.remove(text)
    
    # Gabungkan stopwords bawaan dengan tambahan custom
    stop_words_list = factory.get_stop_words()
    custom_stopwords = ['baca', 'juga', 'halaman', 'kompas', 'com', 'detik', 'cnn', 'indonesia', 'tersebut', 'menjadi', 'hingga', 'kata', 'kalau', 'tak']
    
    # Gabungkan semua stopwords
    all_stopwords = set(stop_words_list + custom_stopwords)
    
    # Buat wordcloud
    wordcloud = WordCloud(
        width=800, 
        height=400, 
        background_color='white', 
        stopwords=all_stopwords,
        min_font_size=10,
        max_words=200
    ).generate(text)
    
    plt.figure(figsize=(10, 6))
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")
    plt.title('Word Cloud Isu Dominan', fontsize=15)
    plt.tight_layout()
    plt.show()
def plot_news_volume_trend(df):
    """3. Line Chart: Volume Berita per Tanggal"""
    if 'tanggal' not in df.columns:
        print("[SKIP] Kolom 'tanggal' tidak ditemukan.")
        return

    # Pastikan format tanggal datetime, ambil tanggalnya saja (YYYY-MM-DD)
    try:
        df['date_only'] = pd.to_datetime(df['tanggal']).dt.date
    except Exception as e:
        print(f"[ERROR] Gagal parsing tanggal: {e}")
        return

    daily_counts = df['date_only'].value_counts().sort_index()

    plt.figure(figsize=(12, 6))
    sns.lineplot(x=daily_counts.index, y=daily_counts.values, marker='o', linewidth=2.5, color='b')
    
    plt.title('Tren Volume Berita per Tanggal', fontsize=15)
    plt.xlabel('Tanggal', fontsize=12)
    plt.ylabel('Jumlah Berita', fontsize=12)
    plt.xticks(rotation=45)
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    
    plt.tight_layout()
    plt.show()

def plot_impact_scatter(df):
    """4. Scatter Plot: Kerugian Ekonomi vs Korban Jiwa"""
    if 'estimasi_kerugian' not in df.columns or 'estimasi_korban' not in df.columns:
        print("[SKIP] Kolom estimasi tidak lengkap.")
        return

    # Parsing data
    df['kerugian_num'] = df['estimasi_kerugian'].apply(parse_currency)
    df['korban_num'] = df['estimasi_korban'].apply(parse_people)

    # Filter data yang tidak kosong agar plot tidak numpuk di 0
    df_filtered = df[(df['kerugian_num'] > 0) | (df['korban_num'] > 0)].copy()
    
    if df_filtered.empty:
        print("[SKIP] Tidak ada data numerik valid untuk Scatter Plot.")
        return

    plt.figure(figsize=(10, 6))
    
    # Gunakan Kecamatan atau Topik sebagai hue jika ada
    hue_col = 'kecamatan' if 'kecamatan' in df.columns else 'topik'
    df_filtered[hue_col] = df_filtered[hue_col].fillna('Tidak Diketahui')
    df_filtered[hue_col] = df_filtered[hue_col].replace('', 'Tidak Diketahui')
    df_filtered[hue_col] = df_filtered[hue_col].astype(str)
    print("--- DATA EKSTREM ---")
    outliers = df_filtered[ (df_filtered['kerugian_num'] > 100_000_000_000) | (df_filtered['korban_num'] > 100) ]
    print(outliers[[hue_col, 'kerugian_num', 'korban_num']])
    sns.scatterplot(data=df_filtered, x='kerugian_num', y='korban_num', 
                    hue=hue_col, style=hue_col, s=100, palette='deep')
    plt.title('Scatter Plot: Dampak Kerugian vs Korban Jiwa', fontsize=15)
    plt.xlabel('Estimasi Kerugian (Rupiah)', fontsize=12)
    plt.ylabel('Jumlah Korban Jiwa (Orang)', fontsize=12)
    
    # Format axis angka agar mudah dibaca (M = Miliar, T = Triliun)
    def reformat_large_tick_values(tick_val, pos):
        if tick_val >= 1_000_000_000_000:
            val = round(tick_val/1_000_000_000_000, 1)
            return f'{val}T'
        elif tick_val >= 1_000_000_000:
            val = round(tick_val/1_000_000_000, 1)
            return f'{val}M'
        elif tick_val >= 1_000_000:
            val = round(tick_val/1_000_000, 1)
            return f'{val}Jt'
        else:
            return str(int(tick_val))

    plt.gca().xaxis.set_major_formatter(plt.FuncFormatter(reformat_large_tick_values))
    
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.show()

def plot_source_distribution(df):
    """5. Pie Chart: Distribusi Sumber Berita"""
    if 'link' not in df.columns:
        print("[SKIP] Kolom 'link' tidak ditemukan.")
        return

    def extract_domain(url):
        try:
            domain = urlparse(url).netloc
            return domain.replace('www.', '')
        except:
            return 'unknown'

    df['source'] = df['link'].apply(extract_domain)
    source_counts = df['source'].value_counts()

    plt.figure(figsize=(8, 8))
    plt.pie(source_counts, labels=source_counts.index, autopct='%1.1f%%', startangle=140, colors=sns.color_palette('pastel'))
    plt.title('Distribusi Sumber Berita', fontsize=15)
    plt.tight_layout()
    plt.show()
