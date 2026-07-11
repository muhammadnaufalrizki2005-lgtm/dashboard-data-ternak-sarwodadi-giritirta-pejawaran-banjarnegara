import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from streamlit_option_menu import option_menu

# Konfigurasi Halaman (Minimalist & Clean)
st.set_page_config(page_title="Dashboard Pendataan Ternak", layout="wide")

# Fungsi Load, Clean & Parse Data
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('Data Ternak Sarwodadi, Giritirta.xlsx - Sheet1.csv', header=None, skiprows=3)
    except:
        try:
            df = pd.read_excel('Data Ternak Sarwodadi, Giritirta.xlsx', header=None, skiprows=3)
        except:
            st.error("File data tidak ditemukan. Pastikan nama filenya benar di GitHub.")
            return pd.DataFrame()
    
    # Memastikan hanya mengambil 17 kolom (mencegah error length mismatch)
    df = df.iloc[:, 0:17]
    
    df.columns = [
        'No', 'Nama Pemilik', 'RT', 'RW', 
        'Kambing_Jantan', 'Kambing_Betina', 'Kambing_Total', 'Kambing_Anakan',
        'Domba_Jantan', 'Domba_Betina', 'Domba_Total', 'Domba_Anakan',
        'Sapi_Jantan', 'Sapi_Betina', 'Sapi_Total', 'Sapi_Anakan',
        'Ketersediaan'
    ]
    
    # Fungsi khusus untuk menangani "0-" atau "-"
    def format_wilayah(val, prefix):
        if pd.isna(val):
            return "-"
        
        s = str(val).replace('.0', '').strip()
        if s.lower() in ['nan', '-', '', 'none', '0-']:
            return "-"
            
        if s.isdigit() and len(s) == 1:
            return f"{prefix} 0{s}"
            
        return f"{prefix} {s.upper()}"
    
    records = []
    for _, row in df.iterrows():
        if pd.isna(row['Nama Pemilik']):
            continue
            
        def parse_num(val):
            try:
                return float(val) if pd.notna(val) else 0.0
            except:
                return 0.0
                
        for jenis in ['Kambing', 'Domba', 'Sapi']:
            jantan = parse_num(row[f'{jenis}_Jantan'])
            betina = parse_num(row[f'{jenis}_Betina'])
            anakan = parse_num(row[f'{jenis}_Anakan'])
            total_excel = parse_num(row[f'{jenis}_Total'])
            
            if jantan > 0 or betina > 0 or anakan > 0 or total_excel > 0:
                rt_rapi = format_wilayah(row['RT'], "RT")
                rw_rapi = format_wilayah(row['RW'], "RW")
                
                final_total = total_excel if total_excel > 0 else (jantan + betina + anakan)
                
                records.append({
                    'No': int(row['No']) if pd.notna(row['No']) else 0,
                    'Nama Pemilik': str(row['Nama Pemilik']).strip().title(),
                    'RT': rt_rapi,
                    'RW': rw_rapi,
                    'Jenis Ternak': jenis,
                    'Jantan': int(jantan),
                    'Betina': int(betina),
                    'Anakan': int(anakan),
                    'Total Ekor': int(final_total),
                    'Ketersediaan': str(row['Ketersediaan']).strip() if pd.notna(row['Ketersediaan']) else 'Belum Konfirmasi'
                })
                
    final_df = pd.DataFrame(records)
    return final_df

data_peternak = load_data()
earth_tones = ['#8D6E63', '#D7CCC8', '#A1887F', '#5D4037', '#BCAAA4']

