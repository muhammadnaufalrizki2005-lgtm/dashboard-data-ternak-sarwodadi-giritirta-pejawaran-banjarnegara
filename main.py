import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from streamlit_option_menu import option_menu
import json
import os

# Konfigurasi Halaman
st.set_page_config(page_title="Dashboard Pendataan Ternak", layout="wide", initial_sidebar_state="expanded")

# Kumpulan Warna Aesthetic/Earth Tones untuk Grafik
COLORS = ['#8D6E63', '#A1887F', '#D7CCC8', '#5D4037', '#BCAAA4', '#795548', '#3E2723']
TERN_COLORS = {'Kambing': '#8D6E63', 'Domba': '#BCAAA4', 'Sapi': '#3E2723'}

# =========================================================
# FUNGSI 1: LOAD DATA POPULASI
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
    
    # PERBAIKAN: Mengatasi Missing Data agar tampil "Belum Terdata"
    def format_wilayah(val, prefix):
        if pd.isna(val): return f"{prefix} Belum Terdata"
        s = str(val).replace('.0', '').strip()
        if s.lower() in ['nan', '-', '', 'none', '0-']: return f"{prefix} Belum Terdata"
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
                    'Nama Pemilik': nama_disensor, 
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
# FUNGSI 2: LOAD DATA MEDIS
# =========================================================
@st.cache_data
def load_data_medis():
    try:
        df_medis = pd.read_excel('Pemeriksaan Hewan Ternak.xlsx', sheet_name='Sheet2')
        if 'Nama Peternak' in df_medis.columns:
            df_medis['Nama Peternak'] = 'Peternak - ' + df_medis['No'].astype(str)
        if 'No. Telepon' in df_medis.columns:
            df_medis['No. Telepon'] = '*** (Disembunyikan)'
    except Exception:
        df_medis = pd.DataFrame(columns=['Nama Peternak', 'Alamat Peternakan (RT/RW)', 'Jenis Ternak', 'Suhu Tubuh (°C)', 'Gejala Klinis', 'Diagnosa', 'Terapi / Pengobatan'])

    tambahan_susulan = []
    lokasi_baru = ['RT 1/RW 1 (Sarwodadi)', 'RT 2/RW 2 (Sarwodadi)', 'Dusun Tlodas']
    for lok in lokasi_baru:
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
    df_medis = df_medis.astype(object).fillna('-')
    return df_medis

# =========================================================
# MEMUAT DATA
# =========================================================
data_peternak = load_data_populasi()
data_medis = load_data_medis()

# =========================================================
# SIDEBAR & NAVIGASI
# =========================================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3050/3050525.png", width=100) # Ilustrasi sapi/ternak
    st.markdown("### Sistem Informasi Ternak")
    menu = option_menu(
        "Menu Navigasi",
        ["📖 Profil Desa", "📊 Statistik & Populasi", "💉 Kalkulator Vaksin", "🩺 Pantauan Kesehatan"],
        menu_icon="cast", default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#5D4037", "font-size": "18px"}, 
            "nav-link": {"font-size": "15px", "text-align": "left", "margin":"5px", "--hover-color": "#e0e0e0"},
            "nav-link-selected": {"background-color": "#8D6E63", "color": "white", "font-weight": "bold"},
        }
    )

# =========================================================
# HALAMAN 1: PROFIL DESA
# =========================================================
if menu == "📖 Profil Desa":
    st.markdown("<h1 style='text-align: center; color: #4E342E;'>Peta Potensi Peternakan Desa</h1>", unsafe_allow_html=True)
    st.write("---")
    
    st.markdown("""
    > **Sarwodadi & Giritirta** merupakan wilayah agraris dengan potensi peternakan yang kuat. 
    > Peta di bawah ini menunjukkan area sebaran peternak warga.
    """)

    sarwodadi_coords = [-7.244900, 109.775966]
    giritirta_coords = [-7.242258, 109.782562]
    center_coords = [(sarwodadi_coords[0] + giritirta_coords[0]) / 2, (sarwodadi_coords[1] + giritirta_coords[1]) / 2]
    
    m = folium.Map(location=center_coords, zoom_start=15, tiles="CartoDB positron")
    folium.Marker(location=sarwodadi_coords, popup="Desa Sarwodadi", icon=folium.Icon(color="green", icon="info-sign")).add_to(m)
    folium.Marker(location=giritirta_coords, popup="Desa Giritirta", icon=folium.Icon(color="lightgreen", icon="info-sign")).add_to(m)
    
    st_folium(m, width=1000, height=450)

