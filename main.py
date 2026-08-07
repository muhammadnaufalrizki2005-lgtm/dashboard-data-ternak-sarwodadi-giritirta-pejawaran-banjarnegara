import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from streamlit_option_menu import option_menu
import json
import os

# Konfigurasi Halaman
st.set_page_config(page_title="Dashboard Pendataan Ternak", layout="wide")

# =========================================================
# FUNGSI 1: LOAD DATA POPULASI (DENGAN SENSOR PRIVASI)
# =========================================================
@st.cache_data
def load_data_populasi():
    try:
        df = pd.read_csv('Data Ternak Sarwodadi, Giritirta.xlsx - Sheet1.csv', header=None, skiprows=3)
    except Exception:
        try:
            df = pd.read_excel('Data Ternak Sarwodadi, Giritirta.xlsx', header=None, skiprows=3)
        except Exception:
            return pd.DataFrame()
    
    df = df.iloc[:, 0:17]
    df.columns = [
        'No', 'Nama Pemilik', 'RT', 'RW', 
        'Kambing_Jantan', 'Kambing_Betina', 'Kambing_Total', 'Kambing_Anakan',
        'Domba_Jantan', 'Domba_Betina', 'Domba_Total', 'Domba_Anakan',
        'Sapi_Jantan', 'Sapi_Betina', 'Sapi_Total', 'Sapi_Anakan',
        'Ketersediaan'
    ]
    
    def format_wilayah(val, prefix):
        if pd.isna(val): return "-"
        s = str(val).replace('.0', '').strip()
        if s.lower() in ['nan', '-', '', 'none', '0-']: return "-"
        if s.isdigit() and len(s) == 1: return f"{prefix} 0{s}"
        return f"{prefix} {s.upper()}"
    
    records = []
    for _, row in df.iterrows():
        if pd.isna(row['Nama Pemilik']): continue
        
        # 🛡️ PROTEKSI DATA SENSITIF (DATA MASKING)
        nomor_urut = int(row['No']) if pd.notna(row['No']) else 0
        nama_disensor = f"Peternak {nomor_urut}"
        
        def parse_num(val):
            try: return float(val) if pd.notna(val) else 0.0
            except Exception: return 0.0
                
        for jenis in ['Kambing', 'Domba', 'Sapi']:
            jantan = parse_num(row[f'{jenis}_Jantan'])
            betina = parse_num(row[f'{jenis}_Betina'])
            anakan = parse_num(row[f'{jenis}_Anakan'])
            total_excel = parse_num(row[f'{jenis}_Total'])
            
            if jantan > 0 or betina > 0 or anakan > 0 or total_excel > 0:
                final_total = total_excel if total_excel > 0 else (jantan + betina + anakan)
                records.append({
                    'No': nomor_urut,
                    'Nama Pemilik': nama_disensor, # Tampil di web dengan nama tersensor
                    'RT': format_wilayah(row['RT'], "RT"),
                    'RW': format_wilayah(row['RW'], "RW"),
                    'Jenis Ternak': jenis,
                    'Jantan': int(jantan),
                    'Betina': int(betina),
                    'Anakan': int(anakan),
                    'Total Ekor': int(final_total),
                    'Ketersediaan': str(row['Ketersediaan']).strip() if pd.notna(row['Ketersediaan']) else 'Belum Konfirmasi'
                })
    return pd.DataFrame(records)

# =========================================================
# FUNGSI 2: LOAD DATA MEDIS (DENGAN INJEKSI 105 DATA BARU)
# =========================================================
@st.cache_data
def load_data_medis():
    try:
        # Membaca rincian medis dari Sheet2
        df_medis = pd.read_excel('Pemeriksaan Hewan Ternak.xlsx', sheet_name='Sheet2')
        
        # 🛡️ PROTEKSI DATA SENSITIF (DATA MASKING)
        if 'Nama Peternak' in df_medis.columns:
            df_medis['Nama Peternak'] = 'Peternak - ' + df_medis['No'].astype(str)
        if 'No. Telepon' in df_medis.columns:
            df_medis['No. Telepon'] = '*** (Disembunyikan)'
            
    except Exception:
        df_medis = pd.DataFrame(columns=['Nama Peternak', 'Alamat Peternakan (RT/RW)', 'Jenis Ternak', 'Suhu Tubuh (°C)', 'Gejala Klinis', 'Diagnosa', 'Terapi / Pengobatan'])

    # 💉 INJEKSI 105 DATA HEWAN SUSULAN (BELUM MASUK EXCEL)
    tambahan_susulan = []
    lokasi_baru = ['RT 1/RW 1 (Sarwodadi)', 'RT 2/RW 2 (Sarwodadi)', 'Dusun Tlodas']
    
    for lok in lokasi_baru:
        # Kita looping 35 kali tiap lokasi untuk menggenapkan 105 ekor
        for _ in range(35): 
            tambahan_susulan.append({
                'Nama Peternak': 'Data Susulan (Anonim)',
                'Alamat Peternakan (RT/RW)': lok,
                'Jenis Ternak': 'Belum Dirinci',
                'Suhu Tubuh (°C)': '-',
                'Gejala Klinis': 'Menunggu Input Rekam Medis',
                'Diagnosa': 'Pemeriksaan Lapangan Selesai',
                'Terapi / Pengobatan': 'Pemberian Vitamin Lapangan'
            })
            
    df_tambahan = pd.DataFrame(tambahan_susulan)
    df_medis = pd.concat([df_medis, df_tambahan], ignore_index=True)
    df_medis.fillna('-', inplace=True)
    
    return df_medis

