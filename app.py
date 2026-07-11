import streamlit as st
import pandas as pd
import psycopg2

import streamlit as st
import pandas as pd
import psycopg2

# 1. Konfigurasi koneksi murni psycopg2
@st.cache_resource
def get_native_connection():
    try:
        conn = psycopg2.connect(
            host=st.secrets["connections"]["postgresql"]["host"],
            port=st.secrets["connections"]["postgresql"]["port"],
            database=st.secrets["connections"]["postgresql"]["database"],
            user=st.secrets["connections"]["postgresql"]["username"],
            password=st.secrets["connections"]["postgresql"]["password"]
        )
        return conn
    except Exception as e:
        st.error(f"Koneksi gagal: {e}")
        st.stop()

# 2. Inisialisasi koneksi
conn = get_native_connection()

# --- SHIM: Menambahkan fungsi .query() ke psycopg2 agar tidak error ---
# Kode lama Anda memanggil conn.query(), ini akan mencegah error AttributeError
def patched_query(sql):
    return pd.read_sql(sql, conn)
conn.query = patched_query 
# ----------------------------------------------------------------------

# 3. Inisialisasi cursor untuk kode lama Anda
cursor = conn.cursor()

# INITIAL DATABASE TABLES
cursor.execute("CREATE TABLE IF NOT EXISTS owners (id SERIAL PRIMARY KEY, nama TEXT, no_telp TEXT UNIQUE, total_cuci INTEGER DEFAULT 0, total_akumulasi INTEGER DEFAULT 0, total_cuci_motor INTEGER DEFAULT 0, loyalty_history TEXT DEFAULT '')")
cursor.execute("CREATE TABLE IF NOT EXISTS vehicles (id SERIAL PRIMARY KEY, owner_id INTEGER, jenis_mobil TEXT, ukuran_mobil TEXT, plat_nomor TEXT UNIQUE, kategori_kendaraan TEXT DEFAULT 'Mobil', FOREIGN KEY(owner_id) REFERENCES owners(id) ON DELETE CASCADE)")
cursor.execute("CREATE TABLE IF NOT EXISTS transactions (id SERIAL PRIMARY KEY, tanggal TEXT, nama_pelanggan TEXT, paket_layanan TEXT, metode_bayar TEXT, nominal INTEGER, jenis_mobil TEXT, ukuran_mobil TEXT, plat_nomor TEXT, tambahan_layanan TEXT, kategori_kendaraan TEXT DEFAULT 'Mobil', harga_paket_real INTEGER DEFAULT 0, harga_tambahan_real INTEGER DEFAULT 0, kategori_laporan TEXT DEFAULT 'Umum')")
cursor.execute("CREATE TABLE IF NOT EXISTS detailing_trx (id SERIAL PRIMARY KEY, tanggal TEXT, nama_pelanggan TEXT, no_hp TEXT, jenis_mobil TEXT, ukuran_mobil TEXT, plat_nomor TEXT, paket_detailing TEXT, metode_bayar TEXT, nominal INTEGER, pekerja TEXT, upah_pekerja INTEGER, bersih INTEGER)")
cursor.execute("CREATE TABLE IF NOT EXISTS employee_bonuses (id SERIAL PRIMARY KEY, tanggal TEXT, nama_karyawan TEXT, jenis_bonus TEXT, nominal_bonus INTEGER)")
cursor.execute("CREATE TABLE IF NOT EXISTS laundry_karpet (id SERIAL PRIMARY KEY, owner_id INTEGER, nama_pelanggan TEXT, no_hp TEXT, warna_karpet TEXT, jumlah_pcs INTEGER DEFAULT 1, tgl_masuk TEXT, tgl_jadi TEXT, harga INTEGER DEFAULT 0, status TEXT DEFAULT 'Proses', metode_bayar TEXT DEFAULT 'Cash', is_archived INTEGER DEFAULT 0)")
cursor.execute("CREATE TABLE IF NOT EXISTS master_karyawan (slot_id SERIAL PRIMARY KEY, nama TEXT DEFAULT '', jabatan TEXT DEFAULT '', alamat TEXT DEFAULT '', tgl_lahir TEXT DEFAULT '', no_hp TEXT DEFAULT '', nik TEXT DEFAULT '', tgl_masuk TEXT DEFAULT '', is_active INTEGER DEFAULT 1)")
cursor.execute("CREATE TABLE IF NOT EXISTS kasbon_karyawan (id SERIAL PRIMARY KEY, slot_id INTEGER, jumlah_bon INTEGER DEFAULT 0, jenis_potongan TEXT DEFAULT 'Mingguan', tanggal TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS absensi_karyawan (id SERIAL PRIMARY KEY, slot_id INTEGER, tanggal TEXT, jam_masuk TEXT DEFAULT '08:00', jam_keluar TEXT DEFAULT '22:00', status TEXT DEFAULT 'Masuk', jam_izin_mulai TEXT, jam_izin_selesai TEXT, alasan_izin TEXT, uang_makan REAL DEFAULT 0)")
cursor.execute("CREATE TABLE IF NOT EXISTS upah_permobil_daily (id SERIAL PRIMARY KEY, tanggal TEXT, upah_siang REAL DEFAULT 0, upah_malam REAL DEFAULT 0, total_upah REAL DEFAULT 0, s_orang INTEGER DEFAULT 6, m_orang INTEGER DEFAULT 6)")

conn.commit()

# AUTO-MIGRATION
def auto_migrate(query):
    try:
        # Menggunakan koneksi baru
        conn.query(query)
    except Exception as e:
        st.error(f"Gagal migrasi: {e}")

auto_migrate("ALTER TABLE master_karyawan ADD COLUMN IF NOT EXISTS is_active INTEGER DEFAULT 1")
auto_migrate("ALTER TABLE master_karyawan ADD COLUMN IF NOT EXISTS gaji_mingguan_master REAL DEFAULT 0")
auto_migrate("ALTER TABLE master_karyawan ADD COLUMN IF NOT EXISTS gaji_bulanan_master REAL DEFAULT 0")
auto_migrate("ALTER TABLE upah_permobil_daily ADD COLUMN IF NOT EXISTS upah_siang REAL DEFAULT 0")
auto_migrate("ALTER TABLE upah_permobil_daily ADD COLUMN IF NOT EXISTS upah_malam REAL DEFAULT 0")
auto_migrate("ALTER TABLE upah_permobil_daily ADD COLUMN IF NOT EXISTS total_upah REAL DEFAULT 0")
auto_migrate("ALTER TABLE upah_permobil_daily ADD COLUMN IF NOT EXISTS s_orang INTEGER DEFAULT 6")
auto_migrate("ALTER TABLE upah_permobil_daily ADD COLUMN IF NOT EXISTS m_orang INTEGER DEFAULT 6")
auto_migrate("ALTER TABLE absensi_karyawan ADD COLUMN IF NOT EXISTS jam_izin_mulai TEXT")
auto_migrate("ALTER TABLE absensi_karyawan ADD COLUMN IF NOT EXISTS jam_izin_selesai TEXT")
auto_migrate("ALTER TABLE absensi_karyawan ADD COLUMN IF NOT EXISTS alasan_izin TEXT")
auto_migrate("ALTER TABLE absensi_karyawan ADD COLUMN IF NOT EXISTS uang_makan REAL DEFAULT 0")
auto_migrate("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS kategori_laporan TEXT DEFAULT 'Umum'")
auto_migrate("ALTER TABLE owners ADD COLUMN IF NOT EXISTS loyalty_history TEXT DEFAULT ''")
auto_migrate("ALTER TABLE upah_permobil_daily ADD COLUMN IF NOT EXISTS koreksi_s_sgp INTEGER DEFAULT 0")
auto_migrate("ALTER TABLE upah_permobil_daily ADD COLUMN IF NOT EXISTS koreksi_s_plat INTEGER DEFAULT 0")
auto_migrate("ALTER TABLE upah_permobil_daily ADD COLUMN IF NOT EXISTS koreksi_s_motor INTEGER DEFAULT 0")
auto_migrate("ALTER TABLE upah_permobil_daily ADD COLUMN IF NOT EXISTS koreksi_m_sgp INTEGER DEFAULT 0")
auto_migrate("ALTER TABLE upah_permobil_daily ADD COLUMN IF NOT EXISTS koreksi_m_plat INTEGER DEFAULT 0")
auto_migrate("ALTER TABLE upah_permobil_daily ADD COLUMN IF NOT EXISTS koreksi_m_motor INTEGER DEFAULT 0")

