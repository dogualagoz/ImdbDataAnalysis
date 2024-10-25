import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import webbrowser
from matplotlib import pyplot as plt
import numpy as np
import matplotlib.ticker as ticker
from scipy.interpolate import make_interp_spline

# --------------------------- DATABASE CONNECTION ---------------------------
def veritabanina_baglan():
    """Veritabanına bağlan ve imleç oluştur."""
    con = sqlite3.connect("imdbtop1000.db")
    return con, con.cursor()

con, cursor = veritabanina_baglan()

# --------------------------- DATA FETCHING / UTILS ---------------------------
def ayir_turler():
    """Veritabanından türleri ayır ve liste olarak döndür."""
    cursor.execute("SELECT Genre FROM imdb_top_1000")
    genres = set()
    for sutun in cursor.fetchall():
        tur_listesi = sutun[0].split(",")
        for tur in tur_listesi:
            genres.add(tur.strip())
    return sorted(genres)

def moving_average(data, window_size=5):
    """Verilen veriler üzerinde hareketli ortalama uygular."""
    return np.convolve(data, np.ones(window_size) / window_size, mode='valid')

# Google'da arat fonksiyonu
def google_arat():
    """Seçili filmi Google'da aratır."""
    try:
        selected_item = tree.selection()[0]  # Seçilen satırı al
        film_basligi = tree.item(selected_item)['values'][0]  # Filmin başlığını al
        query = f"https://www.google.com/search?q={film_basligi}"  # Google arama sorgusu hazırla
        webbrowser.open(query)  # Web tarayıcısında arama yap
    except IndexError:
        messagebox.showwarning("Uyarı", "Bir film seçiniz!")  # Eğer seçim yoksa uyarı göster

# --------------------------- GRAPH FUNCTIONS ---------------------------
def goster_grafik(title, xlabel, ylabel, fig):
    """Grafik için başlık ve eksen bilgilerini ayarla ve göster."""
    ax = fig.gca()
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    plt.show()

# Yıllara göre film sayısı grafiği
def film_sayisi_grafik():
    # Veritabanından verileri çekiyoruz
    cursor.execute("SELECT Released_Year, COUNT(*) FROM imdb_top_1000 GROUP BY Released_Year")
    data = cursor.fetchall()

    # Yıllar ve sayımlar listelerini hazırlıyoruz
    years = []
    counts = []
    
    # Yıl değerlerini kontrol edip, sadece sayısal değerleri alıyoruz
    for row in data:
        year = row[0]
        if isinstance(year, int) or (isinstance(year, str) and year.isdigit()):
            year = int(year)  # Yılı integer yapıyoruz
            years.append(year)
            counts.append(row[1])  # Sayıları ekliyoruz

    # Yıllara göre film sayısını sıralıyoruz
    sorted_data = sorted(zip(years, counts), key=lambda x: x[0])
    years, counts = zip(*sorted_data)  # Sıralanan verileri ayırıyoruz

    # Grafiği oluşturma
    fig, ax = plt.subplots(figsize=(12, 6))  # Daha geniş bir grafik alanı ayarladık
    ax.bar(years, counts, color='skyblue')  # Grafiğe renk verdik
    ax.set_title("Yıllara Göre Film Sayısı")
    ax.set_xlabel("Yıl")
    ax.set_ylabel("Film Sayısı")
    
    # Grafiği gösterme
    goster_grafik("Yıllara Göre Film Sayısı", "Yıl", "Film Sayısı", fig)

def imdb_film_sayisi_grafik():
    """IMDb puanına göre film sayısı grafiğini oluştur."""
    cursor.execute("SELECT IMDB_Rating, COUNT(*) FROM imdb_top_1000 GROUP BY IMDB_Rating")
    data = cursor.fetchall()
    ratings, counts = zip(*data)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(ratings, counts)
    goster_grafik("IMDb Puanı - Film Sayısı", "IMDb Puanı", "Film Sayısı", fig)

def imdb_gise_grafik():
    """IMDb puanı ve gişe arasındaki ilişkiyi gösteren grafik oluştur."""
    cursor.execute("""
        SELECT IMDB_Rating, AVG(CAST(REPLACE(REPLACE(Gross, ',', ''), '$', '') AS INTEGER))
        FROM imdb_top_1000 WHERE Gross IS NOT NULL AND Gross != 'N/A' GROUP BY IMDB_Rating
    """)
    data = cursor.fetchall()
    ratings, avg_gross = zip(*data)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(ratings, avg_gross, marker="o")
    goster_grafik("IMDb Puanı - Ortalama Gişe", "IMDb Puanı", "Ortalama Gişe ($)", fig)