# =========================================================
# HALAMAN 2: STATISTIK POPULASI (VISUALISASI KREATIF)
# =========================================================
elif menu == "📊 Statistik & Populasi":
    st.markdown("<h1 style='color: #4E342E;'>📊 Infografis Populasi Ternak Warga</h1>", unsafe_allow_html=True)
    st.write("Pantau sebaran dan kekayaan peternakan desa kita dengan mudah melalui grafik di bawah ini.")
    
    if not data_peternak.empty:
        # ---- HACK MISSING DATA & FILTER ----
        # Hanya tampilkan data yang total ekornya lebih dari 0 agar grafik tidak error
        df_visual = data_peternak[data_peternak['Total Ekor'] > 0].copy()
        df_visual['RW'] = df_visual['RW'].replace("", "RW Belum Terdata")
        df_visual['RT'] = df_visual['RT'].replace("", "RT Belum Terdata")

        # ---- BAGIAN ATAS: KARTU METRIK UTAMA ----
        st.markdown("### 🏆 Ringkasan Kekayaan Ternak")
        col1, col2, col3, col4 = st.columns(4)
        total_ekor = int(df_visual['Total Ekor'].sum())
        total_peternak = df_visual['No'].nunique()
        ternak_favorit = df_visual.groupby('Jenis Ternak')['Total Ekor'].sum().idxmax()
        rt_terbanyak = df_visual.groupby('RT')['Total Ekor'].sum().idxmax()

        col1.info(f"**🐄 Total Populasi**\n## {total_ekor} Ekor")
        col2.success(f"**👨‍🌾 Total Peternak**\n## {total_peternak} Warga")
        col3.warning(f"**⭐ Ternak Mayoritas**\n## {ternak_favorit}")
        col4.error(f"**📍 RT Terpadat**\n## {rt_terbanyak}")
        
        st.write("---")

        # ---- VISUALISASI UTAMA ----
        c1, c2 = st.columns([1, 1])
        
        with c1:
            # DONUT CHART: Komposisi Hewan
            st.markdown("#### 🍩 Komposisi Jenis Ternak")
            df_jenis = df_visual.groupby('Jenis Ternak')['Total Ekor'].sum().reset_index()
            fig_pie = px.pie(df_jenis, values='Total Ekor', names='Jenis Ternak', hole=0.5,
                             color='Jenis Ternak', color_discrete_map=TERN_COLORS)
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            fig_pie.update_layout(margin=dict(t=0, b=0, l=0, r=0), showlegend=False)
            st.plotly_chart(fig_pie, use_container_width=True)

        with c2:
            # TREEMAP: Sebaran per Wilayah
            st.markdown("#### 🗺️ Peta Kepadatan Wilayah (RW & RT)")
            # Menggunakan YlOrBr agar tidak error di Plotly Express
            fig_tree = px.treemap(df_visual, path=['RW', 'RT', 'Jenis Ternak'], values='Total Ekor',
                                  color='Total Ekor', color_continuous_scale='YlOrBr')
            fig_tree.update_layout(margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig_tree, use_container_width=True)

        # BAR CHART: Jantan vs Betina vs Anakan
        st.markdown("#### 📊 Demografi Kelompok Umur & Kelamin")
        df_demografi = df_visual.groupby('Jenis Ternak')[['Jantan', 'Betina', 'Anakan']].sum().reset_index()
        df_demografi_melt = df_demografi.melt(id_vars='Jenis Ternak', var_name='Kategori', value_name='Jumlah')
        fig_bar = px.bar(df_demografi_melt, x='Jenis Ternak', y='Jumlah', color='Kategori',
                         barmode='group', color_discrete_sequence=['#5D4037', '#A1887F', '#D7CCC8'])
        st.plotly_chart(fig_bar, use_container_width=True)

        # TABEL MENTAH (Disembunyikan dengan Expander agar tidak penuh)
        with st.expander("📂 Klik di sini untuk melihat Tabel Data Detail (Raw Data)"):
            tabel_tampil = data_peternak[['No', 'Nama Pemilik', 'RT', 'RW', 'Jenis Ternak', 'Total Ekor']].copy()
            tabel_tampil.set_index('No', inplace=True)
            st.dataframe(tabel_tampil, use_container_width=True)
    else:
        st.warning("Data Populasi kosong.")