# Sidebar Navigasi dengan tambahan Menu Program Kerja Kesehatan Hewan
with st.sidebar:
    menu = option_menu(
        "📌 Menu Navigasi",
        ["📖 Profil Desa", "📊 Dashboard Data Peternakan", "💉 Rencana Vitamin & Vaksin"],
        menu_icon="list",
        default_index=0,
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
    st.markdown("""
    **Desa Sarwodadi dan Desa Giritirta** adalah dua wilayah yang bertetangga dan saling bersinergi di utara Kabupaten Banjarnegara. 
    Dikelilingi oleh keasrian alam khas pegunungan, kedua desa ini memiliki lingkungan yang sangat mendukung kemajuan sektor agraris.
    
    ### 👥 Potensi Peternakan Warga
    Warga di Desa Sarwodadi dan Giritirta sangat proaktif dalam memanfaatkan potensi alamnya, salah satunya melalui sektor peternakan yang menjadi pundi-pundi ekonomi keluarga.
    
    Berdasarkan hasil pendataan wilayah terkini, hewan ternak yang menjadi komoditas utama warga di kedua desa ini meliputi:
    * **Kambing**
    * **Domba**
    * **Sapi**
    """)

    st.markdown("### 🗺️ Peta Wilayah")
    sarwodadi_coords = [-7.244900, 109.775966]
    giritirta_coords = [-7.242258, 109.782562]
    center_coords = [(sarwodadi_coords[0] + giritirta_coords[0]) / 2, (sarwodadi_coords[1] + giritirta_coords[1]) / 2]
    
    m = folium.Map(location=center_coords, zoom_start=15)
    folium.Marker(location=sarwodadi_coords, popup="Desa Sarwodadi", tooltip="Desa Sarwodadi", icon=folium.Icon(color="green", icon="leaf")).add_to(m)
    folium.Marker(location=giritirta_coords, popup="Desa Giritirta", tooltip="Desa Giritirta", icon=folium.Icon(color="darkgreen", icon="leaf")).add_to(m)
    st_folium(m, width=700, height=400)

# ================= HALAMAN 2: DASHBOARD UTAMA =================
elif menu == "📊 Dashboard Data Peternakan":
    st.title("📊 Dashboard Pendataan Peternak Warga")
    st.write("---")

    st.sidebar.header("🔎 Filter Data")
    if not data_peternak.empty:
        filter_mode = st.sidebar.radio("Filter berdasarkan:", ["RW", "RT"])

        if filter_mode == "RW":
            pilihan_unik = sorted(data_peternak["RW"].unique())
            selected_lokasi = st.sidebar.multiselect("Pilih RW", options=pilihan_unik, default=pilihan_unik)
            filtered_data = data_peternak[data_peternak["RW"].isin(selected_lokasi)]
        else:
            pilihan_unik = sorted(data_peternak["RT"].unique())
            selected_lokasi = st.sidebar.multiselect("Pilih RT", options=pilihan_unik, default=pilihan_unik)
            filtered_data = data_peternak[data_peternak["RT"].isin(selected_lokasi)]

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Total Populasi Ternak", value=f"{int(filtered_data['Total Ekor'].sum())} Ekor")
        with col2:
            st.metric(label="Total Peternak", value=f"{filtered_data['No'].nunique()} Orang")
        with col3:
            if not filtered_data.empty:
                st.metric(label="Jenis Ternak Terbanyak", value=filtered_data.groupby('Jenis Ternak')['Total Ekor'].sum().idxmax())
            else:
                st.metric(label="Jenis Ternak Terbanyak", value="-")

        st.write("---")

        st.subheader("📄 Data Peternak")
        tabel_tampil = filtered_data[['No', 'Nama Pemilik', 'RT', 'RW', 'Jenis Ternak', 'Jantan', 'Betina', 'Anakan', 'Total Ekor', 'Ketersediaan']].copy()
        tabel_tampil.set_index('No', inplace=True)
        
        st.dataframe(tabel_tampil, use_container_width=True)
        st.write("---")

        st.subheader("📊 Total Ternak per RT")
        total_per_rt = filtered_data.groupby(["RT", "Jenis Ternak"])["Total Ekor"].sum().reset_index()
        fig_rt = px.bar(
            total_per_rt, x="RT", y="Total Ekor", color="Jenis Ternak",
            barmode="group", color_discrete_sequence=earth_tones, text_auto=True
        )
        fig_rt.update_xaxes(type='category', title_text='Rukun Tetangga (RT)')
        st.plotly_chart(fig_rt, use_container_width=True)

        st.subheader("🏘️ Total Ternak per RW")
        total_per_rw = filtered_data.groupby(["RW", "Jenis Ternak"])["Total Ekor"].sum().reset_index()
        fig_rw = px.bar(
            total_per_rw, x="RW", y="Total Ekor", color="Jenis Ternak",
            barmode="group", color_discrete_sequence=earth_tones, text_auto=True
        )
        fig_rw.update_xaxes(type='category', title_text='Rukun Warga (RW)')
        st.plotly_chart(fig_rw, use_container_width=True)

        st.subheader("🥧 Distribusi Ternak Keseluruhan")
        total_all = filtered_data.groupby("Jenis Ternak")["Total Ekor"].sum().reset_index()
        fig_pie = px.pie(
            total_all, names="Jenis Ternak", values="Total Ekor",
            color_discrete_sequence=earth_tones
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.warning("Data belum tersedia atau gagal dimuat.")

# ================= HALAMAN 3: FITUR KOLABORASI PROKER VAKSIN & VITAMIN =================
elif menu == "💉 Rencana Vitamin & Vaksin":
    st.title("💉 Perencanaan Program Kesehatan Hewan")
    st.write("Halaman ini dirancang khusus untuk mendukung program pemberian vaksin dan vitamin pada ternak warga.")
    st.write("---")
    
    # 1. Analisis Ketersediaan Warga (Pie Chart Keberhasilan Sosialisasi)
    st.subheader("🥧 Persentase Ketersediaan Warga")
    data_pemilik_unik = data_peternak.groupby('No').first().reset_index()
    keberhasilan_df = data_pemilik_unik.groupby('Ketersediaan').size().reset_index(name='Jumlah Orang')
    
    fig_ketersediaan = px.pie(
        keberhasilan_df, names="Ketersediaan", values="Jumlah Orang",
        color_discrete_sequence=['#8D6E63', '#D7CCC8', '#5D4037']
    )
    st.plotly_chart(fig_ketersediaan, use_container_width=True)
    st.write("---")

    # 2. Filter data target lapangan (Hanya yang berstatus 'Bersedia')
    target_vaksin_df = data_peternak[data_peternak['Ketersediaan'] == 'Bersedia'].copy()
    
    st.subheader("📋 Kalkulator Estimasi Kebutuhan Logistik (Target Warga Bersedia)")
    
    if not target_vaksin_df.empty:
        # Menghitung populasi target spesifik berdasarkan jenis hewan
        kambing_target = target_vaksin_df[target_vaksin_df['Jenis Ternak'] == 'Kambing']['Total Ekor'].sum()
        domba_target = target_vaksin_df[target_vaksin_df['Jenis Ternak'] == 'Domba']['Total Ekor'].sum()
        sapi_target = target_vaksin_df[target_vaksin_df['Jenis Ternak'] == 'Sapi']['Total Ekor'].sum()
        
        # Asumsi Dosis Vitamin / Vaksin: Kambing & Domba = 2 ml, Sapi = 5 ml
        dosis_kambing_domba = 2
        dosis_sapi = 5
        total_vitamin_ml = ((kambing_target + domba_target) * dosis_kambing_domba) + (sapi_target * dosis_sapi)
        
        # Tampilan Metrik Logistik Lapangan
        v_col1, v_col2, v_col3 = st.columns(3)
        with v_col1:
            st.metric(label="Total Peternak Siap Dikunjungi", value=f"{target_vaksin_df['No'].nunique()} Orang")
        with v_col2:
            st.metric(label="Total Populasi Hewan Target", value=f"{int(target_vaksin_df['Total Ekor'].sum())} Ekor")
        with v_col3:
            st.metric(label="Estimasi Kebutuhan Cairan Vitamin", value=f"{int(total_vitamin_ml)} ml", help="Kambing/Domba: 2ml/ekor, Sapi: 5ml/ekor")
            
        st.write("---")
        
        # 3. Daftar Target Lapangan & Tombol Unduh Cetak
        st.subheader("📍 Daftar Nama & Lokasi Target Lapangan")
        st.write("Gunakan tombol di bawah ini untuk mengunduh daftar target ke dalam bentuk Excel/CSV agar mudah dibawa saat turun ke lapangan.")
        
        tabel_target = target_vaksin_df[['No', 'Nama Pemilik', 'RT', 'RW', 'Jenis Ternak', 'Jantan', 'Betina', 'Anakan', 'Total Ekor']].copy()
        tabel_target.set_index('No', inplace=True)
        
        # Sediakan Tombol Download CSV
        csv_data = tabel_target.to_csv().encode('utf-8')
        st.download_button(
            label="📥 Unduh Daftar Target Lapangan (CSV)",
            data=csv_data,
            file_name="target_lapangan_vitamin_ternak.csv",
            mime="text/csv"
        )
        
        # Menampilkan Tabel Target
        st.dataframe(tabel_target, use_container_width=True)
        
    else:
        st.warning("Belum ada data warga dengan status 'Bersedia' yang terdeteksi.")