# Yıllara göre tür trendleri grafiği (yumuşatılmış geçişler ve kavisli çizgi)
def tur_trendleri_grafik():
    # En popüler 7 türü bulmak için
    cursor.execute("""
        SELECT Genre, COUNT(*) as count
        FROM imdb_top_1000 
        GROUP BY Genre
        ORDER BY count DESC
        LIMIT 7
    """)
    pop_genres_data = cursor.fetchall()
    pop_genres = []

    # Türleri ayıklıyoruz
    for row in pop_genres_data:
        genres = row[0].split(",")
        for genre in genres:
            genre = genre.strip()
            if genre not in pop_genres:
                pop_genres.append(genre)
                if len(pop_genres) == 7:
                    break
        if len(pop_genres) == 7:
            break

    # Yıllara göre popüler türlerin film sayısını bulmak için
    genre_year_counts = {genre: {} for genre in pop_genres}
    cursor.execute("SELECT Released_Year, Genre FROM imdb_top_1000")
    data = cursor.fetchall()

    for row in data:
        year = row[0]
        # Eğer yıl sayısal değilse o satırı yok sayıyoruz
        if isinstance(year, int) or (isinstance(year, str) and year.isdigit()):
            year = int(year)  # Yıl sayısal ise integer yapıyoruz
            genres = row[1].split(",")
            for genre in genres:
                genre = genre.strip()
                if genre in genre_year_counts:
                    if year in genre_year_counts[genre]:
                        genre_year_counts[genre][year] += 1
                    else:
                        genre_year_counts[genre][year] = 1

    # Grafiği çizmek için
    fig, ax = plt.subplots(figsize=(12, 6))

    for genre, year_data in genre_year_counts.items():
        years = sorted([year for year in year_data.keys()])
        counts = [year_data[year] for year in years]

        # Hareketli ortalama uyguluyoruz
        if len(counts) > 5:
            smooth_counts = moving_average(counts, window_size=7)
            smooth_years = years[:len(smooth_counts)]  # Yılları da aynı uzunlukta tutuyoruz
            
            # Kavisli geçişler için spline uyguluyoruz
            years_spline = np.linspace(min(smooth_years), max(smooth_years), 300)  # Daha fazla nokta ekleyerek kavisli geçiş sağlıyoruz
            spline = make_interp_spline(smooth_years, smooth_counts, k=3)  # Cubic Spline Interpolation
            counts_spline = spline(years_spline)
            
            # Kavisli çizgi
            ax.plot(years_spline, counts_spline, label=genre, linewidth=0.5)
        else:
            ax.plot(years, counts, label=genre, linewidth=1.5)

    ax.set_title("Yıllara Göre Tür Trendleri (En Popüler 7 Tür)")
    ax.set_xlabel("Yıl")
    ax.set_ylabel("Film Sayısı")
    ax.legend()

    # Y eksenini 0'dan 20'ye kadar ayarlıyoruz
    ax.set_ylim(0, 20)
    ax.yaxis.set_major_locator(ticker.MultipleLocator(5))

    # X ekseni 1920, 1930, 1940 şeklinde artacak
    ax.xaxis.set_major_locator(ticker.MultipleLocator(10))

    # Grafiği gösterme
    goster_grafik("Yıllara Göre Tür Trendleri (En Popüler 7 Tür)", "Yıl", "Film Sayısı", fig)

# --------------------------- SEARCH AND FILTER FUNCTIONS ---------------------------
def tabloyu_doldur(sorgu):
    """Tablodaki verileri verilen sorguya göre güncelle."""
    temizle_tablo()
    cursor.execute(sorgu)
    rows = cursor.fetchall()
    for row in rows:
        tree.insert("", tk.END, values=row)
    satir_sayisi_var.set(f"Toplam Satır Sayısı: {len(rows)}")

def temizle_tablo():
    """Tablodaki tüm satırları temizle."""
    for row in tree.get_children():
        tree.delete(row)

def ara_yonetmen():
    """Yönetmen adına göre tabloyu filtrele."""
    director_name = search_entry.get()
    sorgu = f"SELECT Series_Title, Released_Year, Runtime, Genre, IMDB_Rating, Director, Star1, Gross FROM imdb_top_1000 WHERE Director LIKE '%{director_name}%'"
    tabloyu_doldur(sorgu)