# STYLING INTERFACE
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    * { font-family: 'Plus Jakarta Sans', sans-serif; }
    .stApp { background-color: #f0f7ff; }
    div[data-testid="stSidebarUserContent"] .stRadio div[role="radiogroup"] { display: none !important; }
    .stSidebar { background-color: #ffffff !important; border-right: 1px solid #bae6fd !important; }
    .stTabs [data-baseweb="tab-list"] { background-color: #ffffff; padding: 6px; border-radius: 12px; border: 1px solid #e2e8f0; gap: 8px; }
    .stTabs [data-baseweb="tab"] { color: #64748b !important; font-weight: 600 !important; font-size: 14px; padding: 10px 20px; border-radius: 8px; border: none !important; background-color: transparent; transition: all 0.25s ease; }
    .stTabs [data-baseweb="tab"]:hover { color: #0284c7 !important; background-color: #e0f2fe; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { color: #ffffff !important; background: linear-gradient(135deg, #0284c7 0%, #38bdf8 100%) !important; box-shadow: 0 4px 12px rgba(56, 189, 248, 0.2); }
    label, .stMarkdown p, h2, h3, h4, span, caption { color: #334155 !important; }
    
    .stTextInput input, .stNumberInput input { background-color: #ffffff !important; color: #0f172a !important; border: 1px solid #cbd5e1 !important; border-radius: 8px !important; height: 42px; }
    div[data-baseweb="select"] > div { background-color: #ffffff !important; border: 1px solid #cbd5e1 !important; border-radius: 8px !important; }
    
    div[data-testid="stWidgetLabel"] p { margin-bottom: 2px !important; padding-bottom: 0px !important; font-weight: 600; font-size: 13px; }
    div[data-testid="stRadio"] { padding-top: 4px; }
    div[data-baseweb="select"] { margin-top: 0px !important; }
    div[data-testid="stForm"] { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #bae6fd; }
    .stButton button, .stDownloadButton button, .stLinkButton a { background: #ffffff; color: #334155 !important; border: 1px solid #cbd5e1 !important; border-radius: 8px !important; padding: 10px 20px; font-weight: 600; transition: all 0.2s ease; text-decoration: none !important; }
    .stButton button:hover, .stLinkButton a:hover { background: linear-gradient(135deg, #0284c7 0%, #38bdf8 100%) !important; color: white !important; border: none !important; box-shadow: 0 4px 12px rgba(56, 189, 248, 0.3); transform: translateY(-1px); }
    div[data-testid="stMetricValue"] { color: #0284c7 !important; font-weight: 700; }
    div[data-testid="stDataEditor"] { border: 1px solid #bae6fd !important; border-radius: 12px; overflow: hidden; background-color: #ffffff; }
    .btn-whatsapp-custom { background: linear-gradient(135deg, #25D366 0%, #128C7E 100%) !important; color: white !important; border: none !important; padding: 14px; border-radius: 8px; cursor: pointer; width: 100%; font-weight: bold; font-size: 16px; box-shadow: 0 4px 12px rgba(37, 211, 102, 0.2); transition: all 0.2s ease; }
    .btn-whatsapp-custom:hover { transform: translateY(-1px); box-shadow: 0 6px 16px rgba(18, 140, 126, 0.4); }
    </style>
""", unsafe_allow_html=True)

# HELPER
def bulatkan_sabtu_malam(nominal):
    now = datetime.now()
    if now.weekday() == 5 and now.hour == 21 and now.minute >= 30:
        nominal_int = int(round(nominal))
        sisa = nominal_int % 1000
        if sisa >= 500:
            return nominal_int + (1000 - sisa)
        else:
            return nominal_int - sisa
    return int(round(nominal))

def map_nama_karyawan(nama_pendek):
    cursor.execute("SELECT nama FROM master_karyawan WHERE is_active=1 AND REPLACE(LOWER(nama), ' ', '') LIKE %s", (f"%{nama_pendek.lower().replace(' ', '')}%",))
    res = cursor.fetchone()
    return res[0] if res else nama_pendek

def hitung_usia_dan_masa_kerja(tgl_lahir_str, tgl_masuk_str):
    hari_ini = date.today()
    usia_out, masa_kerja_out = "-", "-"
    if tgl_lahir_str:
        try:
            dt_lahir = datetime.strptime(tgl_lahir_str, "%Y-%m-%d").date()
            usia_out = f"{relativedelta(hari_ini, dt_lahir).years} Tahun"
        except: pass
    if tgl_masuk_str:
        try:
            dt_masuk = datetime.strptime(tgl_masuk_str, "%Y-%m-%d").date()
            if hari_ini >= dt_masuk:
                diff_m = relativedelta(hari_ini, dt_masuk)
                parts = []
                if diff_m.years > 0: parts.append(f"{diff_m.years} Tahun")
                if diff_m.months > 0 or diff_m.years == 0: parts.append(f"{diff_m.months} Bulan")
                masa_kerja_out = " ".join(parts)
            else: masa_kerja_out = "Belum Masuk"
        except: pass
    return usia_out, masa_kerja_out

def generate_qr(data):
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def kirim_wa_link(no_telp, nama, plat, jenis, ukuran, paket, h_paket, tambahan, h_tambahan, metode, total_harga, status_loyalti_str, kategori):
    if no_telp.startswith("0"): no_telp = "62" + no_telp[1:]
    pesan = (
        f"*NOTA PEMBAYARAN - {NAMA_BISNIS}*\n-----------------------------------------\n"
        f"Terima kasih telah mempercayakan kendaraan Anda kepada kami.\n\n"
        f"*Detail Pelanggan:*\nNama: {nama}\n{kategori}: {jenis} ({plat})\nUkuran/Tipe: {ukuran}\n\n"
        f"*Rincian Layanan & Tarif:*\n- {paket}: Rp {h_paket:,}\n- Tambahan ({tambahan}): Rp {h_tambahan:,}\n"
        f"-----------------------------------------\n*TOTAL PEMBAYARAN:* Rp {total_harga:,}\n-----------------------------------------\n"
        f"Metode Bayar: {metode}\nStatus Loyalti: {status_loyalti_str}\n-----------------------------------------\n"
        f"Apabila ada yang kurang dari kami silahkan hubungi kami atau kembali ke lokasi untuk kita lakukan perbaikan secara gratis.\n\n"
        f" _{ALAMAT_BISNIS}_\nSemoga kendaraan Anda semakin prima!"
    )
    return f"https://api.whatsapp.com/send?phone={no_telp}&text={urllib.parse.quote(pesan)}"

def cari_pelanggan_pintar(query_str):
    if not query_str: return []
    q_caps = f"%{query_str.upper().replace(' ', '')}%"
    cursor.execute("SELECT o.id, o.nama, o.no_telp, o.total_cuci, o.total_akumulasi, o.total_cuci_motor, o.loyalty_history FROM owners o LEFT JOIN vehicles v ON o.id = v.owner_id WHERE REPLACE(UPPER(o.nama), ' ', '') LIKE %s OR o.no_telp LIKE %s OR REPLACE(UPPER(v.plat_nomor), ' ', '') LIKE %s GROUP BY o.id", (q_caps, q_caps, q_caps))
    return cursor.fetchall()

def get_weeks_of_month(target_date):
    if target_date.day >= 11:
        start_cycle = target_date.replace(day=11)
        end_cycle = (start_cycle + relativedelta(months=1)).replace(day=10)
    else:
        end_cycle = target_date.replace(day=10)
        start_cycle = (end_cycle - relativedelta(months=1)).replace(day=11)
        
    weeks = []
    current_start = start_cycle
    while current_start <= end_cycle:
        days_to_saturday = 6 if current_start.weekday() == 6 else 5 - current_start.weekday()
        current_end = current_start + timedelta(days=days_to_saturday)
        if current_end > end_cycle: current_end = end_cycle
        weeks.append((current_start, current_end))
        current_start = current_end + timedelta(days=1)
    return weeks

def ambil_bon_mingguan_realtime(slot_id, start_date, end_date):
    s_begin = f"{start_date.strftime('%Y-%m-%d')} 00:00:00"
    s_end = f"{end_date.strftime('%Y-%m-%d')} 23:59:59"
    cursor.execute("SELECT SUM(jumlah_bon) FROM kasbon_karyawan WHERE slot_id = %s AND jenis_potongan = 'Mingguan' AND tanggal BETWEEN %s AND %s", (slot_id, s_begin, s_end))
    return cursor.fetchone()[0] or 0

def ambil_bon_bulanan_realtime(slot_id, target_date):
    if target_date.day >= 11:
        start_cycle = target_date.replace(day=11)
        end_cycle = (target_date + relativedelta(months=1)).replace(day=10)
    else:
        start_cycle = (target_date - relativedelta(months=1)).replace(day=11)
        end_cycle = target_date.replace(day=10)
        
    s_begin = f"{start_cycle.strftime('%Y-%m-%d')} 00:00:00"
    s_end = f"{end_cycle.strftime('%Y-%m-%d')} 23:59:59"
    cursor.execute("SELECT SUM(jumlah_bon) FROM kasbon_karyawan WHERE slot_id = %s AND jenis_potongan = 'Bulanan' AND tanggal BETWEEN %s AND %s", (slot_id, s_begin, s_end))
    return cursor.fetchone()[0] or 0

def hitung_gaji_harian(slot_id, nama_karyawan, tanggal_str):
    cursor.execute("SELECT status, jam_masuk, jam_keluar, uang_makan FROM absensi_karyawan WHERE slot_id=%s AND tanggal=%s", (slot_id, tanggal_str))
    row_abs = cursor.fetchone()
    
    cursor.execute("SELECT gaji_mingguan_master FROM master_karyawan WHERE slot_id=%s", (slot_id,))
    row_master = cursor.fetchone()
    gaji_mingguan_master = float(row_master[0]) if row_master and row_master[0] else 0
    
    is_karyawan_lama = any(x in nama_karyawan.lower() for x in ["ibnu", "hendry", "hendri", "raden"])
    
    if row_abs:
        status, j_in, j_out = row_abs[0], row_abs[1], row_abs[2]
    else:
        status = "Masuk" if tanggal_str <= date.today().strftime('%Y-%m-%d') else "Belum Waktunya"
        j_in, j_out = "08:00", "22:00"
    
    if status in ["Libur", "Izin", "Belum Waktunya"]:
        uang_makan = 0
    else:
        if "ibnu" in nama_karyawan.lower(): uang_makan = 30000 if status == "Masuk" else 15000
        elif any(x in nama_karyawan.lower() for x in ["raden", "hendry", "hendri"]): uang_makan = 15000 if status == "Masuk" else 7500
        else: uang_makan = float(row_abs[3]) if (row_abs and row_abs[3] is not None) else 0
            
    cursor.execute("SELECT SUM(nominal_bonus) FROM employee_bonuses WHERE nama_karyawan = %s AND tanggal LIKE %s", (nama_karyawan, f"{tanggal_str}%"))
    res_b = cursor.fetchone()
    bonus_hari_ini = res_b[0] if res_b and res_b[0] else 0
    
    if status in ["Libur", "Izin", "Belum Waktunya"]:
        return bonus_hari_ini + uang_makan, status, 0, bonus_hari_ini, uang_makan

    try: j_in_time = datetime.strptime(j_in, "%H:%M").time()
    except: j_in_time = datetime.strptime("08:00", "%H:%M").time()
    try: j_out_time = datetime.strptime(j_out, "%H:%M").time()
    except: j_out_time = datetime.strptime("22:00", "%H:%M").time()

    if is_karyawan_lama:
        cursor.execute("SELECT s_orang, m_orang, koreksi_s_sgp, koreksi_s_plat, koreksi_s_motor, koreksi_m_sgp, koreksi_m_plat, koreksi_m_motor FROM upah_permobil_daily WHERE tanggal=%s", (tanggal_str,))
        row_upah = cursor.fetchone()
        s_org = row_upah[0] if row_upah and row_upah[0] else 6
        m_org = row_upah[1] if row_upah and row_upah[1] else 6
        k_s_sgp = row_upah[2] if row_upah and row_upah[2] is not None else 0
        k_s_plat = row_upah[3] if row_upah and row_upah[3] is not None else 0
        k_s_motor = row_upah[4] if row_upah and row_upah[4] is not None else 0
        k_m_sgp = row_upah[5] if row_upah and row_upah[5] is not None else 0
        k_m_plat = row_upah[6] if row_upah and row_upah[6] is not None else 0
        k_m_motor = row_upah[7] if row_upah and row_upah[7] is not None else 0
        
        cursor.execute("SELECT tanggal, paket_layanan, kategori_kendaraan FROM transactions WHERE tanggal LIKE %s", (f"{tanggal_str}%",))
        semua_trx = cursor.fetchall()
        
        s_sgp, s_plat, s_motor, m_sgp, m_plat, m_motor = 0, 0, 0, 0, 0, 0
        for t in semua_trx:
            try:
                trx_dt = datetime.strptime(t[0], "%Y-%m-%d %H:%M:%S")
                paket_str_lower = str(t[1]).lower()
                kat_str = str(t[2]).lower()
                is_malam = trx_dt.hour >= 18
                if kat_str == "motor":
                    if is_malam: m_motor += 1
                    else: s_motor += 1
                else:
                    if "platinum" in paket_str_lower:
                        if is_malam: m_plat += 1
                        else: s_plat += 1
                    elif any(x in paket_str_lower for x in ["silver", "gold", "premium", "full wax", "paket 1", "paket 2", "paket 3", "paket 4", "paket 5", "paket 6", "paket 7", "paket 8", "paket 9", "coating"]):
                        if is_malam: m_sgp += 1
                        else: s_sgp += 1
            except: pass
            
        s_sgp = max(0, s_sgp + k_s_sgp)
        s_plat = max(0, s_plat + k_s_plat)
        s_motor = max(0, s_motor + k_s_motor)
        m_sgp = max(0, m_sgp + k_m_sgp)
        m_plat = max(0, m_plat + k_m_plat)
        m_motor = max(0, m_motor + k_m_motor)
        
        upah_siang = ((s_sgp * 5000) + (s_plat * 8000) + (s_motor * 2000)) / s_org if (j_in_time.hour < 18 and s_org > 0) else 0
        upah_malam = ((m_sgp * 8000) + (m_plat * 10000) + (m_motor * 2000)) / m_org if ((j_out_time.hour > 18 or j_out_time.hour == 0) and m_org > 0) else 0
        gaji_base = int(upah_siang + upah_malam)
    else:
        gaji_full_reguler = gaji_mingguan_master / 6.0
        gaji_base = int(gaji_full_reguler) if status == "Masuk" else int(gaji_full_reguler / 2.0)

    return gaji_base + bonus_hari_ini + uang_makan, status, gaji_base, bonus_hari_ini, uang_makan

def hitung_gaji_mingguan_akumulasi(s_id, nama_k, g_mingguan_master, start_date, end_date):
    is_karyawan_lama = any(x in nama_k.lower() for x in ["ibnu", "hendry", "hendri", "raden"])
    gaji_dasar_tanpa_bonus = 0
    total_hari_masuk = 0
    total_setengah = 0
    total_bonus_minggu_ini = 0
    
    curr_d = start_date
    while curr_d <= end_date:
        g_tot, stat_hr, g_base, b_hr, u_mkn = hitung_gaji_harian(s_id, nama_k, curr_d.strftime('%Y-%m-%d'))
        total_bonus_minggu_ini += b_hr
        
        if curr_d <= date.today():
            if stat_hr == "Masuk": total_hari_masuk += 1
            elif stat_hr == "Setengah Hari": total_setengah += 1
            
            if is_karyawan_lama:
                gaji_dasar_tanpa_bonus += g_base + u_mkn
        curr_d += timedelta(days=1)
        
    if not is_karyawan_lama:
        base_bersih = (total_hari_masuk * float(g_mingguan_master) / 6.0) + (total_setengah * float(g_mingguan_master) / 12.0)
        if total_hari_masuk == 7: base_bersih += 50000
        gaji_dasar_tanpa_bonus = int(base_bersih)
        
    gaji_kotor_plus_bonus = gaji_dasar_tanpa_bonus + total_bonus_minggu_ini
    return bulatkan_sabtu_malam(gaji_kotor_plus_bonus), total_hari_masuk, total_bonus_minggu_ini

def get_loyalty_tier(paket_name):
    p = paket_name.upper()
    if "SILVER" in p or "TIDAK CUCI" in p: return None
    if "GOLD" in p: return "Cuci Gold"
    if "PLATINUM" in p: return "Paket Platinum"
    if "FULL WAX" in p: return "Full Wax"
    if "PREMIUM" in p or "PAKET" in p or "COATING" in p: return "Cuci Premium"
    return None

def get_most_frequent(history_str):
    if not history_str: return "-"
    items = [x.strip() for x in history_str.split(',') if x.strip()]
    if not items: return "-"
    return Counter(items).most_common(1)[0][0]

st.markdown("""
    <div style="background: #ffffff; padding: 25px; border-radius: 16px; text-align: center; margin-bottom: 30px; border: 1px solid #bae6fd; box-shadow: 0 4px 20px rgba(56, 189, 248, 0.08);">
        <h1 style="color: #0f172a; font-weight: 800; font-size: 32px; margin: 0; background: linear-gradient(135deg, #0284c7 0%, #38bdf8 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;"> GC Carwash Paris</h1>
        <div style="color: #0284c7; font-size: 11px; letter-spacing: 4px; margin-top: 6px; text-transform: uppercase; font-weight: 600;">Premium Detailing & Nano Ceramic</div>
    </div>
""", unsafe_allow_html=True)

if 'menu_aktif' not in st.session_state: st.session_state.menu_aktif = " POS / Pembayaran"
menu_options = [
    {"label": " POS / Pembayaran", "id": "pos"}, 
    {"label": " Pendaftaran Member", "id": "reg"},
    {"label": " Database Pelanggan", "id": "db"}, 
    {"label": " Laporan Pendapatan", "id": "report"},
    {"label": " Laporan Detailing", "id": "detailing"},
    {"label": " Laundry Karpet", "id": "laundry"}, 
    {"label": " Bonus Karyawan", "id": "bonus"},
    {"label": " Data Karyawan (Master)", "id": "karyawan_master"},
    {"label": " Kasbon Karyawan", "id": "kasbon_core"},
    {"label": " Absensi Karyawan", "id": "absensi_core"},
    {"label": " Upah Permobil", "id": "upah_permobil_core"},
    {"label": " Gaji Karyawan", "id": "gaji_core"},
    {"label": " Data Gaji Terpusat (Matriks)", "id": "data_gaji_matriks"}
]

for menu in menu_options:
    if st.sidebar.button(menu["label"], key=f"btn_nav_{menu['id']}", use_container_width=True):
        st.session_state.menu_aktif = menu["label"]
        st.rerun()

choice = st.session_state.menu_aktif

if "gaji_mingguan_state" not in st.session_state: st.session_state.gaji_mingguan_state = {}
if "gaji_bulanan_state" not in st.session_state: st.session_state.gaji_bulanan_state = {}

if choice == " POS / Pembayaran":
    st.markdown("<h3 style='font-size:18px; font-weight:700;'> Pencarian Pelanggan Pintar</h3>", unsafe_allow_html=True)
    raw_query = st.text_input("Masukkan Nama, Plat Nomor, atau No. HP Pelanggan:", "").strip()
    
    if raw_query:
        all_owners = cari_pelanggan_pintar(raw_query)
        if all_owners:
            selected_owner = None
            if len(all_owners) > 1:
                st.warning(f" Ditemukan {len(all_owners)} data cocok. Silakan tentukan spesifik:")
                opsi_owner = {f"{row[1]} ({row[2]})": row for row in all_owners}
                pilihan_nama = st.selectbox("Pilihan Profil Pelanggan:", list(opsi_owner.keys()))
                selected_owner = opsi_owner[pilihan_nama]
            else: selected_owner = all_owners[0]
                
            o_id, nama, no_telp, total_cuci_dummy, total_akumulasi, total_cuci_motor, history_str = selected_owner
            cursor.execute("SELECT jenis_mobil, ukuran_mobil, plat_nomor, kategori_kendaraan FROM vehicles WHERE owner_id = %s", (o_id,))
            list_mobil = cursor.fetchall()
            
            st.markdown(f"<h3 style='font-size:20px; font-weight:700; border-left: 4px solid #38bdf8; padding-left:10px;'> Kasir Pembayaran Akun: {nama}</h3>", unsafe_allow_html=True)
            st.text(f" No. WhatsApp: {no_telp}")
            st.markdown("####  Detail Transaksi Hari Ini")
            
            opsi_mobil_terdaftar = [f"[{m[3]}] {m[0]} - {m[2]} ({m[1]})" for m in list_mobil if m[2]]
            opsi_mobil_terdaftar.append("Kendaraan Baru / Lainnya")
            pilihan_armada = st.selectbox("Pilih Kendaraan Hari Ini:", opsi_mobil_terdaftar)
            
            if pilihan_armada == "Kendaraan Baru / Lainnya":
                col_kat, col_j, col_u, col_p1, col_p2, col_p3 = st.columns([1.5, 2.5, 1, 1, 1.5, 1])
                with col_kat: kat_final = st.selectbox("Kategori:", ["Mobil", "Motor"], key="pos_k_baru")
                with col_j: jenis_final = st.text_input("Nama Kendaraan:", placeholder="Avanza / Vario", key="pos_j_baru").strip()
                with col_u:
                    opsi_ukuran = ["S", "M", "L", "XL"] if kat_final == "Mobil" else ["M", "L", "XL", "HARLEY"]
                    ukuran_mobil = st.selectbox("Size:", opsi_ukuran, key="pos_u_baru")
                with col_p1: p_wil = st.text_input("Wilayah", key="pos_p_wil", max_chars=2).upper().strip()
                with col_p2: p_num = st.text_input("Nomor", key="pos_p_num", max_chars=4).strip()
                with col_p3: p_seri = st.text_input("Seri", key="pos_p_seri", max_chars=3).upper().strip()
                
                plat_final = f"{p_wil} {p_num} {p_seri}".strip() if (p_wil and p_num) else ""
                
                if plat_final and st.checkbox("Simpan kendaraan baru ini ke akun pelanggan secara permanen"):
                    try:
                        cursor.execute("INSERT INTO vehicles (owner_id, jenis_mobil, ukuran_mobil, plat_nomor, kategori_kendaraan) VALUES (%s, %s, %s, %s, %s)", (o_id, jenis_final, ukuran_mobil, plat_final, kat_final))
                        conn.commit()
                    except IntegrityError:
                        conn.rollback()
                        pass
            else:
                kat_final = pilihan_armada.split("]")[0].replace("[", "")
                detail_sisa = pilihan_armada.split("] ")[1]
                jenis_final = detail_sisa.split(" - ")[0]
                plat_final = detail_sisa.split(" - ")[1].split(" (")[0]
                ukuran_mobil = detail_sisa.split("(")[1].replace(")", "")
            
            daftar_paket_tersedia = DATA_PAKET_MOBIL[ukuran_mobil] if kat_final == "Mobil" else DATA_PAKET_MOTOR[ukuran_mobil]
            
            is_gratis = False
            diskon_max = 0
            most_freq = "-"
            history_list = []
            
            if kat_final == "Mobil":
                st.markdown("---")
                st.markdown("#### 🛠️ Atur Progress Loyalty Manual")
                
                history_list = [x.strip() for x in (history_str if history_str else "").split(',') if x.strip()]
                progress_saat_ini = len(history_list)
                most_freq_temp = get_most_frequent(history_str) if history_list else "-"
                
                progress_baru = st.number_input(
                    "Jumlah Cuci (Progress Loyalty Saat Ini):", 
                    min_value=0, max_value=8, value=progress_saat_ini, step=1,
                    help="Tekan tombol (+ / -) untuk menambah atau mengurangi progres loyalty manual sebelum transaksi."
                )
                
                if progress_baru != progress_saat_ini:
                    if progress_baru > progress_saat_ini:
                        selisih = progress_baru - progress_saat_ini
                        pad_item = most_freq_temp if most_freq_temp != "-" else "Cuci Premium"
                        history_list.extend([pad_item] * selisih)
                    else:
                        history_list = history_list[:progress_baru]
                    history_str = ",".join(history_list)
                
                is_gratis = len(history_list) >= 8
                most_freq = get_most_frequent(history_str) if history_list else "-"
                
                if is_gratis:
                    diskon_max = DATA_PAKET_MOBIL[ukuran_mobil].get(most_freq, 0)
                    st.success(f"🎉 REWARD TIME! Pelanggan berhak klaim cuci gratis. Paket Dominan: {most_freq} (Potongan Rp {diskon_max:,}).")
                else:
                    if history_list: st.info(f"🎖️ Loyalty Progress: {len(history_list)}/8. Estimasi Reward ke-9: {most_freq}")
                    else: st.info("🎖️ Loyalty Progress: 0/8. Belum ada cuci yang masuk kriteria (Gold/Premium/Platinum/Full Wax).")
            
            paket_pilihan = st.selectbox("1. Pilih Paket Cuci Utama:", list(daftar_paket_tersedia.keys()))
            harga_paket_final = st.number_input("Harga Paket Utama:", min_value=0, value=int(daftar_paket_tersedia[paket_pilihan]), step=1000)
            
            tier = get_loyalty_tier(paket_pilihan) if kat_final == "Mobil" else None
            
            karyawan_paket = ""
            if any(x in paket_pilihan.upper() for x in ["PAKET", "PLATINUM", "FULL WAX", "COATING"]):
                karyawan_paket = st.text_input(f" Karyawan Paket Utama ({paket_pilihan}):", placeholder="Contoh: ibnu, hendry").strip()
            
            tambahan_pilihan = st.selectbox("2. Tambahan Paket / Layanan Tambahan:", list(DATA_TAMBAHAN[ukuran_mobil].keys()))
            nama_tambahan_final = st.text_input("Masukkan Nama Layanan Tambahan Custom:", value="Layanan Custom").strip() if tambahan_pilihan == "Layanan Custom / Lainnya" else tambahan_pilihan
            harga_tambahan_final = st.number_input("Harga Paket Tambahan:", min_value=0, value=int(DATA_TAMBAHAN[ukuran_mobil][tambahan_pilihan]), step=1000)
            
            karyawan_tambahan = ""
            bonus_tambahan = 0
            if tambahan_pilihan != "Tanpa Tambahan":
                karyawan_tambahan = st.text_input(" Karyawan yang Mengerjakan Tambahan:", placeholder="Contoh: ibnu, hendry").strip()
                if karyawan_tambahan:
                    if tambahan_pilihan == "Paket Oli Plastik":
                        bonus_tambahan = 5000
                        st.info("Bonus otomatis Rp 5.000/orang untuk Paket Oli Plastik.")
                    else:
                        bonus_tambahan = st.number_input("Nominal Bonus per Orang (Rp) (Kosongkan/Isi manual untuk Custom):", min_value=0, value=0, step=1000)

            metode_bayar = st.selectbox("3. Metode Pembayaran:", ["Cash", "QRIS", "Debit"])
            st.markdown("---")
            
            if is_gratis and kat_final == "Mobil":
                harga_paket_setelah_diskon = max(0, harga_paket_final - diskon_max)
                if harga_paket_setelah_diskon > 0:
                    st.warning(f"Total Paket: Rp {harga_paket_final:,}. Dipotong Free {most_freq}: Rp {diskon_max:,}. Sisa bayar selisih: Rp {harga_paket_setelah_diskon:,}")
            else:
                harga_paket_setelah_diskon = harga_paket_final
                
            total_harga = harga_paket_setelah_diskon + harga_tambahan_final
            
            st.markdown(f' <div style="background-color: #ffffff; border: 1px solid #bae6fd; padding: 20px; border-radius: 12px; margin-bottom: 20px;"><h2 style="margin: 0; font-weight:700; font-size:24px;"> Total Pembayaran: <span style="color:#0284c7;">Rp {total_harga:,}</span></h2></div>', unsafe_allow_html=True)
            
            if kat_final == "Mobil":
                if is_gratis:
                    status_loyalti_str = f"KLAIM REWARD: Diskon Cuci {most_freq} (-Rp {diskon_max:,})"
                else:
                    new_len = len(history_list) + (1 if tier else 0)
                    est_reward = most_freq if history_list else (tier if tier else "Belum ada")
                    if tier: status_loyalti_str = f"Cuci ke {new_len} dari 8. (Estimasi Reward ke-9: {est_reward})"
                    else: status_loyalti_str = f"Cuci ke {len(history_list)} dari 8. (Paket Silver tidak menambah loyalty)"
            else:
                status_loyalti_str = "Non-Member (Motor No Loyalty)"
                
            wa_url = kirim_wa_link(no_telp, nama, plat_final, jenis_final, ukuran_mobil, paket_pilihan, harga_paket_setelah_diskon, nama_tambahan_final, harga_tambahan_final, metode_bayar, total_harga, status_loyalti_str, kat_final)
            
            if st.button(" Konfirmasi & Simpan Transaksi", use_container_width=True):
                waktu_sekarang = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                baru_akumulasi = (total_akumulasi if total_akumulasi else 0) + 1
                
                if kat_final == "Mobil":
                    if is_gratis:
                        cursor.execute("UPDATE owners SET total_cuci = 0, loyalty_history = '', total_akumulasi = %s WHERE id = %s", (baru_akumulasi, o_id))
                    else:
                        if tier:
                            new_hist_list = history_list + [tier]
                            new_hist_str = ",".join(new_hist_list)
                            cursor.execute("UPDATE owners SET total_cuci = %s, loyalty_history = %s, total_akumulasi = %s WHERE id = %s", (len(new_hist_list), new_hist_str, baru_akumulasi, o_id))
                        else:
                            cursor.execute("UPDATE owners SET total_cuci = %s, loyalty_history = %s, total_akumulasi = %s WHERE id = %s", (len(history_list), history_str, baru_akumulasi, o_id))
                else:
                    cursor.execute("UPDATE owners SET total_cuci_motor = %s, total_akumulasi = %s WHERE id = %s", ((total_cuci_motor if total_cuci_motor else 0) + 1, baru_akumulasi, o_id))
                
                kategori_laporan = "Detailing" if any(x in paket_pilihan.upper() for x in ["PAKET 3", "PAKET 4", "PAKET 5", "PAKET 6", "COATING"]) else "Umum"
                
                cursor.execute("INSERT INTO transactions (tanggal, nama_pelanggan, jenis_mobil, ukuran_mobil, plat_nomor, paket_layanan, tambahan_layanan, metode_bayar, nominal, kategori_kendaraan, harga_paket_real, harga_tambahan_real, kategori_laporan) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (waktu_sekarang, nama, jenis_final, ukuran_mobil, plat_final, paket_pilihan, nama_tambahan_final, metode_bayar, total_harga, kat_final, harga_paket_final, harga_tambahan_final, kategori_laporan))
                
                tb_total = 0
                if karyawan_paket:
                    dp = [n.strip() for n in karyawan_paket.split(",") if n.strip()]
                    if dp:
                        paket_upper = paket_pilihan.upper()
                        
                        if "COATING" in paket_upper:
                            h_p4 = DATA_PAKET_MOBIL.get(ukuran_mobil, {}).get("PAKET 4 (CUCI HIDROLIK + DETAILING LUAR DALAM)", 0)
                            h_p5 = DATA_PAKET_MOBIL.get(ukuran_mobil, {}).get("PAKET 5 (CUCI HIDROLIK + DETAILING MESIN)", 0)
                            upah_p4 = h_p4 * 0.35
                            upah_p5 = h_p5 * 0.20
                            upah_p1 = 20000
                            if ukuran_mobil == "S": upah_app = 130000
                            elif ukuran_mobil == "M": upah_app = 140000
                            elif ukuran_mobil == "L": upah_app = 150000
                            elif ukuran_mobil == "XL": upah_app = 170000
                            else: upah_app = 0
                            
                            tb_total = upah_p4 + upah_p5 + upah_p1 + upah_app
                            
                        elif any(x in paket_upper for x in ["PAKET 3", "PAKET 4", "PAKET 6"]):
                            tb_total = harga_paket_final * 0.35
                        elif "PAKET 5" in paket_upper:
                            tb_total = harga_paket_final * 0.20
                        elif any(x in paket_upper for x in ["PAKET 1", "PAKET 2", "PAKET 7", "PAKET 9"]):
                            tb_total = 20000
                        elif "PLATINUM" in paket_upper:
                            tb_total = harga_paket_final * 0.025
                        elif "FULL WAX" in paket_upper:
                            tb_total = 10000
                        else:
                            tb_total = 10000
                        
                        tb_per_orang = int(tb_total / len(dp))
                        
                        for kry in dp: 
                            kry_full = map_nama_karyawan(kry)
                            cursor.execute("INSERT INTO employee_bonuses (tanggal, nama_karyawan, jenis_bonus, nominal_bonus) VALUES (%s, %s, %s, %s)", (waktu_sekarang, kry_full, f"Bonus {paket_pilihan.split(' ')[0]}", tb_per_orang))
                
                if kategori_laporan == "Detailing":
                    bersih = total_harga - int(tb_total)
                    cursor.execute("INSERT INTO detailing_trx (tanggal, nama_pelanggan, no_hp, jenis_mobil, ukuran_mobil, plat_nomor, paket_detailing, metode_bayar, nominal, pekerja, upah_pekerja, bersih) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (waktu_sekarang, nama, no_telp, jenis_final, ukuran_mobil, plat_final, paket_pilihan, metode_bayar, total_harga, karyawan_paket, int(tb_total), bersih))

                if karyawan_tambahan and bonus_tambahan > 0:
                    dt = [n.strip() for n in karyawan_tambahan.split(",") if n.strip()]
                    tb_tambahan_bulat = int(bonus_tambahan)
                    for kry in dt:
                        kry_full = map_nama_karyawan(kry)
                        cursor.execute("INSERT INTO employee_bonuses (tanggal, nama_karyawan, jenis_bonus, nominal_bonus) VALUES (%s, %s, %s, %s)", (waktu_sekarang, kry_full, f"Bonus Tambahan: {nama_tambahan_final}", tb_tambahan_bulat))
                        
                conn.commit()
                st.success(" Transaksi Sukses Ditulis! Upah Permobil Washer otomatis diperbarui.")
                st.markdown(f'<a href="{wa_url}" target="_blank" style="text-decoration:none;"><button class="btn-whatsapp-custom"> KIRIM NOTA KE WHATSAPP KLIEN</button></a>', unsafe_allow_html=True)

elif choice == " Pendaftaran Member":
    st.markdown("<h3 style='font-size:18px; font-weight:700;'> Registrasi Akun & Multi Kendaraan</h3>", unsafe_allow_html=True)
    t_baru, t_tambah_unit = st.tabs([" BUAT AKUN BARU", " TAMBAH KENDARAAN MEMBER LAMA"])
    
    with t_baru:
        nama_input = st.text_input("Nama Lengkap Pemilik:").strip()
        telp_input = st.text_input("Nomor WhatsApp Utama:").strip()
        
        st.markdown("---")
        with st.expander("🛠️ Migrasi Data Kartu Stempel Lama (Opsional)", expanded=False):
            st.info("Jika pelanggan memiliki stempel di kartu fisik lama, masukkan jumlah riwayatnya di bawah ini agar loyalty-nya otomatis terhitung.")
            col_lg1, col_lg2 = st.columns(2)
            with col_lg1:
                c_g = st.number_input("Jumlah Cuci Gold:", min_value=0, value=0)
                c_pr = st.number_input("Jumlah Cuci Premium / Paket 1-9:", min_value=0, value=0)
            with col_lg2:
                c_pl = st.number_input("Jumlah Cuci Platinum:", min_value=0, value=0)
                c_fw = st.number_input("Jumlah Full Wax:", min_value=0, value=0)

        st.markdown("---")
        st.markdown("###  Pengisian Data Kendaraan Pertama")
        col_kat, col_j, col_u, col_p1, col_p2, col_p3 = st.columns([1.5, 2.5, 1, 1, 1.5, 1])
        with col_kat: kat = st.selectbox("Kategori:", ["Mobil", "Motor"], key="kat_reg_1")
        with col_j: j = st.text_input("Nama Kendaraan:", placeholder="Avanza / Vario", key="j_reg_1").strip()
        with col_u:
            opsi_uk = ["S", "M", "L", "XL"] if kat == "Mobil" else ["M", "L", "XL", "HARLEY"]
            u = st.selectbox("Size:", opsi_uk, key="u_reg_1")
        with col_p1: p1 = st.text_input("Wilayah", key="p1_r1", max_chars=2).upper().strip()
        with col_p2: p2 = st.text_input("Nomor", key="p2_r1", max_chars=4).strip()
        with col_p3: p3 = st.text_input("Seri", key="p3_r1", max_chars=3).upper().strip()
        plat_gabung = f"{p1} {p2} {p3}".strip() if (p1 and p2) else ""
        
        if st.button(" Simpan Akun Member Baru", use_container_width=True):
            if not nama_input or not telp_input or not j or not plat_gabung: 
                st.error(" Mohon isi semua informasi secara lengkap!")
            else:
                new_hist = (["Cuci Gold"]*c_g) + (["Cuci Premium"]*c_pr) + (["Paket Platinum"]*c_pl) + (["Full Wax"]*c_fw)
                new_hist_str = ",".join(new_hist)
                total_cuci_awal = len(new_hist)
                
                try:
                    cursor.execute("INSERT INTO owners (nama, no_telp, total_cuci, total_akumulasi, total_cuci_motor, loyalty_history) VALUES (%s, %s, %s, 0, 0, %s)", (nama_input, telp_input, total_cuci_awal, new_hist_str))
                    conn.commit()
                except IntegrityError:
                    conn.rollback()
                    pass
                
                cursor.execute("SELECT id FROM owners WHERE no_telp = %s", (telp_input,))
                owner_id = cursor.fetchone()[0]
                try:
                    cursor.execute("INSERT INTO vehicles (owner_id, jenis_mobil, ukuran_mobil, plat_nomor, kategori_kendaraan) VALUES (%s, %s, %s, %s, %s)", (owner_id, j, u, plat_gabung, kat))
                    conn.commit()
                    st.success(f" Berhasil mendaftarkan akun {nama_input} beserta riwayat stempelnya!")
                    st.image(generate_qr(telp_input), width=200)
                except IntegrityError:
                    conn.rollback()
                    st.error("Plat sudah terdaftar.")
                    
    with t_tambah_unit:
        cari_owner_key = st.text_input("Ketik Nama / No HP Member Lama:", key="search_old_owner")
        if cari_owner_key:
            res_owners = cari_pelanggan_pintar(cari_owner_key)
            if res_owners:
                dict_select = {f"{r[1]} ({r[2]})": r for r in res_owners}
                pilihan_nama_lama = st.selectbox("Klik/Pilih Profil Akun Member:", list(dict_select.keys()))
                o_terpilih = dict_select[pilihan_nama_lama]
                col_kat2, col_j2, col_u2, col_p1_2, col_p2_2, col_p3_2 = st.columns([1.5, 2.5, 1, 1, 1.5, 1])
                with col_kat2: kat2 = st.selectbox("Kategori Unit:", ["Mobil", "Motor"], key="kat_reg_2")
                with col_j2: j2 = st.text_input("Nama Kendaraan:", placeholder="Fortuner / Nmax", key="j_reg_2").strip()
                with col_u2:
                    opsi_uk2 = ["S", "M", "L", "XL"] if kat2 == "Mobil" else ["M", "L", "XL", "HARLEY"]
                    u2 = st.selectbox("Size:", opsi_uk2, key="u2_reg_2")
                with col_p1_2: p1_2 = st.text_input("Wilayah", key="p1_r2", max_chars=2).upper().strip()
                with col_p2_2: p2_2 = st.text_input("Nomor", key="p2_r2", max_chars=4).strip()
                with col_p3_2: p3_2 = st.text_input("Seri", key="p3_r2", max_chars=3).upper().strip()
                plat_gabung2 = f"{p1_2} {p2_2} {p3_2}".strip() if (p1_2 and p2_2) else ""
                if st.button(" Daftarkan Kendaraan Utama/Tambahan", use_container_width=True) and j2 and plat_gabung2:
                    try:
                        cursor.execute("INSERT INTO vehicles (owner_id, jenis_mobil, ukuran_mobil, plat_nomor, kategori_kendaraan) VALUES (%s, %s, %s, %s, %s)", (o_terpilih[0], j2, u2, plat_gabung2, kat2))
                        conn.commit(); st.success("Sukses menambahkan kendaraan!")
                    except IntegrityError:
                        conn.rollback()
                        st.error("Plat sudah terdaftar.")

elif choice == " Database Pelanggan":
    st.markdown("<h3 style='font-size:18px; font-weight:700;'> Database & Manajemen Data Pelanggan</h3>", unsafe_allow_html=True)
    t_db_utama, t_db_history = st.tabs([" DATABASE UTAMA", " DATA TERDAHULU PELANGGAN"])
    
    with t_db_utama:
        cursor.execute("SELECT id, nama, no_telp, total_cuci, total_cuci_motor, total_akumulasi FROM owners")
        processed_data = []
        for row in cursor.fetchall():
            o_id, o_nama, o_telp, t_cuci, t_motor, t_akumulasi = row
            cursor.execute("SELECT kategori_kendaraan, jenis_mobil, ukuran_mobil, plat_nomor FROM vehicles WHERE owner_id = %s", (o_id,))
            v_rows = cursor.fetchall()
            v_list = [f"[{vr[0].upper()}] {vr[1]} ({vr[3]})" for vr in v_rows if vr[3]]
            has_mobil = any(vr[0] == "Mobil" for vr in v_rows)
            processed_data.append({
                "Pilih": False, "ID Akun": o_id, "Nama Pelanggan": o_nama, "Nomor WhatsApp": o_telp,
                "Daftar Unit Kendaraan": " | ".join(v_list) if v_list else "-",
                "Loyalty Mobil": f"{t_cuci}/8" if has_mobil else "-", "Total Mobil": str(t_akumulasi) if has_mobil else "-", "Total Motor": str(t_motor)
            })
        df_o_display = pd.DataFrame(processed_data)
        if not df_o_display.empty:
            edited_df_o = st.data_editor(df_o_display, disabled=["ID Akun", "Daftar Unit Kendaraan", "Loyalty Mobil", "Total Mobil", "Total Motor"], use_container_width=True, key="ed_owner_v7")
            c_o1, c_o2 = st.columns([4, 1])
            with c_o1:
                if st.button(" Simpan Perubahan Nama & Kontak", use_container_width=True):
                    for idx, r in edited_df_o.iterrows(): cursor.execute("UPDATE owners SET nama = %s, no_telp = %s WHERE id = %s", (r['Nama Pelanggan'], r['Nomor WhatsApp'], r['ID Akun']))
                    conn.commit(); st.success(" Profil Pelanggan diperbarui!"); st.rerun()
            with c_o2:
                ld = edited_df_o[edited_df_o['Pilih'] == True]['ID Akun'].tolist()
                if st.button(f" Hapus Akun", type="primary", use_container_width=True) and ld:
                    for target_id in ld: 
                        cursor.execute("DELETE FROM owners WHERE id = %s", (int(target_id),))
                        cursor.execute("DELETE FROM vehicles WHERE owner_id = %s", (int(target_id),))
                    conn.commit(); st.success(" Akun dihapus!"); st.rerun()
        else: st.info(" Belum ada data pelanggan.")
        
    with t_db_history:
        st.markdown("#### Histori Transaksi Pelanggan & Analitik")
        search_hist = st.text_input("Ketik Nama / No HP Pelanggan untuk melihat data pencucian terdahulu:", key="search_hist_input").strip()
        
        if search_hist:
            hist_owners = cari_pelanggan_pintar(search_hist)
            if hist_owners:
                if len(hist_owners) > 1:
                    opsi_h_owner = {f"{row[1]} ({row[2]})": row for row in hist_owners}
                    pilih_h_nama = st.selectbox("Pilih Pelanggan:", list(opsi_h_owner.keys()), key="sel_hist")
                    sel_h_owner = opsi_h_owner[pilih_h_nama]
                else:
                    sel_h_owner = hist_owners[0]
                    
                h_id, h_nama, h_telp, _, _, _, _ = sel_h_owner
                
                cursor.execute("SELECT tanggal, kategori_kendaraan, plat_nomor, paket_layanan, nominal FROM transactions WHERE nama_pelanggan = %s ORDER BY id DESC", (h_nama,))
                trx_history_data = cursor.fetchall()
                
                if trx_history_data:
                    # Hitung rata-rata
                    tgl_pertama_str = trx_history_data[-1][0]
                    tgl_terakhir_str = trx_history_data[0][0]
                    
                    try:
                        tgl_pertama = datetime.strptime(tgl_pertama_str, "%Y-%m-%d %H:%M:%S")
                        tgl_terakhir = datetime.strptime(tgl_terakhir_str, "%Y-%m-%d %H:%M:%S")
                        hari_diff = (tgl_terakhir - tgl_pertama).days
                        bulan_diff = hari_diff / 30.0
                        if bulan_diff < 1: bulan_diff = 1.0
                    except:
                        bulan_diff = 1.0
                        
                    total_cuci_all = len(trx_history_data)
                    rata_rata_bulan = round(total_cuci_all / bulan_diff, 1)
                    
                    st.markdown(f"**Profil Ditemukan:** {h_nama} ({h_telp})")
                    col_met1, col_met2 = st.columns(2)
                    with col_met1: st.metric("Total Transaksi Terdata", f"{total_cuci_all} kali")
                    with col_met2: st.metric("Estimasi Cuci per Bulan", f"{rata_rata_bulan} kali / bulan")
                    
                    df_hist_display = pd.DataFrame(trx_history_data, columns=["Waktu", "Kategori", "Plat Nomor", "Paket Layanan", "Harga (Rp)"])
                    st.dataframe(df_hist_display, use_container_width=True)
                else:
                    st.info("Belum ada histori transaksi untuk pelanggan ini.")
            else:
                st.warning("Data pelanggan tidak ditemukan.")

elif choice == " Laporan Pendapatan":
    st.markdown("<h3 style='font-size:18px; font-weight:700;'> Laporan Pendapatan</h3>", unsafe_allow_html=True)
    t_lap_harian, t_lap_total = st.tabs([" LAPORAN HARIAN", " TOTAL PENDAPATAN"])
    
    with t_lap_harian:
        pilihan_tgl = st.date_input(" Pilih Tanggal:", value=date.today())
        tgl_awal_str, tgl_akhir_str = f"{pilihan_tgl.strftime('%Y-%m-%d')} 00:00:00", f"{pilihan_tgl.strftime('%Y-%m-%d')} 23:59:59"
        
        cursor.execute("SELECT SUM(nominal) FROM transactions WHERE metode_bayar = 'Cash' AND COALESCE(kategori_laporan, 'Umum') = 'Umum' AND tanggal BETWEEN %s AND %s", (tgl_awal_str, tgl_akhir_str))
        tc = cursor.fetchone()[0] or 0
        cursor.execute("SELECT SUM(nominal) FROM transactions WHERE metode_bayar = 'QRIS' AND COALESCE(kategori_laporan, 'Umum') = 'Umum' AND tanggal BETWEEN %s AND %s", (tgl_awal_str, tgl_akhir_str))
        tq = cursor.fetchone()[0] or 0
        cursor.execute("SELECT SUM(nominal) FROM transactions WHERE metode_bayar = 'Debit' AND COALESCE(kategori_laporan, 'Umum') = 'Umum' AND tanggal BETWEEN %s AND %s", (tgl_awal_str, tgl_akhir_str))
        td = cursor.fetchone()[0] or 0
        gt = tc + tq + td
        
        st.markdown(f' <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 15px; margin-bottom: 25px;"><div style="background-color: #ffffff; padding: 20px; border-radius: 12px; border-left: 4px solid #64748b;"> CASH<br><b>Rp {tc:,}</b></div><div style="background-color: #ffffff; padding: 20px; border-radius: 12px; border-left: 4px solid #38bdf8;"> QRIS<br><b style="color:#0284c7;">Rp {tq:,}</b></div><div style="background-color: #ffffff; padding: 20px; border-radius: 12px; border-left: 4px solid #7dd3fc;"> DEBIT<br><b>Rp {td:,}</b></div><div style="background: linear-gradient(135deg, #0284c7 0%, #38bdf8 100%); padding: 20px; border-radius: 12px;"><span style="color:white; font-size:11px;"> GRAND TOTAL OMSET UMUM</span><h3 style="color:white; margin:0; font-size:22px;">Rp {gt:,}</h3></div></div>', unsafe_allow_html=True)
        
        cursor.execute("SELECT kategori_kendaraan, paket_layanan FROM transactions WHERE tanggal BETWEEN %s AND %s", (tgl_awal_str, tgl_akhir_str))
        trx_harian = cursor.fetchall()
        
        mobil_silver = mobil_gold = mobil_premium = mobil_platinum = mobil_lainnya = total_mobil = 0
        motor_biasa = motor_wax = motor_lainnya = total_motor = 0
        
        for kat, paket in trx_harian:
            paket_lower = str(paket).lower()
            if kat == "Mobil":
                total_mobil += 1
                if "silver" in paket_lower: mobil_silver += 1
                elif "gold" in paket_lower: mobil_gold += 1
                elif "premium" in paket_lower: mobil_premium += 1
                elif "platinum" in paket_lower: mobil_platinum += 1
                elif any(x in paket_lower for x in ["full wax", "paket 1", "paket 2", "paket 3", "paket 4", "paket 5", "paket 6", "paket 7", "paket 8", "paket 9", "coating"]): mobil_premium += 1
                else: mobil_lainnya += 1
            elif kat == "Motor":
                total_motor += 1
                if "biasa" in paket_lower: motor_biasa += 1
                elif "wax" in paket_lower: motor_wax += 1
                else: motor_lainnya += 1

        st.markdown("####  Rekapitulasi Unit Kendaraan Harian")
        col_rek_m, col_rek_mtr = st.columns(2)
        with col_rek_m:
            st.markdown(f'''
            <div style="background:#ffffff; padding:15px; border-radius:10px; border:1px solid #cbd5e1;">
                <h5 style="margin-top:0; color:#0284c7;">🚗 Kategori Mobil</h5>
                <ul style="list-style-type:none; padding-left:0; margin-bottom:0;">
                    <li>Paket Silver: <b>{mobil_silver}</b> unit</li>
                    <li>Paket Gold: <b>{mobil_gold}</b> unit</li>
                    <li>Paket Premium (termasuk Full Wax & Paket Detailing): <b>{mobil_premium}</b> unit</li>
                    <li>Paket Platinum: <b>{mobil_platinum}</b> unit</li>
                    <li>Lainnya (termasuk paket custom/detailing): <b>{mobil_lainnya}</b> unit</li>
                    <hr style="margin:10px 0;">
                    <li style="font-size:16px;"><b>Total Mobil Hari Ini: {total_mobil} unit</b></li>
                </ul>
            </div>
            ''', unsafe_allow_html=True)
            
        with col_rek_mtr:
            st.markdown(f'''
            <div style="background:#ffffff; padding:15px; border-radius:10px; border:1px solid #cbd5e1;">
                <h5 style="margin-top:0; color:#16a34a;">🏍️ Kategori Motor</h5>
                <ul style="list-style-type:none; padding-left:0; margin-bottom:0;">
                    <li>Cuci Biasa: <b>{motor_biasa}</b> unit</li>
                    <li>Cuci Wax: <b>{motor_wax}</b> unit</li>
                    <li>Lainnya: <b>{motor_lainnya}</b> unit</li>
                    <br><br>
                    <hr style="margin:10px 0;">
                    <li style="font-size:16px;"><b>Total Motor Hari Ini: {total_motor} unit</b></li>
                </ul>
            </div>
            ''', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        df_income = pd.read_sql_query("SELECT id, tanggal, nama_pelanggan, kategori_kendaraan, jenis_mobil, ukuran_mobil, plat_nomor, paket_layanan, tambahan_layanan, metode_bayar, nominal FROM transactions WHERE COALESCE(kategori_laporan, 'Umum') = 'Umum' AND tanggal BETWEEN %s AND %s ORDER BY id DESC", conn, params=(tgl_awal_str, tgl_akhir_str))
        if not df_income.empty:
            df_income.insert(0, "Pilih", False)
            df_income.columns = [' Pilih', 'ID Nota', 'Waktu', 'Pelanggan', 'Kategori', 'Kendaraan', 'Ukuran', 'Plat Nomor', 'Paket Utama', 'Tambahan', 'Metode', 'Total Dibayar (Rp)']
            
            disabled_cols_inc = [c for c in df_income.columns if c not in [' Pilih', 'Metode']]
            
            edited_income = st.data_editor(
                df_income, 
                disabled=disabled_cols_inc,
                column_config={"Metode": st.column_config.SelectboxColumn(options=["Cash", "QRIS", "Debit"])},
                use_container_width=True, 
                key="ed_income_v6"
            )
            
            col_inc1, col_inc2 = st.columns([4, 1])
            with col_inc1:
                if st.button(" Simpan Perubahan Metode Bayar", key="btn_simpan_inc", use_container_width=True):
                    for idx, row in edited_income.iterrows():
                        cursor.execute("UPDATE transactions SET metode_bayar = %s WHERE id = %s", (row['Metode'], int(row['ID Nota'])))
                    conn.commit(); st.success("Metode bayar berhasil diperbarui!"); st.rerun()
            with col_inc2:
                lt = edited_income[edited_income[' Pilih'] == True]['ID Nota'].tolist()
                if st.button(f" Hapus Nota Terpilih ({len(lt)})", type="primary", use_container_width=True) and lt:
                    for target_id in lt:
                        # --- LOGIC ROLLBACK LOYALTY ---
                        cursor.execute("SELECT plat_nomor, kategori_kendaraan, paket_layanan FROM transactions WHERE id = %s", (int(target_id),))
                        trx_info = cursor.fetchone()
                        if trx_info:
                            t_plat, t_kat, t_paket = trx_info
                            cursor.execute("SELECT owner_id FROM vehicles WHERE plat_nomor = %s", (t_plat,))
                            v_info = cursor.fetchone()
                            if v_info:
                                owner_id = v_info[0]
                                cursor.execute("SELECT total_akumulasi, total_cuci, total_cuci_motor, loyalty_history FROM owners WHERE id = %s", (owner_id,))
                                o_info = cursor.fetchone()
                                if o_info:
                                    t_akumulasi, t_cuci, t_motor, h_str = o_info
                                    new_akumulasi = max(0, (t_akumulasi if t_akumulasi else 0) - 1)
                                    
                                    if t_kat == "Mobil":
                                        tier = get_loyalty_tier(t_paket)
                                        if tier and h_str:
                                            h_list = [x.strip() for x in h_str.split(',') if x.strip()]
                                            if h_list and h_list[-1] == tier:
                                                h_list.pop()
                                            new_h_str = ",".join(h_list)
                                            cursor.execute("UPDATE owners SET total_cuci = %s, loyalty_history = %s, total_akumulasi = %s WHERE id = %s", (len(h_list), new_h_str, new_akumulasi, owner_id))
                                        else:
                                            cursor.execute("UPDATE owners SET total_akumulasi = %s WHERE id = %s", (new_akumulasi, owner_id))
                                    elif t_kat == "Motor":
                                        new_motor = max(0, (t_motor if t_motor else 0) - 1)
                                        cursor.execute("UPDATE owners SET total_cuci_motor = %s, total_akumulasi = %s WHERE id = %s", (new_motor, new_akumulasi, owner_id))
                        
                        # --- HAPUS TRANSAKSI ---
                        cursor.execute("DELETE FROM transactions WHERE id = %s", (int(target_id),))
                    conn.commit(); st.success(" Transaksi dibersihkan & Loyalty berhasil di-rollback!"); st.rerun()

    with t_lap_total:
        st.markdown("####  Total Pendapatan Berdasarkan Rentang Waktu")
        st.info("Pilih tanggal awal dan akhir (misal: Tanggal 1 s/d 20) untuk melihat total pendapatan secara keseluruhan.")
        rentang_tgl = st.date_input("Pilih Rentang Tanggal:", value=(date.today(), date.today()), key="rentang_total_input")
        
        if isinstance(rentang_tgl, tuple) and len(rentang_tgl) == 2:
            tgl_awal_tot_str = f"{rentang_tgl[0].strftime('%Y-%m-%d')} 00:00:00"
            tgl_akhir_tot_str = f"{rentang_tgl[1].strftime('%Y-%m-%d')} 23:59:59"
            
            cursor.execute("SELECT SUM(nominal) FROM transactions WHERE metode_bayar = 'Cash' AND COALESCE(kategori_laporan, 'Umum') = 'Umum' AND tanggal BETWEEN %s AND %s", (tgl_awal_tot_str, tgl_akhir_tot_str))
            tc_tot = cursor.fetchone()[0] or 0
            cursor.execute("SELECT SUM(nominal) FROM transactions WHERE metode_bayar = 'QRIS' AND COALESCE(kategori_laporan, 'Umum') = 'Umum' AND tanggal BETWEEN %s AND %s", (tgl_awal_tot_str, tgl_akhir_tot_str))
            tq_tot = cursor.fetchone()[0] or 0
            cursor.execute("SELECT SUM(nominal) FROM transactions WHERE metode_bayar = 'Debit' AND COALESCE(kategori_laporan, 'Umum') = 'Umum' AND tanggal BETWEEN %s AND %s", (tgl_awal_tot_str, tgl_akhir_tot_str))
            td_tot = cursor.fetchone()[0] or 0
            gt_tot = tc_tot + tq_tot + td_tot
            
            st.markdown(f' <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 15px; margin-top: 15px;"><div style="background-color: #ffffff; padding: 20px; border-radius: 12px; border-left: 4px solid #64748b; box-shadow: 0 2px 10px rgba(0,0,0,0.05);"> TOTAL CASH<br><b>Rp {tc_tot:,}</b></div><div style="background-color: #ffffff; padding: 20px; border-radius: 12px; border-left: 4px solid #38bdf8; box-shadow: 0 2px 10px rgba(0,0,0,0.05);"> TOTAL QRIS<br><b style="color:#0284c7;">Rp {tq_tot:,}</b></div><div style="background-color: #ffffff; padding: 20px; border-radius: 12px; border-left: 4px solid #7dd3fc; box-shadow: 0 2px 10px rgba(0,0,0,0.05);"> TOTAL DEBIT<br><b>Rp {td_tot:,}</b></div><div style="background: linear-gradient(135deg, #0284c7 0%, #38bdf8 100%); padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(2,132,199,0.3);"><span style="color:white; font-size:11px;"> GRAND TOTAL KESELURUHAN</span><h3 style="color:white; margin:0; font-size:24px;">Rp {gt_tot:,}</h3></div></div>', unsafe_allow_html=True)
        elif isinstance(rentang_tgl, tuple) and len(rentang_tgl) == 1:
            st.warning(" Silakan klik tanggal akhir pada kalender untuk melihat total pendapatan.")

elif choice == " Laporan Detailing":
    st.markdown("<h3 style='font-size:18px; font-weight:700;'> Laporan Pendapatan Detailing</h3>", unsafe_allow_html=True)
    tgl_pilih = st.date_input("Pilih Tanggal Untuk Siklus Detailing:", value=date.today())
    
    if tgl_pilih.day >= 11:
        start_cycle = tgl_pilih.replace(day=11)
        end_cycle = (tgl_pilih + relativedelta(months=1)).replace(day=10)
    else:
        end_cycle = tgl_pilih.replace(day=10)
        start_cycle = (end_cycle - relativedelta(months=1)).replace(day=11)
        
    st.info(f"Menampilkan data siklus detailing: {start_cycle.strftime('%d %B %Y')} s/d {end_cycle.strftime('%d %B %Y')}")
    
    s_begin = f"{start_cycle.strftime('%Y-%m-%d')} 00:00:00"
    s_end = f"{end_cycle.strftime('%Y-%m-%d')} 23:59:59"
    
    df_detailing = pd.read_sql_query("SELECT id, tanggal, nama_pelanggan, no_hp, jenis_mobil, ukuran_mobil, plat_nomor, paket_detailing, metode_bayar, nominal, pekerja, upah_pekerja, bersih FROM detailing_trx WHERE tanggal BETWEEN %s AND %s ORDER BY id DESC", conn, params=(s_begin, s_end))
    
    if not df_detailing.empty:
        cash = df_detailing[df_detailing['metode_bayar'] == 'Cash']['nominal'].sum()
        qris = df_detailing[df_detailing['metode_bayar'] == 'QRIS']['nominal'].sum()
        debit = df_detailing[df_detailing['metode_bayar'] == 'Debit']['nominal'].sum()
        total_upah = df_detailing['upah_pekerja'].sum()
        total_bersih = df_detailing['bersih'].sum()
        
        st.markdown(f'''
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; margin-bottom: 25px;">
            <div style="background:#fff; padding:15px; border-radius:10px; border-left:4px solid #64748b;">CASH<br><b>Rp {cash:,}</b></div>
            <div style="background:#fff; padding:15px; border-radius:10px; border-left:4px solid #38bdf8;">QRIS<br><b style="color:#0284c7;">Rp {qris:,}</b></div>
            <div style="background:#fff; padding:15px; border-radius:10px; border-left:4px solid #7dd3fc;">DEBIT<br><b>Rp {debit:,}</b></div>
            <div style="background:#fff; padding:15px; border-radius:10px; border-left:4px solid #f59e0b;">TOTAL UPAH PEKERJA<br><b style="color:#d97706;">Rp {total_upah:,}</b></div>
            <div style="background: linear-gradient(135deg, #10b981 0%, #34d399 100%); padding:15px; border-radius:10px;"><span style="color:white; font-size:11px;">PENDAPATAN BERSIH</span><h3 style="color:white; margin:0; font-size:20px;">Rp {total_bersih:,}</h3></div>
        </div>
        ''', unsafe_allow_html=True)
        
        df_detailing.insert(0, "Pilih", False)
        df_detailing.columns = [' Pilih', 'ID', 'Tanggal Transaksi', 'Pelanggan', 'No HP', 'Jenis Mobil', 'Ukuran', 'Plat', 'Jenis Detailing', 'Metode Bayar', 'Total Pembayaran (Rp)', 'Pekerja', 'Upah Dibagi (Rp)', 'Pendapatan Bersih (Rp)']
        
        disabled_cols_det = [c for c in df_detailing.columns if c not in [' Pilih', 'Metode Bayar']]
        
        ed_detailing = st.data_editor(
            df_detailing, 
            disabled=disabled_cols_det,
            column_config={"Metode Bayar": st.column_config.SelectboxColumn(options=["Cash", "QRIS", "Debit"])},
            use_container_width=True, 
            key="ed_detail_trx"
        )
        
        c_det1, c_det2 = st.columns([4, 1])
        with c_det1:
            if st.button(" Simpan Perubahan Metode Bayar", key="btn_simpan_det", use_container_width=True):
                for idx, row in ed_detailing.iterrows():
                    cursor.execute("UPDATE detailing_trx SET metode_bayar = %s WHERE id = %s", (row['Metode Bayar'], int(row['ID'])))
                    cursor.execute("UPDATE transactions SET metode_bayar = %s WHERE tanggal = %s AND plat_nomor = %s", (row['Metode Bayar'], row['Tanggal Transaksi'], row['Plat']))
                conn.commit(); st.success("Metode bayar Detailing berhasil diperbarui!"); st.rerun()
        with c_det2:
            ld_det = ed_detailing[ed_detailing[' Pilih'] == True]['ID'].tolist()
            if st.button("🗑️ Hapus Histori Detailing Terpilih", type="primary", use_container_width=True) and ld_det:
                for d_id in ld_det:
                    cursor.execute("SELECT tanggal, plat_nomor FROM detailing_trx WHERE id = %s", (int(d_id),))
                    del_info = cursor.fetchone()
                    if del_info:
                        tgl_del, plat_del = del_info
                        cursor.execute("DELETE FROM transactions WHERE tanggal = %s AND plat_nomor = %s", (tgl_del, plat_del))
                        cursor.execute("DELETE FROM employee_bonuses WHERE tanggal = %s", (tgl_del,))
                    cursor.execute("DELETE FROM detailing_trx WHERE id = %s", (int(d_id),))
                conn.commit()
                st.success("Transaksi detailing dihapus. Upah pencuci di laporan umum serta bonus karyawan terkait juga berhasil dibersihkan otomatis!")
                st.rerun()
    else:
        st.warning("Belum ada transaksi detailing pada siklus ini.")

elif choice == " Laundry Karpet":
    st.markdown("<h3 style='font-size:18px; font-weight:700;'> Modul Laundry Karpet</h3>", unsafe_allow_html=True)
    t_input, t_monitor, t_pembayaran, t_history = st.tabs([" 1. PENERIMAAN BARU", " 2. MONITOR ANTREAN", " 3. PEMBAYARAN", " 4. HISTORI"])
    
    with t_input:
        pk = st.text_input("Pencarian Pintar Akun Pelanggan (opsional):").strip()
        
        if pk and "lk_search_temp" not in st.session_state:
            hc = cari_pelanggan_pintar(pk)
            if hc:
                st.session_state["lk_nama_auto"] = hc[0][1]
                st.session_state["lk_hp_auto"] = hc[0][2]
                st.session_state["lk_oid_auto"] = hc[0][0]
                st.session_state["lk_search_temp"] = pk
                st.success(f" Terhubung secara otomatis: {hc[0][1]} ({hc[0][2]})")
        elif not pk and "lk_search_temp" in st.session_state:
            del st.session_state["lk_search_temp"]
            st.session_state["lk_nama_auto"] = ""
            st.session_state["lk_hp_auto"] = ""
            st.session_state["lk_oid_auto"] = None
            
        def_n = st.session_state.get("lk_nama_auto", "")
        def_h = st.session_state.get("lk_hp_auto", "")
        oid = st.session_state.get("lk_oid_auto", None)
        
        col_ka1, col_ka2 = st.columns(2)
        with col_ka1: 
            n_k = st.text_input("Nama Pelanggan / Mushola:", value=def_n)
            h_k = st.text_input("No HP / WhatsApp:", value=def_h)
        with col_ka2: 
            tm = st.date_input("Tanggal Masuk:", value=date.today(), key="lk_tm")
            tj = st.date_input("Estimasi Selesai:", value=date.today() + timedelta(days=3), key="lk_tj")
            
        jp = st.number_input("Jumlah Unit Karpet (Pcs):", min_value=1, value=1, step=1, key="lk_jp")
        
        st.markdown(f"**Masukkan Spesifikasi {jp} Karpet (Opsional):**")
        ldk_list = []
        for i in range(int(jp)):
            ldk_list.append(st.text_input(f"Spesifikasi Karpet Ke-{i+1}:", key=f"lk_spek_{i}"))
            
        if st.button(" Masukkan Daftar Antrean", type="primary", use_container_width=True):
            if n_k and h_k:
                karpet_text = "\n".join([f"{idx+1}. {tx}" for idx, tx in enumerate(ldk_list) if tx.strip()])
                if not karpet_text: karpet_text = "Karpet Custom"
                
                cursor.execute("INSERT INTO laundry_karpet (owner_id, nama_pelanggan, no_hp, warna_karpet, jumlah_pcs, tgl_masuk, tgl_jadi, harga, status, metode_bayar, is_archived) VALUES (%s, %s, %s, %s, %s, %s, %s, 0, 'Proses', 'Cash', 0)", (oid, n_k, h_k, karpet_text, int(jp), str(tm), str(tj)))
                conn.commit()
                
                for key in list(st.session_state.keys()):
                    if key.startswith("lk_"): del st.session_state[key]
                st.rerun()
            else:
                st.error("Nama dan No HP wajib diisi!")

    with t_monitor:
        df_k_list = pd.read_sql_query("SELECT id, nama_pelanggan, no_hp, warna_karpet, jumlah_pcs, tgl_masuk, tgl_jadi, harga, status FROM laundry_karpet WHERE is_archived = 0 ORDER BY tgl_masuk DESC, id DESC", conn)
        if not df_k_list.empty:
            df_k_list.insert(0, "☑️ Info WA (Selesai)", False)
            df_k_list.insert(0, "Pilih", False)
            df_k_list.columns = [' Pilih', '☑️ Info WA (Selesai)', 'ID Order', 'Pelanggan', 'No HP', 'Spesifikasi Karpet', 'Pcs', 'Tgl Masuk', 'Estimasi Jadi', 'Total Biaya (Rp)', 'Status']
            
            ed_karpet = st.data_editor(df_k_list, disabled=['ID Order', 'Spesifikasi Karpet', 'Pcs', 'Tgl Masuk', 'Status'], column_config={
                "Status": st.column_config.SelectboxColumn(options=["Proses", "Selesai (Info WA)", "Selesai & Lunas"])
            }, use_container_width=True, key="karpet_monitor_v17")
            
            c_ac1, c_ac2 = st.columns([4, 1])
            with c_ac1:
                if st.button(" Update Status & Harga", use_container_width=True):
                    for idx, row in ed_karpet.iterrows():
                        id_ord, h_baru = int(row['Total Biaya (Rp)'])
                        st_baru = row['Status']
                        
                        if row['☑️ Info WA (Selesai)'] and st_baru == "Proses":
                            st_baru = "Selesai (Info WA)"
                            
                        cursor.execute("UPDATE laundry_karpet SET nama_pelanggan=%s, no_hp=%s, tgl_jadi=%s, harga=%s, status=%s WHERE id=%s", (row['Pelanggan'], row['No HP'], row['Estimasi Jadi'], h_baru, st_baru, id_ord))

                    conn.commit(); st.success(" Data Terupdate!"); st.rerun()
            with c_ac2:
                ldc = ed_karpet[ed_karpet[' Pilih'] == True]['ID Order'].tolist()
                if st.button(f" Arsipkan", type="primary", use_container_width=True) and ldc:
                    for target_id in ldc: cursor.execute("UPDATE laundry_karpet SET is_archived = 1 WHERE id = %s", (int(target_id),))
                    conn.commit(); st.success(" Diarsipkan!"); st.rerun()

            st.markdown("---")
            st.markdown("#### 📲 Hubungi Pelanggan (Info Karpet Selesai)")
            ada_wa = False
            for idx, row in ed_karpet.iterrows():
                if row['Status'] == "Selesai (Info WA)":
                    ada_wa = True
                    pesan = (
                        f"Halo kak {row['Pelanggan']},\n\n"
                        f"Laundry karpetnya sudah selesai dan siap diambil di {NAMA_BISNIS} ya!\n\n"
                        f"*Detail Laundry Karpet:*\n"
                        f"- Jumlah: {row['Pcs']} Pcs\n"
                        f"- Jenis/Spesifikasi: {row['Spesifikasi Karpet']}\n"
                        f"- Total Biaya: *Rp {int(row['Total Biaya (Rp)']):,}*\n\n"
                        f"Silakan datang ke lokasi untuk pengambilan. Terima kasih!"
                    )
                    no_hp_wa = str(row['No HP'])
                    if no_hp_wa.startswith("0"): no_hp_wa = "62" + no_hp_wa[1:]
                    wa_link = f"https://api.whatsapp.com/send?phone={no_hp_wa}&text={urllib.parse.quote(pesan)}"
                    
                    st.link_button(f"💬 Kirim Info Pengambilan ke {row['Pelanggan']}", wa_link)
                    
            if not ada_wa:
                st.info("Centang kolom '☑️ Info WA (Selesai)' pada tabel di atas dan pastikan biayanya sudah diisi, lalu klik 'Update Status & Harga'. Tombol WhatsApp akan muncul di sini.")

    with t_pembayaran:
        st.markdown("#### Kasir Pembayaran Laundry Karpet")
        cursor.execute("SELECT id, nama_pelanggan, no_hp, warna_karpet, jumlah_pcs, harga FROM laundry_karpet WHERE status = 'Selesai (Info WA)' AND is_archived = 0")
        list_siap_bayar = cursor.fetchall()
        
        if not list_siap_bayar:
            st.info(" Belum ada antrean karpet yang siap dibayar (Pastikan status di Monitor Antrean sudah 'Selesai (Info WA)').")
        else:
            opsi_bayar = {f"[{r[0]}] {r[1]} - Rp {r[5]:,}": r for r in list_siap_bayar}
            pilih_bayar = st.selectbox("Pilih Pelanggan & Pesanan:", list(opsi_bayar.keys()))
            
            data_terpilih = opsi_bayar[pilih_bayar]
            id_bayar, nama_bayar, hp_bayar, spek_bayar, pcs_bayar, harga_bayar = data_terpilih
            
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                st.text_input("Nama Pelanggan:", value=nama_bayar, disabled=True)
                metode_pembayaran_karpet = st.selectbox("Metode Pembayaran:", ["Cash", "QRIS", "Debit"], key="metode_karpet")
            with col_b2:
                st.number_input("Total Tagihan (Rp):", value=int(harga_bayar), disabled=True)
                
            if st.button(" Konfirmasi Pembayaran & Lunas", type="primary", use_container_width=True):
                waktu_sekarang = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                waktu_tgl_saja = datetime.now().strftime("%Y-%m-%d") 
                
                cursor.execute("UPDATE laundry_karpet SET status = 'Selesai & Lunas', metode_bayar = %s, tgl_jadi = %s WHERE id = %s", (metode_pembayaran_karpet, waktu_tgl_saja, id_bayar))
                cursor.execute("INSERT INTO transactions (tanggal, nama_pelanggan, jenis_mobil, ukuran_mobil, plat_nomor, paket_layanan, tambahan_layanan, metode_bayar, nominal, kategori_kendaraan, harga_paket_real, harga_tambahan_real) VALUES (%s, %s, 'Laundry Karpet', 'Karpet', '-', 'Laundry Karpet', %s, %s, %s, 'Karpet', %s, 0)", (waktu_sekarang, nama_bayar, f"Isi: {spek_bayar}", metode_pembayaran_karpet, harga_bayar, harga_bayar))
                
                if harga_bayar > 0:
                    bonus_total_karpet = harga_bayar * 0.35
                    bonus_per_orang = int(bonus_total_karpet / 2)
                    for nama_panggilan in ["ibnu", "raden"]:
                        kry_full = map_nama_karyawan(nama_panggilan)
                        cursor.execute("INSERT INTO employee_bonuses (tanggal, nama_karyawan, jenis_bonus, nominal_bonus) VALUES (%s, %s, %s, %s)", (waktu_sekarang, kry_full, "Uang Karpet", bonus_per_orang))

                conn.commit()
                st.success(" Pembayaran Berhasil! Pendapatan & Bonus otomatis tercatat.")
                st.rerun()

        st.markdown("---")
        st.markdown("#### 🧾 Kirim Nota Pembayaran Lunas via WhatsApp")
        cursor.execute("SELECT id, nama_pelanggan, no_hp, warna_karpet, jumlah_pcs, harga, metode_bayar FROM laundry_karpet WHERE status = 'Selesai & Lunas' AND is_archived = 0 ORDER BY tgl_masuk DESC, id DESC LIMIT 5")
        list_lunas = cursor.fetchall()
        
        if not list_lunas:
            st.info("Belum ada transaksi karpet lunas terbaru.")
        else:
            for r_lunas in list_lunas:
                pesan_lunas = (
                    f"*NOTA PEMBAYARAN LAUNDRY KARPET - {NAMA_BISNIS}*\n-----------------------------------------\n"
                    f"Terima kasih telah mempercayakan laundry karpet Anda kepada kami.\n\n"
                    f"*Detail Pelanggan:*\nNama: {r_lunas[1]}\n\n"
                    f"*Rincian Layanan & Tarif:*\n- Jumlah: {r_lunas[4]} Pcs\n- Spesifikasi: {r_lunas[3]}\n"
                    f"-----------------------------------------\n*TOTAL PEMBAYARAN:* Rp {int(r_lunas[5]):,}\n-----------------------------------------\n"
                    f"Metode Bayar: {r_lunas[6]}\nStatus: *LUNAS*\n-----------------------------------------\n"
                    f" _{ALAMAT_BISNIS}_\n"
                )
                no_hp_lunas = str(r_lunas[2])
                if no_hp_lunas.startswith("0"): no_hp_lunas = "62" + no_hp_lunas[1:]
                wa_link_lunas = f"https://api.whatsapp.com/send?phone={no_hp_lunas}&text={urllib.parse.quote(pesan_lunas)}"
                
                st.link_button(f"🧾 Kirim Nota Lunas ke {r_lunas[1]} (Rp {int(r_lunas[5]):,})", wa_link_lunas)

    with t_history:
        df_all_karpet = pd.read_sql_query("SELECT id, nama_pelanggan, no_hp, warna_karpet, jumlah_pcs, tgl_masuk, tgl_jadi, harga, status, metode_bayar FROM laundry_karpet ORDER BY tgl_masuk DESC, id DESC", conn)
        if not df_all_karpet.empty:
            df_all_karpet.insert(0, "Pilih", False)
            df_all_karpet.columns = [' Pilih', 'ID Order', 'Pelanggan', 'No HP', 'Rincian', 'Pcs', 'Tgl Masuk', 'Tgl Jadi', 'Biaya (Rp)', 'Status', 'Metode']
            
            disabled_cols_hk = [c for c in df_all_karpet.columns if c not in [' Pilih', 'Metode']]
            
            ed_h_k = st.data_editor(
                df_all_karpet, 
                disabled=disabled_cols_hk,
                column_config={"Metode": st.column_config.SelectboxColumn(options=["Cash", "QRIS", "Debit"])},
                use_container_width=True, 
                key="ed_hk_v5"
            )
            
            c_hk1, c_hk2 = st.columns([4, 1])
            with c_hk1:
                if st.button(" Simpan Perubahan Metode Bayar", key="btn_simpan_hk", use_container_width=True):
                    for idx, row in ed_h_k.iterrows():
                        cursor.execute("UPDATE laundry_karpet SET metode_bayar = %s WHERE id = %s", (row['Metode'], int(row['ID Order'])))
                        cursor.execute("UPDATE transactions SET metode_bayar = %s WHERE nama_pelanggan = %s AND kategori_kendaraan = 'Karpet' AND nominal = %s", (row['Metode'], row['Pelanggan'], row['Biaya (Rp)']))
                    conn.commit(); st.success("Metode bayar Laundry Karpet berhasil diperbarui!"); st.rerun()
            with c_hk2:
                l_del = ed_h_k[ed_h_k[' Pilih'] == True]['ID Order'].tolist()
                if st.button(f" Hapus Histori Terpilih", type="primary", use_container_width=True) and l_del:
                    for target_id in l_del: cursor.execute("DELETE FROM laundry_karpet WHERE id = %s", (int(target_id),))
                    conn.commit(); st.success(" Log dihapus!"); st.rerun()

elif choice == " Bonus Karyawan":
    st.markdown("<h3 style='font-size:18px; font-weight:700;'> Rekapitulasi Bonus Karyawan</h3>", unsafe_allow_html=True)
    pilihan_tanggal = st.date_input(" Filter Tanggal:", value=date.today())
    string_awal = f"{(pilihan_tanggal - timedelta(days=(pilihan_tanggal.weekday() + 1) % 7)).strftime('%Y-%m-%d')} 00:00:00"
    string_akhir = f"{(pilihan_tanggal - timedelta(days=(pilihan_tanggal.weekday() + 1) % 7) + timedelta(days=6)).strftime('%Y-%m-%d')} 23:59:59"
    
    df_bonus_total = pd.read_sql_query("SELECT nama_karyawan, SUM(nominal_bonus) as total FROM employee_bonuses WHERE tanggal BETWEEN %s AND %s GROUP BY nama_karyawan ORDER BY total DESC", conn, params=(string_awal, string_akhir))
    if not df_bonus_total.empty:
        df_bonus_total.columns = ['Nama Karyawan', 'Total Gaji Bonus Pekan Ini (Rp)']
        st.dataframe(df_bonus_total, use_container_width=True)
    else: st.warning(" Tidak ada data bonus pekan ini.")
        
    st.markdown("---")
    with st.form("form_tambah_bonus", clear_on_submit=True):
        col_b1, col_b2, col_b3 = st.columns(3)
        with col_b1: in_nama_kry = st.text_input("Nama Karyawan:").strip()
        with col_b2: in_jns_bn = st.text_input("Keterangan Bonus:").strip()
        with col_b3: in_nom_bn = st.number_input("Nominal Bonus (Rp):", min_value=0, step=1000)
        if st.form_submit_button(" Simpan Log Bonus") and in_nama_kry and in_nom_bn > 0:
            kry_full = map_nama_karyawan(in_nama_kry)
            in_nom_bn_bulat = int(in_nom_bn)
            cursor.execute("INSERT INTO employee_bonuses (tanggal, nama_karyawan, jenis_bonus, nominal_bonus) VALUES (%s, %s, %s, %s)", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), kry_full, in_jns_bn, in_nom_bn_bulat))
            conn.commit(); st.success(" Berhasil dicatat!"); st.rerun()

    df_log_all = pd.read_sql_query("SELECT id, tanggal, nama_karyawan, jenis_bonus, nominal_bonus FROM employee_bonuses ORDER BY id DESC", conn)
    if not df_log_all.empty:
        df_log_all.insert(0, "Pilih", False)
        df_log_all.columns = [' Pilih', 'ID Log', 'Tanggal Jam', 'Nama Karyawan', 'Deskripsi', 'Nominal Bonus (Rp)']
        edited_log_bonus = st.data_editor(df_log_all, disabled=list(df_log_all.columns[1:]), use_container_width=True, key="ed_log_bonus_v3")
        lb = edited_log_bonus[edited_log_bonus[' Pilih'] == True]['ID Log'].tolist()
        if st.button(f" Hapus Log Terpilih", type="primary") and lb:
            for target_id in lb: cursor.execute("DELETE FROM employee_bonuses WHERE id = %s", (int(target_id),))
            conn.commit(); st.success(" Log bonus dibersihkan!"); st.rerun()

elif choice == " Data Karyawan (Master)":
    st.markdown("<h3 style='font-size:18px; font-weight:700;'> Data Master Karyawan (Arsip Permanen)</h3>", unsafe_allow_html=True)
    with st.expander("➕ Tambah Karyawan Baru", expanded=False):
        with st.form("form_tambah_karyawan_baru", clear_on_submit=True):
            col_add_1, col_add_2 = st.columns(2)
            with col_add_1:
                add_nama = st.text_input("Nama Lengkap Karyawan:", key="add_nm")
                add_jabatan = st.text_input("Jabatan:", key="add_jb")
                add_no_hp = st.text_input("Nomor HP:", key="add_hp")
                add_nik = st.text_input("NIK:", key="add_nk")
            with col_add_2:
                add_g_mingguan = st.number_input("Gaji Mingguan (Rp):", step=10000, key="add_g_ming")
                add_g_bulanan = st.number_input("Gaji Pokok Bulanan (Rp):", step=50000, key="add_g_bul")
                add_tgl_lahir = st.date_input("Pilih Tanggal Lahir:", value=date(1995, 1, 1), min_value=date(1950, 1, 1), max_value=date.today(), key="add_tl")
                add_tgl_masuk = st.date_input("Tanggal Masuk Kerja:", value=date.today(), min_value=date(2010, 1, 1), key="add_tm")
            
            add_alamat = st.text_area("Alamat Tinggal:", height=65, key="add_al")
            
            if st.form_submit_button("➕ Simpan Karyawan", use_container_width=True):
                if add_nama.strip(): 
                    cursor.execute("INSERT INTO master_karyawan (nama, jabatan, alamat, tgl_lahir, no_hp, nik, tgl_masuk, is_active, gaji_mingguan_master, gaji_bulanan_master) VALUES (%s, %s, %s, %s, %s, %s, %s, 1, %s, %s)", (add_nama.strip().upper(), add_jabatan.strip(), add_alamat.strip(), add_tgl_lahir.strftime("%Y-%m-%d"), str(add_no_hp), str(add_nik), add_tgl_masuk.strftime("%Y-%m-%d"), float(add_g_mingguan), float(add_g_bulanan)))
                    conn.commit(); st.success("Karyawan baru berhasil ditambahkan!"); st.rerun()

    st.markdown("---")
    cursor.execute("SELECT slot_id, nama, jabatan, alamat, tgl_lahir, no_hp, nik, tgl_masuk, gaji_mingguan_master, gaji_bulanan_master FROM master_karyawan WHERE is_active = 1 ORDER BY slot_id ASC")
    raw_karyawan = cursor.fetchall()
    if raw_karyawan:
        st.markdown("####  Edit Data Karyawan")
        slot_opsi = {f"ID {r[0]} - {r[1]}": r for r in raw_karyawan}
        pilih_slot_str = st.selectbox("Pilih Karyawan:", list(slot_opsi.keys()))
        slot_id_terpilih, s_nama, s_jabatan, s_alamat, s_tgl_lahir, s_no_hp, s_nik, s_tgl_masuk, s_g_minggu, s_g_bulan = slot_opsi[pilih_slot_str]
        
        try: def_lahir = datetime.strptime(s_tgl_lahir, "%Y-%m-%d").date() if s_tgl_lahir else date(1995, 1, 1)
        except: def_lahir = date(1995, 1, 1)
        try: def_masuk = datetime.strptime(s_tgl_masuk, "%Y-%m-%d").date() if s_tgl_masuk else date.today()
        except: def_masuk = date.today()
        
        with st.form("form_edit_master_karyawan"):
            col_ka_1, col_ka_2 = st.columns(2)
            with col_ka_1:
                in_nama = st.text_input("Nama Lengkap Karyawan:", value=s_nama)
                in_jabatan = st.text_input("Jabatan:", value=s_jabatan)
                in_no_hp = st.text_input("Nomor HP:", value=s_no_hp)
                in_nik = st.text_input("NIK:", value=s_nik)
            with col_ka_2:
                in_g_minggu = st.number_input("Gaji Mingguan (Rp):", value=int(s_g_minggu) if s_g_minggu else 0, step=10000)
                in_g_bulan = st.number_input("Gaji Pokok Bulanan (Rp):", value=int(s_g_bulan) if s_g_bulan else 0, step=50000)
                in_tgl_lahir = st.date_input("Pilih Tanggal Lahir:", value=def_lahir)
                in_tgl_masuk = st.date_input("Tanggal Masuk Kerja:", value=def_masuk)
            
            in_alamat = st.text_area("Alamat Tinggal:", value=s_alamat, height=65)
                
            if st.form_submit_button("💾 Perbarui Data Karyawan", use_container_width=True):
                cursor.execute("UPDATE master_karyawan SET nama = %s, jabatan = %s, alamat = %s, tgl_lahir = %s, no_hp = %s, nik = %s, tgl_masuk = %s, gaji_mingguan_master = %s, gaji_bulanan_master = %s WHERE slot_id = %s", (in_nama.strip().upper(), in_jabatan.strip(), in_alamat.strip(), in_tgl_lahir.strftime("%Y-%m-%d"), str(in_no_hp), str(in_nik), in_tgl_masuk.strftime("%Y-%m-%d"), float(in_g_minggu), float(in_g_bulan), slot_id_terpilih))
                conn.commit(); st.success("Perubahan data berhasil disimpan!"); st.rerun()

    processed_karyawan = []
    for row in raw_karyawan:
        u_calc, m_calc = hitung_usia_dan_masa_kerja(row[4], row[7])
        processed_karyawan.append({
            "Pilih": False, "ID": row[0], "Nama Lengkap": row[1], "Jabatan": row[2], 
            "Gaji Mingguan": f"Rp {int(row[8]):,}" if row[8] else "Rp 0", 
            "Gaji Bulanan": f"Rp {int(row[9]):,}" if row[9] else "Rp 0",
            "No HP": row[5], "Masa Kerja": m_calc
        })
    
    if processed_karyawan:
        df_karyawan_all = pd.DataFrame(processed_karyawan)
        edited_k_table = st.data_editor(df_karyawan_all, disabled=list(df_karyawan_all.columns[1:]), use_container_width=True)
        list_del_k = edited_k_table[edited_k_table['Pilih'] == True]['ID'].tolist()
        if st.button("🗑️ Hapus Karyawan Terpilih", type="primary") and list_del_k:
            for target_k_id in list_del_k: cursor.execute("UPDATE master_karyawan SET is_active = 0 WHERE slot_id = %s", (int(target_k_id),))
            conn.commit(); st.success("Dinonaktifkan!"); st.rerun()

elif choice == " Kasbon Karyawan":
    st.markdown("<h3 style='font-size:18px; font-weight:700;'> Menu Pencatatan Kasbon Karyawan</h3>", unsafe_allow_html=True)
    cursor.execute("SELECT slot_id, nama FROM master_karyawan WHERE nama != '' AND is_active = 1")
    list_active_karyawan = cursor.fetchall()
    if not list_active_karyawan: st.warning(" Silakan isi nama karyawan terlebih dahulu di menu Master.")
    else:
        with st.form("form_add_kasbon", clear_on_submit=True):
            col_ks1, col_ks2, col_ks3, col_ks4 = st.columns([2, 1, 1.5, 1.5])
            with col_ks1:
                opsi_ks_nama = {f"{k[1]}": k[0] for k in list_active_karyawan}
                pilih_kry_bon = st.selectbox("Pilih Karyawan:", list(opsi_ks_nama.keys()))
            with col_ks2: tgl_bon_input = st.date_input("Tanggal Bon:")
            with col_ks3: jumlah_bon_input = st.number_input("Jumlah Bon (Rp):", min_value=0, step=5000)
            with col_ks4: potong_dari_opsi = st.selectbox("Dipotong Dari Gaji:", ["Mingguan", "Bulanan"])
            if st.form_submit_button("Simpan Data Kasbon") and jumlah_bon_input > 0:
                jam_sekarang = datetime.now().strftime(" %H:%M:%S")
                tanggal_bon_full = tgl_bon_input.strftime("%Y-%m-%d") + jam_sekarang
                cursor.execute("INSERT INTO kasbon_karyawan (slot_id, jumlah_bon, jenis_potongan, tanggal) VALUES (%s, %s, %s, %s)", (opsi_ks_nama[pilih_kry_bon], int(jumlah_bon_input), potong_dari_opsi, tanggal_bon_full))
                conn.commit(); st.success("Kasbon berhasil disimpan!"); st.rerun()
                
        st.markdown("---")
        st.markdown("#### Histori Kasbon Karyawan")
        col_kb1, col_kb2 = st.columns(2)
        with col_kb1: tgl_kb_awal = st.date_input("Filter Dari Tanggal:", value=date.today() - timedelta(days=30))
        with col_kb2: tgl_kb_akhir = st.date_input("Sampai Tanggal:", value=date.today())
        
        tgl_kb_awal_str = f"{tgl_kb_awal.strftime('%Y-%m-%d')} 00:00:00"
        tgl_kb_akhir_str = f"{tgl_kb_akhir.strftime('%Y-%m-%d')} 23:59:59"
        
        df_log_bon = pd.read_sql_query("SELECT kk.id, kk.tanggal, mk.nama, kk.jumlah_bon, kk.jenis_potongan FROM kasbon_karyawan kk JOIN master_karyawan mk ON kk.slot_id = mk.slot_id WHERE kk.tanggal BETWEEN %s AND %s ORDER BY kk.id DESC", conn, params=(tgl_kb_awal_str, tgl_kb_akhir_str))
        if not df_log_bon.empty:
            df_log_bon['tanggal_format'] = pd.to_datetime(df_log_bon['tanggal']).dt.strftime('%A, %d-%m-%Y %H:%M')
            df_log_bon = df_log_bon[['id', 'tanggal', 'tanggal_format', 'nama', 'jumlah_bon', 'jenis_potongan']]
            df_log_bon.insert(0, "Pilih", False)
            df_log_bon.columns = [" Pilih", "ID Bon", "Tgl Original", "Hari & Tanggal Kasbon", "Nama Karyawan", "Jumlah Bon (Rp)", "Potongan Gaji"]
            
            edited_log_bon = st.data_editor(df_log_bon, disabled=["ID Bon", "Tgl Original", "Hari & Tanggal Kasbon", "Nama Karyawan"], column_config={"Potongan Gaji": st.column_config.SelectboxColumn(options=["Mingguan", "Bulanan"])}, use_container_width=True, key="ed_log_bon_v8")
            
            c_bon1, c_bon2 = st.columns([4, 1])
            with c_bon1:
                if st.button(" Simpan Perubahan", use_container_width=True):
                    for idx, row in edited_log_bon.iterrows(): cursor.execute("UPDATE kasbon_karyawan SET jumlah_bon = %s, jenis_potongan = %s, tanggal = %s WHERE id = %s", (int(row["Jumlah Bon (Rp)"]), row["Potongan Gaji"], row["Tgl Original"], int(row["ID Bon"])))
                    conn.commit(); st.success("Berhasil Diperbarui!"); st.rerun()
            with c_bon2:
                l_bon_del = edited_log_bon[edited_log_bon[" Pilih"] == True]["ID Bon"].tolist()
                if st.button("Hapus Log", type="primary", use_container_width=True) and l_bon_del:
                    for target_id in l_bon_del: cursor.execute("DELETE FROM kasbon_karyawan WHERE id = %s", (int(target_id),))
                    conn.commit(); st.success("Dihapus!"); st.rerun()

elif choice == " Absensi Karyawan":
    st.markdown("<h3 style='font-size:18px; font-weight:700;'> Absensi Karyawan (Siklus Mingguan)</h3>", unsafe_allow_html=True)
    selected_date = st.date_input("Pilih Tanggal Untuk Menentukan Minggu (Minggu - Sabtu):", value=date.today())
    start_of_week = selected_date - timedelta(days=selected_date.isoweekday() % 7)
    
    st.info(f"Mengedit jadwal: {start_of_week.strftime('%d %b %Y')} (Minggu) s/d {(start_of_week + timedelta(days=6)).strftime('%d %b %Y')} (Sabtu). Silakan tentukan status Masuk / Setengah Hari / Izin / Libur.")
    
    TIME_OPTIONS = [f"{str(h).zfill(2)}:{str(m).zfill(2)}" for h in range(0, 24) for m in (0, 30)]
    
    cursor.execute("SELECT slot_id, nama FROM master_karyawan WHERE is_active = 1")
    karyawan_list = cursor.fetchall()
    
    for emp_id, emp_name in karyawan_list:
        is_melisa = "melisa" in emp_name.lower()
        is_diva = "diva" in emp_name.lower()
        is_ribut = "ribut" in emp_name.lower()
        is_raden = "raden" in emp_name.lower()
        is_ibnu = "ibnu" in emp_name.lower()
        is_hendry = "hendry" in emp_name.lower() or "hendri" in emp_name.lower()
        
        with st.expander(f"👤 JADWAL: {emp_name}"):
            for i in range(7):
                cur_date = start_of_week + timedelta(days=i)
                cur_date_str = cur_date.strftime('%Y-%m-%d')
                nama_hari = ["Minggu", "Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu"][i]
                hari_idx = cur_date.weekday()
                
                def_stat = 'Masuk'
                def_in, def_out = '08:00', '22:00'
                def_makan = 0
                
                if is_ribut: def_out = '19:00'
                elif is_melisa:
                    if hari_idx == 1: def_in, def_out = '08:00', '22:00'
                    elif hari_idx == 3: def_stat, def_in, def_out = 'Libur', '00:00', '00:00'
                    else: def_in, def_out = '08:00', '16:00'
                elif is_diva:
                    if hari_idx == 3: def_in, def_out = '08:00', '22:00'
                    elif hari_idx == 1: def_stat, def_in, def_out = 'Libur', '00:00', '00:00'
                    else: def_in, def_out = '16:00', '22:00'
                    
                if is_raden or is_hendry: def_makan = 15000
                elif is_ibnu: def_makan = 30000
                
                cursor.execute("SELECT status, jam_masuk, jam_keluar, alasan_izin, uang_makan FROM absensi_karyawan WHERE slot_id=%s AND tanggal=%s", (emp_id, cur_date_str))
                row = cursor.fetchone()
                
                status_db = row[0] if row else def_stat
                j_in = row[1] if row else def_in
                j_out = row[2] if row else def_out
                alasan = row[3] if row and len(row)>3 else ''
                u_makan = int(row[4]) if row and len(row)>4 and row[4] is not None else def_makan
                
                idx_in = TIME_OPTIONS.index(j_in) if j_in in TIME_OPTIONS else TIME_OPTIONS.index(def_in)
                idx_out = TIME_OPTIONS.index(j_out) if j_out in TIME_OPTIONS else TIME_OPTIONS.index(def_out)
                
                st.write(f"**{nama_hari}, {cur_date.strftime('%d/%m/%Y')}**")
                c1, c2, c3, c4, c5 = st.columns([1.5, 2, 2, 2, 3])
                
                with c1:
                    is_libur = st.checkbox("☑️ Libur", value=(status_db == 'Libur'), key=f"cbx_libur_{emp_id}_{i}")
                    
                    if is_libur:
                        curr_stat = "Libur"
                    else:
                        def_idx = 0 if status_db in ["Masuk", "Libur", "Belum Waktunya"] else (1 if status_db == "Setengah Hari" else 2)
                        curr_stat = st.selectbox("Status", ["Masuk", "Setengah Hari", "Izin"], index=def_idx, key=f"st_{emp_id}_{i}", label_visibility="collapsed")
                
                if curr_stat == 'Libur':
                    with c2: st.markdown("<div style='margin-top:10px; font-weight:bold; color:#ef4444;'>LIBUR OFF</div>", unsafe_allow_html=True)
                    with c3: st.empty()
                    new_in, new_out = "00:00", "00:00"
                    with c4: new_makan = st.number_input("Uang Makan", value=0, step=5000, key=f"mkn_{emp_id}_{i}", disabled=True, label_visibility="collapsed")
                    with c5: new_alasan = st.text_input("Alasan", value="", key=f"al_{emp_id}_{i}", disabled=True, label_visibility="collapsed")
                else:
                    with c2: new_in = st.selectbox("Jam Masuk", TIME_OPTIONS, index=idx_in, key=f"in_{emp_id}_{i}", label_visibility="collapsed")
                    with c3: new_out = st.selectbox("Jam Keluar", TIME_OPTIONS, index=idx_out, key=f"out_{emp_id}_{i}", label_visibility="collapsed")
                    with c4: new_makan = st.number_input("Uang Makan", value=u_makan, step=5000, key=f"mkn_{emp_id}_{i}", label_visibility="collapsed")
                    with c5: new_alasan = st.text_input("Alasan Izin/Lain", value=alasan, key=f"al_{emp_id}_{i}", label_visibility="collapsed", placeholder="Ketik alasan")
                
                st.session_state[f"temp_abs_save_{emp_id}_{i}"] = (cur_date_str, curr_stat, new_in, new_out, new_alasan, new_makan)
                st.markdown("---")
            
            if st.button(f"💾 Simpan Absensi {emp_name}", type="primary", use_container_width=True):
                for j in range(7):
                    t_tgl, t_stat, t_in, t_out, t_alasan, t_makan = st.session_state[f"temp_abs_save_{emp_id}_{j}"]
                    
                    if any(x in emp_name.lower() for x in ["raden", "hendry", "hendri"]):
                        t_makan = 15000 if t_stat == "Masuk" else (7500 if t_stat == "Setengah Hari" else 0)
                    elif "ibnu" in emp_name.lower():
                        t_makan = 30000 if t_stat == "Masuk" else (15000 if t_stat == "Setengah Hari" else 0)
                    
                    if t_stat in ["Libur", "Izin"]:
                        t_makan = 0
                        
                    cursor.execute("SELECT id FROM absensi_karyawan WHERE slot_id=%s AND tanggal=%s", (emp_id, t_tgl))
                    ada = cursor.fetchone()
                    if ada: cursor.execute("UPDATE absensi_karyawan SET status=%s, jam_masuk=%s, jam_keluar=%s, alasan_izin=%s, uang_makan=%s WHERE id=%s", (t_stat, t_in, t_out, t_alasan, t_makan, ada[0]))
                    else: cursor.execute("INSERT INTO absensi_karyawan (slot_id, tanggal, jam_masuk, jam_keluar, status, alasan_izin, uang_makan) VALUES (%s,%s,%s,%s,%s,%s,%s)", (emp_id, t_tgl, t_in, t_out, t_stat, t_alasan, t_makan))
                conn.commit(); st.success(f"Absensi untuk {emp_name} berhasil disimpan dan Uang Makan telah disesuaikan otomatis (jika ada)!")

elif choice == " Upah Permobil":
    st.markdown("<h3 style='font-size:18px; font-weight:700;'> Dashboard Real-Time Upah Washer (Permobil)</h3>", unsafe_allow_html=True)
    st.info("Upah dikalkulasi SECARA OTOMATIS dan REAL-TIME dari transaksi POS hari yang dipilih. Menu ini HANYA untuk Ibnu, Hendry & Raden.")
    
    tgl_upah = st.date_input("Cek / Ubah Pembagi Pada Tanggal:", value=date.today())
    tgl_str = tgl_upah.strftime('%Y-%m-%d')
    
    cursor.execute("SELECT tanggal, paket_layanan, kategori_kendaraan FROM transactions WHERE tanggal LIKE %s", (f"{tgl_str}%",))
    trx_hari_ini = cursor.fetchall()
    
    auto_s_sgp, auto_s_plat, auto_s_motor = 0, 0, 0
    auto_m_sgp, auto_m_plat, auto_m_motor = 0, 0, 0
    
    for row in trx_hari_ini:
        try: jam_trx = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S").hour
        except: jam_trx = 12
        
        paket_str_lower = str(row[1]).lower()
        kat_str = str(row[2]).lower()
        is_malam = jam_trx >= 18
        
        if kat_str == "motor":
            if is_malam: auto_m_motor += 1
            else: auto_s_motor += 1
        else:
            if "platinum" in paket_str_lower:
                if is_malam: auto_m_plat += 1
                else: auto_s_plat += 1
            elif any(x in paket_str_lower for x in ["silver", "gold", "premium", "full wax", "paket 1", "paket 2", "paket 3", "paket 4", "paket 5", "paket 6", "paket 7", "paket 8", "paket 9", "coating"]):
                if is_malam: auto_m_sgp += 1
                else: auto_s_sgp += 1
                
    cursor.execute("SELECT s_orang, m_orang, koreksi_s_sgp, koreksi_s_plat, koreksi_s_motor, koreksi_m_sgp, koreksi_m_plat, koreksi_m_motor FROM upah_permobil_daily WHERE tanggal=%s", (tgl_str,))
    row_upah = cursor.fetchone()
    s_orang_val = row_upah[0] if row_upah and row_upah[0] else 6
    m_orang_val = row_upah[1] if row_upah and row_upah[1] else 6
    k_s_sgp = row_upah[2] if row_upah and row_upah[2] is not None else 0
    k_s_plat = row_upah[3] if row_upah and row_upah[3] is not None else 0
    k_s_motor = row_upah[4] if row_upah and row_upah[4] is not None else 0
    k_m_sgp = row_upah[5] if row_upah and row_upah[5] is not None else 0
    k_m_plat = row_upah[6] if row_upah and row_upah[6] is not None else 0
    k_m_motor = row_upah[7] if row_upah and row_upah[7] is not None else 0

    with st.form("form_upah_mobil"):
        st.markdown("#### Shift Siang (08:00 - 18:00)")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Auto S/G/Prem/Detailing", auto_s_sgp)
            in_k_s_sgp = st.number_input("Koreksi SGP (+/-)", value=k_s_sgp, key="in_k_s_sgp")
        with c2:
            st.metric("Auto Platinum", auto_s_plat)
            in_k_s_plat = st.number_input("Koreksi Plat (+/-)", value=k_s_plat, key="in_k_s_plat")
        with c3:
            st.metric("Auto Motor", auto_s_motor)
            in_k_s_motor = st.number_input("Koreksi Motor (+/-)", value=k_s_motor, key="in_k_s_motor")
        with c4:
            st.metric("Pekerja Tersedia", "-")
            s_orang = st.number_input("Jml Karyawan Siang", min_value=1, value=s_orang_val, key="s_orang")
        
        st.markdown("---")
        st.markdown("#### Shift Malam (18:00 - 22:00)")
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Auto S/G/Prem/Detailing", auto_m_sgp)
            in_k_m_sgp = st.number_input("Koreksi SGP (+/-)", value=k_m_sgp, key="in_k_m_sgp")
        with m2:
            st.metric("Auto Platinum", auto_m_plat)
            in_k_m_plat = st.number_input("Koreksi Plat (+/-)", value=k_m_plat, key="in_k_m_plat")
        with m3:
            st.metric("Auto Motor", auto_m_motor)
            in_k_m_motor = st.number_input("Koreksi Motor (+/-)", value=k_m_motor, key="in_k_m_motor")
        with m4:
            st.metric("Pekerja Tersedia", "-")
            m_orang = st.number_input("Jml Karyawan Malam", min_value=1, value=m_orang_val, key="m_orang")
        
        if st.form_submit_button("Simpan Pengaturan Pembagi & Koreksi", use_container_width=True):
            cursor.execute("SELECT id FROM upah_permobil_daily WHERE tanggal=%s", (tgl_str,))
            exists = cursor.fetchone()
            if exists: 
                cursor.execute("UPDATE upah_permobil_daily SET s_orang=%s, m_orang=%s, koreksi_s_sgp=%s, koreksi_s_plat=%s, koreksi_s_motor=%s, koreksi_m_sgp=%s, koreksi_m_plat=%s, koreksi_m_motor=%s WHERE id=%s", (s_orang, m_orang, in_k_s_sgp, in_k_s_plat, in_k_s_motor, in_k_m_sgp, in_k_m_plat, in_k_m_motor, exists[0]))
            else: 
                cursor.execute("INSERT INTO upah_permobil_daily (tanggal, s_orang, m_orang, koreksi_s_sgp, koreksi_s_plat, koreksi_s_motor, koreksi_m_sgp, koreksi_m_plat, koreksi_m_motor) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", (tgl_str, s_orang, m_orang, in_k_s_sgp, in_k_s_plat, in_k_s_motor, in_k_m_sgp, in_k_m_plat, in_k_m_motor))
            conn.commit(); st.success("Pembagi Shift dan Koreksi tersimpan! Nominal gaji harian otomatis disesuaikan dengan nilai koreksi.")

elif choice == " Gaji Karyawan":
    st.markdown("<h3 style='font-size:18px; font-weight:700;'> Pembayaran & Perhitungan Real-Time Gaji Karyawan</h3>", unsafe_allow_html=True)
    t_gaji_harian, t_gaji_mingguan, t_gaji_bulanan = st.tabs([" GAJI HARIAN", " GAJI MINGGUAN", " GAJI POKOK BULANAN"])
    
    cursor.execute("SELECT slot_id, nama, jabatan, gaji_mingguan_master, gaji_bulanan_master FROM master_karyawan WHERE nama != '' AND is_active = 1 ORDER BY slot_id ASC")
    all_slots_karyawan = cursor.fetchall()
    
    with t_gaji_harian:
        if not all_slots_karyawan: st.info("Belum ada data karyawan aktif.")
        else:
            tgl_harian = st.date_input("Pilih Tanggal Gaji Harian:", value=date.today())
            tgl_str = tgl_harian.strftime('%Y-%m-%d')
            
            data_harian = []
            for slot in all_slots_karyawan:
                s_id, nama_k, jabatan_k, g_mingguan, g_bulanan = slot
                g_total, status_hr, upah_dasar, bonus_hr, uang_mkn = hitung_gaji_harian(s_id, nama_k, tgl_str)
                
                if status_hr in ["Libur", "Izin", "Belum Waktunya"]:
                    upah_dasar_str = f"Rp 0 ({status_hr})"
                    g_total_str = f"Rp 0 ({status_hr})"
                else:
                    upah_dasar_str = f"Rp {int(upah_dasar):,}"
                    g_total_str = f"Rp {int(g_total):,}"

                data_harian.append({
                    "Nama Karyawan": nama_k,
                    "Status": status_hr,
                    "Uang Makan": f"Rp {int(uang_mkn):,}",
                    "Upah Real Harian": upah_dasar_str,
                    "Bonus Tambahan (Rp)": f"Rp {int(bonus_hr):,}",
                    "Total HARI INI": g_total_str
                })
            st.dataframe(pd.DataFrame(data_harian), use_container_width=True)

    with t_gaji_mingguan:
        if not all_slots_karyawan: st.info("Belum ada data karyawan aktif.")
        else:
            bulan_gaji = st.date_input("Cek Gaji Mingguan:", value=date.today(), key="date_ref_mingguan")
            rentang_minggu = get_weeks_of_month(bulan_gaji)
            
            opsi_minggu = [f"Minggu ke-{i+1} ({rm[0].strftime('%d %b')} - {rm[1].strftime('%d %b')})" for i, rm in enumerate(rentang_minggu)]
            pilih_minggu_idx = st.selectbox("Pilih Minggu:", range(len(opsi_minggu)), format_func=lambda x: opsi_minggu[x])
            start_w, end_w = rentang_minggu[pilih_minggu_idx]
            
            data_mingguan = []
            for slot in all_slots_karyawan:
                s_id, nama_k, jabatan_k, g_mingguan_master, g_bulanan = slot
                g_kotor_termasuk_bonus, hari_masuk, total_bonus = hitung_gaji_mingguan_akumulasi(s_id, nama_k, g_mingguan_master, start_w, end_w)
                kasbon = ambil_bon_mingguan_realtime(s_id, start_w, end_w)
                
                g_dasar_saja = g_kotor_termasuk_bonus - total_bonus
                gaji_bersih_kalkulasi = g_kotor_termasuk_bonus - kasbon
                
                data_mingguan.append({
                    "ID": s_id,
                    "Nama Karyawan": nama_k,
                    "Hari Masuk": f"{hari_masuk} Hari",
                    "Gaji Dasar (Kotor)": g_dasar_saja,
                    "Bonus Mingguan": total_bonus,
                    "Kasbon (Potongan)": kasbon,
                    "Total Gaji Bersih (Edit)": gaji_bersih_kalkulasi
                })
                
            if data_mingguan:
                df_mingguan = pd.DataFrame(data_mingguan)
                st.markdown("⚠️ **Total Gaji Bersih** otomatis dihitung dari *(Gaji + Bonus - Kasbon)*. Silakan edit kolom **Total Gaji Bersih (Edit)** untuk pembulatan/potongan manual.")
                edited_mingguan = st.data_editor(
                    df_mingguan, 
                    disabled=["ID", "Nama Karyawan", "Hari Masuk", "Gaji Dasar (Kotor)", "Bonus Mingguan", "Kasbon (Potongan)"],
                    use_container_width=True,
                    key="ed_gaji_mingguan"
                )

    with t_gaji_bulanan:
        if not all_slots_karyawan: st.info("Belum ada data karyawan aktif.")
        else:
            bulan_ref = st.date_input("Pilih Bulan Gaji Pokok:", value=date.today(), key="date_ref_bulanan")
            
            data_bulanan = []
            for slot in all_slots_karyawan:
                s_id, nama_k, jabatan_k, g_mingguan, g_bulanan_master = slot
                kasbon_bln = ambil_bon_bulanan_realtime(s_id, bulan_ref)
                
                gaji_bersih_bln = g_bulanan_master - kasbon_bln
                
                data_bulanan.append({
                    "ID": s_id,
                    "Nama Karyawan": nama_k,
                    "Gaji Pokok Master": g_bulanan_master,
                    "Kasbon Bulanan": kasbon_bln,
                    "Total Bersih Diterima (Edit)": gaji_bersih_bln
                })
                
            if data_bulanan:
                df_bulanan = pd.DataFrame(data_bulanan)
                st.markdown("⚠️ Edit kolom **Total Bersih Diterima (Edit)** untuk menyesuaikan nominal jika pembayaran tidak dilakukan secara penuh.")
                edited_bulanan = st.data_editor(
                    df_bulanan,
                    disabled=["ID", "Nama Karyawan", "Gaji Pokok Master", "Kasbon Bulanan"],
                    use_container_width=True,
                    key="ed_gaji_bulanan"
                )

elif choice == " Data Gaji Terpusat (Matriks)":
    st.markdown("<h3 style='font-size:18px; font-weight:700;'> Matriks Rekapitulasi Data Seluruh Gaji Karyawan</h3>", unsafe_allow_html=True)
    cursor.execute("SELECT slot_id, nama, jabatan, gaji_mingguan_master, gaji_bulanan_master FROM master_karyawan WHERE nama != '' AND is_active = 1 ORDER BY slot_id ASC")
    all_slots_karyawan = cursor.fetchall()
    
    if not all_slots_karyawan: st.info("Belum ada data master karyawan.")
    else:
        bulan_ref = st.date_input("Pilih Tanggal Acuan Siklus Laporan (11 - 10):", value=date.today(), key="matriks_date_ref")
        rentang_minggu = get_weeks_of_month(bulan_ref)
        state_key_bulan = bulan_ref.strftime('%Y_%m')
        
        rows_matriks = []
        for slot in all_slots_karyawan:
            s_id, nama_k, jabatan_k, g_mingguan_master, g_bulanan_master = slot
            
            w_vals = [0, 0, 0, 0, 0]
            for idx, minggu in enumerate(rentang_minggu):
                if idx < 5:
                    key_w = f"w_{minggu[0].strftime('%Y%m%d')}_{minggu[1].strftime('%Y%m%d')}"
                    
                    gaji_akumulasi, _, _ = hitung_gaji_mingguan_akumulasi(s_id, nama_k, g_mingguan_master, minggu[0], minggu[1])
                            
                    val = st.session_state.gaji_mingguan_state.get(key_w, {}).get(s_id, gaji_akumulasi)
                    w_vals[idx] = val
            
            def_bul = g_bulanan_master if g_bulanan_master else 0
            
            g_bulanan = st.session_state.gaji_bulanan_state.get(state_key_bulan, {}).get(s_id, def_bul)
            total_akumulasi = sum(w_vals) + g_bulanan
            
            rows_matriks.append({
                "ID Karyawan": s_id, "Nama Karyawan": nama_k, "Jabatan": jabatan_k if jabatan_k else "-",
                "Minggu 1 (Rp)": w_vals[0], "Minggu 2 (Rp)": w_vals[1], "Minggu 3 (Rp)": w_vals[2], 
                "Minggu 4 (Rp)": w_vals[3], "Minggu 5 (Rp)": w_vals[4],
                "Gaji Pokok Bulanan (Rp)": g_bulanan, "Grand Total Kotor (Rp)": total_akumulasi
            })
            
        df_matriks = pd.DataFrame(rows_matriks)
        
        disabled_cols = ["ID Karyawan", "Nama Karyawan", "Jabatan", "Minggu 1 (Rp)", "Minggu 2 (Rp)", "Minggu 3 (Rp)", "Minggu 4 (Rp)", "Minggu 5 (Rp)", "Grand Total Kotor (Rp)"]
        edited_matriks = st.data_editor(df_matriks, disabled=disabled_cols, use_container_width=True, key=f"matriks_terpusat_editor_{state_key_bulan}")
        
        if st.button("Simpan Perubahan Matriks Laporan", use_container_width=True):
            for _, r_m in edited_matriks.iterrows():
                k_id = r_m["ID Karyawan"]
                if state_key_bulan not in st.session_state.gaji_bulanan_state: st.session_state.gaji_bulanan_state[state_key_bulan] = {}
                st.session_state.gaji_bulanan_state[state_key_bulan][k_id] = r_m["Gaji Pokok Bulanan (Rp)"]
            st.success("Seluruh keterhubungan data matriks berhasil diperbarui!")
            st.rerun()

st.sidebar.markdown("---")
with st.sidebar.expander(" 🚨 RESET ENGINE DATABASE"):
    konfirmasi_input = st.text_input("Ketik 'HAPUS PERMANEN' untuk reset:", "")
    if konfirmasi_input == "HAPUS PERMANEN":
        if st.button("🔥 DATA DIHAPUS PERMANEN", type="primary"):
            st.error("Fitur Reset Database dimatikan demi keamanan. Gunakan Supabase SQL Editor jika perlu reset.")

            fresh_cursor = fresh_conn.cursor()
            for table in ["owners", "vehicles", "transactions", "detailing_trx", "employee_bonuses", "laundry_karpet", "master_karyawan", "kasbon_karyawan", "absensi_karyawan", "upah_permobil_daily"]:
                fresh_cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
            fresh_conn.commit(); fresh_conn.close()
            st.cache_resource.clear()
            st.sidebar.success(" Reset berhasil!")
            st.rerun()