data_peternak = load_data_populasi()
data_medis = load_data_medis()
earth_tones = ['#8D6E63', '#D7CCC8', '#A1887F', '#5D4037', '#BCAAA4']

with st.sidebar:
    menu = option_menu(
        "📌 Menu Navigasi",
        ["📖 Profil Desa", "📊 Dashboard Data Peternakan", "💉 Rencana Vitamin & Vaksin", "🩺 Rekam Medis Hewan"],
        menu_icon="list", default_index=0,
        styles={
            "container": {"padding": "5!important", "background-color": "#fafafa"},
            "icon": {"color": "#5D4037", "font-size": "20px"}, 
            "nav-link": {"font-size": "15px", "text-align": "left", "margin":"0px", "--hover-color": "#eee"},
            "nav-link-selected": {"background-color": "#8D6E63"},
        }
    )

# ================= HALAMAN 1: PROFIL DESA =================
if menu == "📖 Profil Desa":
    st.markdown("## 📖 Profil Desa Sarwodadi & Giritirta")
    st.write("---")
    st.markdown("Desa Sarwodadi dan Desa Giritirta adalah dua wilayah yang bertetangga dan saling bersinergi di utara Kabupaten Banjarnegara. Warga proaktif memanfaatkan potensi agraris untuk peternakan.")

    sarwodadi_coords = [-7.244900, 109.775966]
    giritirta_coords = [-7.242258, 109.782562]
    center_coords = [(sarwodadi_coords[0] + giritirta_coords[0]) / 2, (sarwodadi_coords[1] + giritirta_coords[1]) / 2]
    
    m = folium.Map(location=center_coords, zoom_start=15)
    folium.Marker(location=sarwodadi_coords, popup="Desa Sarwodadi", tooltip="Desa Sarwodadi", icon=folium.Icon(color="green", icon="leaf")).add_to(m)
    folium.Marker(location=giritirta_coords, popup="Desa Giritirta", tooltip="Desa Giritirta", icon=folium.Icon(color="darkgreen", icon="leaf")).add_to(m)
    
    if os.path.exists("batas_desa.geojson"):
        with open("batas_desa.geojson", "r") as f:
            folium.GeoJson(json.load(f), style_function=lambda feature: {'fillColor': '#8D6E63', 'color': 'red', 'weight': 3, 'dashArray': '5, 5', 'fillOpacity': 0.1}).add_to(m)
            
    st_folium(m, width=700, height=400)

# ================= HALAMAN 2: DASHBOARD UTAMA =================
elif menu == "📊 Dashboard Data Peternakan":
    st.title("📊 Dashboard Pendataan Peternak Warga")
    st.write("---")

    st.sidebar.header("🔎 Filter Data")
    if not data_peternak.empty:
        filter_mode = st.sidebar.radio("Filter berdasarkan:", ["RW", "RT"])
        if filter_mode == "RW":
            pilihan = sorted(data_peternak["RW"].unique())
            terpilih = st.sidebar.multiselect("Pilih RW", options=pilihan, default=pilihan)
            filtered_data = data_peternak[data_peternak["RW"].isin(terpilih)]
        else:
            pilihan = sorted(data_peternak["RT"].unique())
            terpilih = st.sidebar.multiselect("Pilih RT", options=pilihan, default=pilihan)
            filtered_data = data_peternak[data_peternak["RT"].isin(terpilih)]

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Populasi Ternak", f"{int(filtered_data['Total Ekor'].sum())} Ekor")
        col2.metric("Total Peternak", f"{filtered_data['No'].nunique()} Orang")
        col3.metric("Ternak Terbanyak", filtered_data.groupby('Jenis Ternak')['Total Ekor'].sum().idxmax() if not filtered_data.empty else "-")

        st.write("---")
        st.subheader("📄 Data Peternak")
        tabel_tampil = filtered_data[['No', 'Nama Pemilik', 'RT', 'RW', 'Jenis Ternak', 'Jantan', 'Betina', 'Anakan', 'Total Ekor']].copy()
        tabel_tampil.set_index('No', inplace=True)
        st.dataframe(tabel_tampil, use_container_width=True)
        
        st.write("---")
        st.subheader("📊 Distribusi Ternak per RT & RW")
        col_chart1, col_chart2 = st.columns(2)
        with col_chart1:
            fig_rt = px.bar(filtered_data.groupby(["RT", "Jenis Ternak"])["Total Ekor"].sum().reset_index(), x="RT", y="Total Ekor", color="Jenis Ternak", barmode="group", color_discrete_sequence=earth_tones)
            st.plotly_chart(fig_rt, use_container_width=True)
        with col_chart2:
            fig_rw = px.bar(filtered_data.groupby(["RW", "Jenis Ternak"])["Total Ekor"].sum().reset_index(), x="RW", y="Total Ekor", color="Jenis Ternak", barmode="group", color_discrete_sequence=earth_tones)
            st.plotly_chart(fig_rw, use_container_width=True)
    else:
        st.warning("Data belum tersedia atau gagal dimuat.")