def filtre_tur():
    """Tür dropdown'ına göre tabloyu filtrele."""
    secilen_tur = tur_var.get()
    sorgu = f"SELECT Series_Title, Released_Year, Runtime, Genre, IMDB_Rating, Director, Star1, Gross FROM imdb_top_1000 WHERE Genre LIKE '%{secilen_tur}%'"
    tabloyu_doldur(sorgu)

def grafik_calistir():
    """Seçilen grafiği çalıştır."""
    secilen_grafik = grafik_var.get()
    if secilen_grafik == "Yıllara Göre Film Sayısı":
        film_sayisi_grafik()
    elif secilen_grafik == "IMDb Puanı - Film Sayısı":
        imdb_film_sayisi_grafik()
    elif secilen_grafik == "IMDb Puanı - Ortalama Gişe":
        imdb_gise_grafik()
    elif secilen_grafik == "Yıllara Göre Tür Trendleri":
        tur_trendleri_grafik()

# --------------------------- USER INTERFACE ---------------------------
root = tk.Tk()
root.title("IMDb Top 1000")
root.geometry("1200x700")

# Ana çerçeve
main_frame = tk.Frame(root)
main_frame.pack(fill=tk.BOTH, expand=True)

# Sol panel (Butonlar için)
left_frame = tk.Frame(main_frame)
left_frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.Y)

# Sağ panel (Tablo ve Scrollbar için)
right_frame = tk.Frame(main_frame)
right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

# Scrollbars
x_scrollbar = tk.Scrollbar(right_frame, orient=tk.HORIZONTAL)
x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
y_scrollbar = tk.Scrollbar(right_frame, orient=tk.VERTICAL)
y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# Tablo
tree = ttk.Treeview(right_frame, columns=("Title", "Year", "Duration", "Genre", "IMDB Rating", "Director", "Star", "Gross"), show='headings', xscrollcommand=x_scrollbar.set, yscrollcommand=y_scrollbar.set)
tree.heading("Title", text="Film Başlığı")
tree.heading("Year", text="Yıl")
tree.heading("Duration", text="Süre (dakika)")
tree.heading("Genre", text="Tür")
tree.heading("IMDB Rating", text="IMDB Puanı")
tree.heading("Director", text="Yönetmen")
tree.heading("Star", text="Başrol Oyuncusu")
tree.heading("Gross", text="Gişe ($)")
tree.pack(pady=10, fill=tk.BOTH, expand=True)

x_scrollbar.config(command=tree.xview)
y_scrollbar.config(command=tree.yview)

# --------------------------- SEARCH AND FILTER WIDGETS ---------------------------

# Yönetmen arama kısmı
search_label = tk.Label(left_frame, text="Yönetmene göre ara:")
search_label.pack(anchor=tk.W, pady=5)
search_entry = tk.Entry(left_frame, width=30)
search_entry.pack(anchor=tk.W, pady=5)

search_button = tk.Button(left_frame, text="Ara", command=ara_yonetmen)
search_button.pack(anchor=tk.W, pady=6)

# Tür dropdown menüsü
tur_label = tk.Label(left_frame, text="Tür:")
tur_label.pack(anchor=tk.W, pady=2)

# Türler veritabanından alınıp dropdown'a ekleniyor
tur_opsiyonlar = ayir_turler()
tur_var = tk.StringVar()
tur_dropdown = ttk.Combobox(left_frame, textvariable=tur_var, values=tur_opsiyonlar, state="readonly")
tur_dropdown.pack(anchor=tk.W, pady=3)
tur_dropdown.bind("<<ComboboxSelected>>", lambda event: filtre_tur())

# --------------------------- SORTING AND GRAPH SELECTION ---------------------------

# Sıralama dropdown menüsü
sirala_label = tk.Label(left_frame, text="Sırala:")
sirala_label.pack(anchor=tk.W, pady=2)

sirala_opsiyonlar = ["IMDb Puanı", "Gişe", "Süre", "Yıl", "Alfabetik"]
siralama_var = tk.StringVar(value="IMDb Puanı")
sirala_dropdown = ttk.Combobox(left_frame, textvariable=siralama_var, values=sirala_opsiyonlar, state="readonly")
sirala_dropdown.pack(anchor=tk.W, pady=3)