# =========================================================
# HALAMAN 3: RENCANA VAKSIN
# =========================================================
elif menu == "💉 Kalkulator Vaksin":
    st.markdown("<h1 style='color: #4E342E;'>💉 Prediksi & Kebutuhan Logistik Vaksinasi</h1>", unsafe_allow_html=True)
    st.write("Kalkulasi otomatis kebutuhan botol vitamin dan vaksin untuk peternak yang berstatus **Bersedia**.")
    st.write("---")

    target_vaksin_df = data_peternak[data_peternak['Ketersediaan'] == 'Bersedia'].copy()
    if not target_vaksin_df.empty:
        k_target = target_vaksin_df[target_vaksin_df['Jenis Ternak'] == 'Kambing']['Total Ekor'].sum()
        d_target = target_vaksin_df[target_vaksin_df['Jenis Ternak'] == 'Domba']['Total Ekor'].sum()
        s_target = target_vaksin_df[target_vaksin_df['Jenis Ternak'] == 'Sapi']['Total Ekor'].sum()
        
        # Asumsi Dosis: Kambing/Domba 2ml, Sapi 5ml
        dosis_k = k_target * 2
        dosis_d = d_target * 2
        dosis_s = s_target * 5
        total_vitamin_ml = dosis_k + dosis_d + dosis_s
        botol = int((total_vitamin_ml // 100) + (1 if total_vitamin_ml % 100 > 0 else 0))

        colA, colB = st.columns([1, 2])
        with colA:
            st.markdown("### 📦 Total Belanja")
            st.image("https://cdn-icons-png.flaticon.com/512/883/883356.png", width=80) # Ikon botol obat
            st.markdown(f"<h2 style='color:#d32f2f;'>{botol} Botol</h2>", unsafe_allow_html=True)
            st.write(f"*(1 Botol = 100 ml | Total Kebutuhan {total_vitamin_ml} ml)*")
            
        with colB:
            st.markdown("### 🎯 Proporsi Dosis per Hewan (ml)")
            fig_dosis = px.funnel(
                x=[dosis_s, dosis_k, dosis_d], 
                y=['Sapi (5ml/ekor)', 'Kambing (2ml/ekor)', 'Domba (2ml/ekor)'],
                color_discrete_sequence=['#8D6E63']
            )
            fig_dosis.update_layout(margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig_dosis, use_container_width=True)

        st.write("---")
        st.subheader("📋 Lembar Kerja Lapangan Pemasangan Vaksin")
        st.info("Tabel ini dirancang agar mudah dibaca oleh mantri/dokter hewan saat di lapangan.")
        tabel_target = target_vaksin_df[['No', 'Nama Pemilik', 'RT', 'RW', 'Jenis Ternak', 'Total Ekor']].copy()
        tabel_target['Ceklist Vaksin'] = "⬜ Belum"
        st.dataframe(tabel_target, use_container_width=True, hide_index=True)
    else:
        st.warning("Belum ada warga yang terdata dengan status 'Bersedia'.")

# =========================================================
# HALAMAN 4: REKAM MEDIS
# =========================================================
elif menu == "🩺 Pantauan Kesehatan":
    st.markdown("<h1 style='color: #4E342E;'>🩺 Radar Kesehatan Hewan Ternak</h1>", unsafe_allow_html=True)
    st.markdown("*Pantauan penyakit klinis dan rekam jejak pengobatan medis yang dilakukan.*")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Hewan Diperiksa (termasuk Injeksi Data Lapangan)", f"{len(data_medis)} Ekor")
    with col2:
        if 'Diagnosa' in data_medis.columns:
            kasus_aktif = data_medis[~data_medis['Diagnosa'].astype(str).str.contains('Pemeriksaan|Menunggu|-', case=False, na=False)]
            st.metric("Total Temuan Kasus Penyakit", f"{len(kasus_aktif)} Kasus")
    
    st.write("---")
    
    c1, c2 = st.columns([1.5, 1])
    with c1:
        st.markdown("#### 🦠 Grafik Tren Temuan Penyakit (Diagnosa)")
        if 'Diagnosa' in data_medis.columns:
            df_diagnosa = data_medis['Diagnosa'].value_counts().reset_index()
            df_diagnosa.columns = ['Diagnosa', 'Jumlah']
            fig_diag = px.bar(df_diagnosa, x='Jumlah', y='Diagnosa', orientation='h', 
                              color='Jumlah', color_continuous_scale='Reds')
            fig_diag.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(t=0, l=0, r=0))
            st.plotly_chart(fig_diag, use_container_width=True)
            
    with c2:
        st.markdown("#### 💉 Pengobatan Teratas")
        if 'Terapi / Pengobatan' in data_medis.columns:
            df_terapi = data_medis['Terapi / Pengobatan'].value_counts().reset_index().head(5)
            df_terapi.columns = ['Terapi', 'Jumlah']
            fig_terapi = px.pie(df_terapi, values='Jumlah', names='Terapi', hole=0.4, 
                                color_discrete_sequence=px.colors.sequential.Teal)
            fig_terapi.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0))
            fig_terapi.update_traces(textinfo='percent+label')
            st.plotly_chart(fig_terapi, use_container_width=True)

    st.write("---")
    st.markdown("#### 📜 Buku Induk Rekam Medis")
    st.markdown("*(Nama warga disamarkan oleh sistem untuk melindungi privasi)*")
    
    kolom_aman = [col for col in data_medis.columns if col not in ['No', 'ID/Nama Ternak', 'No. Telepon', 'Nama Dokter Hewan / Paramedik']]
    df_tampil = data_medis[kolom_aman].copy()
    
    # PERBAIKAN: Merapikan nilai '-' yang kosong menjadi teks yang lebih informatif
    if 'Terapi / Pengobatan' in df_tampil.columns:
        df_tampil['Terapi / Pengobatan'] = df_tampil['Terapi / Pengobatan'].replace('-', 'Belum Diberikan Tindakan')
    if 'Diagnosa' in df_tampil.columns:
        df_tampil['Diagnosa'] = df_tampil['Diagnosa'].replace('-', 'Menunggu Hasil')
        
    st.dataframe(df_tampil, use_container_width=True)