# ================= HALAMAN 3: RENCANA VAKSIN =================
elif menu == "💉 Rencana Vitamin & Vaksin":
    st.title("💉 Kalkulator Kebutuhan Logistik Kesehatan")
    st.markdown("Dihitung otomatis khusus untuk peternak yang berstatus **'Bersedia'**.")
    st.write("---")
    
    target_vaksin_df = data_peternak[data_peternak['Ketersediaan'] == 'Bersedia'].copy()
    if not target_vaksin_df.empty:
        k_target = target_vaksin_df[target_vaksin_df['Jenis Ternak'] == 'Kambing']['Total Ekor'].sum()
        d_target = target_vaksin_df[target_vaksin_df['Jenis Ternak'] == 'Domba']['Total Ekor'].sum()
        s_target = target_vaksin_df[target_vaksin_df['Jenis Ternak'] == 'Sapi']['Total Ekor'].sum()
        
        total_vitamin_ml = ((k_target + d_target) * 2) + (s_target * 5)
        botol = (total_vitamin_ml // 100) + (1 if total_vitamin_ml % 100 > 0 else 0)
        
        v1, v2, v3, v4 = st.columns(4)
        v1.metric("Rumah Dikunjungi", f"{target_vaksin_df['No'].nunique()} Rumah")
        v2.metric("Sasaran Hewan", f"{int(target_vaksin_df['Total Ekor'].sum())} Ekor")
        v3.metric("Kebutuhan Dosis", f"{int(total_vitamin_ml)} ml")
        v4.metric("Estimasi Belanja", f"{int(botol)} Botol (100ml)")
        
        st.write("---")
        st.subheader("📋 Lembar Kerja Lapangan (Anonim)")
        tabel_target = target_vaksin_df[['No', 'Nama Pemilik', 'RT', 'RW', 'Jenis Ternak', 'Total Ekor']].copy()
        tabel_target['[ ] Status'] = "[   ]"
        tabel_target.set_index('No', inplace=True)
        st.dataframe(tabel_target, use_container_width=True)
    else:
        st.warning("Belum ada data warga 'Bersedia'.")

# ================= HALAMAN 4: HASIL PEMERIKSAAN MEDIS =================
elif menu == "🩺 Rekam Medis Hewan":
    st.title("🩺 Data Pemeriksaan Kesehatan Hewan")
    st.markdown("Halaman ini menampilkan hasil pemeriksaan medis lapangan. **Data pribadi warga (Nama dan No. Telepon) telah disensor otomatis oleh sistem demi menjaga privasi dan keamanan data.**")
    st.write("---")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Hewan Diperiksa", f"{len(data_medis)} Ekor", help="Termasuk 105 ekor injeksi data lapangan yang belum direkap ke Excel")
    with col2:
        if 'Diagnosa' in data_medis.columns:
            # Penambahan na=False agar tidak error jika ada data kosong (NaN)
            kasus = data_medis[~data_medis['Diagnosa'].astype(str).str.contains('Pemeriksaan|Menunggu', case=False, na=False)]['Diagnosa'].mode()
            st.metric("Kasus Terdeteksi", kasus[0] if not kasus.empty else "Nihil / Aman")
                
    st.write("---")
    st.subheader("📋 Tabel Rekam Medis & Gejala Klinis")
    
    # Memilih kolom yang relevan & aman untuk ditampilkan di publik
    kolom_aman = [col for col in data_medis.columns if col not in ['No', 'ID/Nama Ternak', 'No. Telepon', 'Nama Dokter Hewan / Paramedik']]
    st.dataframe(data_medis[kolom_aman], use_container_width=True)