# Sıralama değiştiğinde tabloyu güncelleyen fonksiyon
sirala_dropdown.bind("<<ComboboxSelected>>", lambda event: siralama_degisti(event))

def siralama_degisti(event):
    """Sıralama kriterine göre tabloyu güncelle."""
    siralama_kriteri = siralama_var.get()
    secilen_tur = tur_var.get()

    # Sıralama kriterine göre sorgu oluştur ve tabloyu güncelle
    if secilen_tur:
        sorgu = f"SELECT Series_Title, Released_Year, Runtime, Genre, IMDB_Rating, Director, Star1, Gross FROM imdb_top_1000 WHERE Genre LIKE '%{secilen_tur}%'"
    else:
        sorgu = "SELECT Series_Title, Released_Year, Runtime, Genre, IMDB_Rating, Director, Star1, Gross FROM imdb_top_1000"

    if siralama_kriteri == "IMDb Puanı":
        sorgu += " ORDER BY IMDB_Rating DESC"
    elif siralama_kriteri == "Gişe":
        sorgu += " ORDER BY CAST(REPLACE(REPLACE(Gross, ',', ''), '$', '') AS INTEGER) DESC"
    elif siralama_kriteri == "Süre":
        sorgu += " ORDER BY CAST(SUBSTR(Runtime, 1, INSTR(Runtime, ' ') - 1) AS INTEGER) DESC"
    elif siralama_kriteri == "Yıl":
        sorgu += " ORDER BY Released_Year DESC"
    elif siralama_kriteri == "Alfabetik":
        sorgu += " ORDER BY Series_Title ASC"

    tabloyu_doldur(sorgu)

# Grafik seçimi
grafik_label = tk.Label(left_frame, text="Grafik:")
grafik_label.pack(anchor=tk.W, pady=2)

grafik_opsiyonlar = ["Yıllara Göre Film Sayısı", "IMDb Puanı - Film Sayısı", "IMDb Puanı - Ortalama Gişe", "Yıllara Göre Tür Trendleri"]
grafik_var = tk.StringVar(value="Yıllara Göre Film Sayısı")
grafik_dropdown = ttk.Combobox(left_frame, textvariable=grafik_var, values=grafik_opsiyonlar, state="readonly")
grafik_dropdown.pack(anchor=tk.W, pady=3)

grafik_button = tk.Button(left_frame, text="Çalıştır", command=grafik_calistir)
grafik_button.pack(anchor=tk.W, pady=6)

# --------------------------- RESET AND WEB SEARCH BUTTONS ---------------------------

# Sıfırlama fonksiyonu (Dropdown ve search alanını sıfırlar, tabloyu yeniden doldurur)
def sifirla():
    tur_var.set('')
    search_entry.delete(0, tk.END)
    siralama_var.set("IMDb Puanı")
    tabloyu_doldur("SELECT Series_Title, Released_Year, Runtime, Genre, IMDB_Rating, Director, Star1, Gross FROM imdb_top_1000 ORDER BY IMDB_Rating DESC")

# Sıfırlama ve İnternet Arama Butonları için Alt Çerçeve
bottom_button_frame = tk.Frame(left_frame)
bottom_button_frame.pack(side=tk.BOTTOM, anchor=tk.W, pady=20)

sifirla_button = tk.Button(bottom_button_frame, text="Sıfırla", command=sifirla)
sifirla_button.pack(side=tk.LEFT, padx=5)

arat_button = tk.Button(bottom_button_frame, text="İnternet Arama", command=google_arat)
arat_button.pack(side=tk.LEFT, padx=5)

# --------------------------- STATUS BAR ---------------------------
# Tablo altındaki satır sayısı etiketi
satir_sayisi_var = tk.StringVar()
satir_sayisi_var.set("Toplam Satır Sayısı: 1000")
satir_sayisi_label = tk.Label(root, textvariable=satir_sayisi_var)
satir_sayisi_label.pack(side=tk.RIGHT, anchor=tk.S, padx=20, pady=10)

# --------------------------- INITIAL DATA LOAD ---------------------------
# Uygulama başladığında tabloyu varsayılan şekilde doldur
tabloyu_doldur("SELECT Series_Title, Released_Year, Runtime, Genre, IMDB_Rating, Director, Star1, Gross FROM imdb_top_1000 ORDER BY IMDB_Rating DESC")

# --------------------------- MAINLOOP AND CLOSE ---------------------------
root.mainloop()

# Veritabanı bağlantısını kapatma
con.close()