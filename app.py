# File ini dimodifikasi secara cepat dari file Notebook
# Terdapat beberapa bagian/cell/komentar yang dihilangkan
# Untuk proses lebih detailnya, cek file ipynb secara langsung

import pandas as pd
import streamlit as st
import plotly.express as px
import folium
import folium.plugins
from streamlit_folium import st_folium

# ===============================
# Baca dataset dari file
# ===============================

st.markdown(
"""
# EDA: Olist E-Commerce Public Dataset
- Author: Andhika Wibawa ([GitHub](https://github.com/AndhikaWB))
- Sumber Dataset: [Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)

Harap bersabar dalam menunggu hasil visualisasi, terutama pada bagian peta...
"""
)

# ============================================
# ### Pertanyaan 1:
# - Produk apa yang paling banyak diminati? Apa kategori dan harganya?
# ============================================

st.header('Pertanyaan Bisnis 1')
st.markdown('Produk apa yang paling banyak diminati? Apa kategori dan harganya?')

df_q1 = pd.read_csv('dashboard/tabel_produk.csv')

fig_q1 = px.bar(
    df_q1,
    x = 'product_id',
    y = 'count',
    color = 'count',
    color_continuous_scale = px.colors.sequential.Blues,
    labels = {
        'product_id': 'ID Produk',
        'count': 'Jumlah Terjual',
        'avg_price': 'Harga Rata-Rata (R$)',
        'product_category_name_english': 'Kategori Produk'
    },
    title = 'Produk yang Paling Diminati',
    # Tampilkan data lainnya saat di-hover mouse
    hover_data = ['avg_price', 'product_category_name_english']
)

fig_q1.update_layout(
    # https://plotly.com/python/reference/layout/xaxis/
    xaxis = {
        # Jangan perlihatkan product_id karena terlalu panjang
        'showticklabels': False,
        # Zoom ke 20 data pertama saja
        'range': [-0.5, 20.5],
    }
)

st.plotly_chart(fig_q1)

st.caption('Gunakan tool "Pan" dan geser grafik ke kanan untuk melihat lebih banyak data.')
st.markdown(
    '''
    Dari grafik di atas, terlihat bahwa produk yang paling diminati (3 besar) adalah `aca2eb`, `99a478`, dan `422879`.
    Masing-masing produk tersebut berharga rata-rata R\$ 71, R\$ 88, dan R\$ 55.
    Lalu, ketiga produk tersebut juga memiliki kategori yang berbeda, yaitu `furniture/decoration`, `bed/bath/table`, dan `garden tools`.
    '''
)

# ============================================
# ### Pertanyaan 2:
# - Kategori apa yang paling banyak diminati?
# ============================================

st.header('Pertanyaan Bisnis 2')
st.markdown('Kategori apa yang paling banyak diminati?')

# Cukup gunakan tabel dari pertanyaan 1
# karena data yang diperlukan sudah ada semua
df_q2 = df_q1

fig_q2 = px.pie(
    df_q2,
    names = 'product_category_name_english',
    values = 'count',
    title = 'Kategori Produk Paling Diminati',
    color_discrete_sequence = px.colors.qualitative.Pastel
)

fig_q2.update_traces(
    textposition = 'inside',
    hovertemplate = '<br>'.join([
        'Kategori Produk: %{label}',
        'Jumlah Produk: %{value}',
        'Persentase: %{percent}'
    ])
)

fig_q2.update_layout(uniformtext_minsize = 12, uniformtext_mode = 'hide')

st.plotly_chart(fig_q2)

st.markdown(
    '''
    Terlihat bahwa kategori produk yang paling diminati (3 besar) adalah `bed/bath/table` dengan persentase 9.87% (11k produk), `health/beauty` dengan persentase 8.58% (9k produk), dan `sports leisure` dengan persentase 7.67% (8k produk).
    '''
)

# ============================================
# ### Pertanyaan 3:
# - Wilayah mana saja yang lebih menguntungkan dan padat pembeli?
# ============================================

st.header('Pertanyaan Bisnis 3')
st.markdown('Wilayah mana saja yang lebih menguntungkan dan padat pembeli?')

df_q3_sample = pd.read_csv('dashboard/tabel_sampel_koordinat.csv')

@st.cache_resource
def cache_map():
    # Buat peta baru dan letakkan posisinya di tengah-tengah semua lokasi
    map = folium.Map(location = df_q3_sample[['geolocation_lat', 'geolocation_lng']].mean().to_list(), zoom_start = 3)

    # Buat pembeda untuk tiap-tiap golongan pembeli (berdasarkan spent_rate)
    # Bisa pakai folium.FeatureGroup (semua titik tampil) atau folium.plugins.MarkerCluster (perwakilan titik)
    marker_low = folium.FeatureGroup(
        name = 'Low Spent-Rate', control = True,
        # icon_create_function = cluster_function['low']
    ).add_to(map)

    marker_med = folium.FeatureGroup(
        name = 'Medium Spent-Rate', control = True,
        # icon_create_function = cluster_function['med']
    ).add_to(map)

    marker_high = folium.FeatureGroup(
        name = 'High Spent-Rate', control = True,
        # icon_create_function = cluster_function['high']
    ).add_to(map)

    # Letakkan marker ke peta beserta keterangannya
    for idx, row in df_q3_sample.iterrows():
        spent_rate = row['spent_rate']
        geoloc = (row['geolocation_lat'], row['geolocation_lng'])
        popup = f'<b>ID Customer:</b> {row["customer_unique_id"]}</br>' \
                f'<b>Total Revenue (R$):</b> {row["total_spent"]}<br>' \
                f'<b>Kategori Revenue:</b> {row["spent_rate"]}'

        # Set warna berdasarkan total uang yang telah dikeluarkan akun pembeli (keuntungan)
        # Hijau = > R$ 120, oranye = > R$ 56.9, merah = < R$ 56.9
        if spent_rate == 'high': mark_color = 'green'
        elif spent_rate == 'med': mark_color = 'orange'
        else: mark_color = 'red'

        circle = folium.Circle(
            location = geoloc,
            fill = True,
            color = mark_color,
            popup = folium.Popup(popup, max_width = 300),
            tooltip = f'<b>Kota:</b> {row["customer_city"]}<br><b>Provinsi:</b> {row["customer_state"]}',
            props = { 'spent_rate': row['spent_rate'] }
        )

        if spent_rate == 'high': circle.add_to(marker_high)
        elif spent_rate == 'med': circle.add_to(marker_med)
        else: circle.add_to(marker_low)

    # Tambahkan layer cluster ke peta
    folium.LayerControl().add_to(map)

    return map

st.markdown('##### Peta Sebaran Domisili Pembeli')

# Tampilkan peta
map = cache_map()
st_folium(map, use_container_width = True)

st.caption('Customer dibagi menjadi 3 kategori (low, med, high) berdasarkan total revenue yang dihasilkannya. Filter kategori tertentu dengan memilih layer pada bagian kanan atas peta.')

df_q3_grouped = pd.read_csv('dashboard/tabel_wilayah.csv')

fig_q3 = px.bar(
    df_q3_grouped,
    x = 'customer_city',
    y = 'total_spent',
    color = 'spent_rate',
    color_discrete_sequence = px.colors.qualitative.Pastel,
    title = 'Wilayah (Kota) yang Paling Menguntungkan',
    labels = {
        # Kategori revenue yang dihasilkan dari customer
        'spent_rate': 'Kategori',
        'customer_city': 'Kota',
        'total_spent': 'Total Revenue (R$)',
        'customer_count': 'Jumlah Customer',
        # Persentase dari total data
        'customer_count_percent': 'Jumlah Customer (%)',
        'total_spent_percent': 'Total Revenue (%)'
    },
    barmode = 'group',
    hover_data = {
        'total_spent_percent': ':.2f',
        'customer_count': ':.2f',
        'customer_count_percent': ':.2f',
    }
)

fig_q3.update_layout(
    # https://plotly.com/python/reference/layout/xaxis/
    xaxis = {
        'title': None,
        # Tampilkan/hilangkan nama kota
        'showticklabels': True,
        # Zoom ke 20 data pertama saja
        'range': [-0.5, 20.5],
    }
)

st.plotly_chart(fig_q3)

st.markdown(
    '''
    Wilayah yang paling menguntungkan adalah `Sao Paulo`, `Rio de Janeiro`, dan `Belo Horizonte`.
    Lalu, terlihat juga bahwa keuntungan ketiga kota tersebut didominasi oleh customer dengan klasifikasi spent_rate `high` (meskipun jumlah akunnya lebih sedikit daripada akun dengan rate di bawahnya yaitu `low` dan `med`).
    '''
)

# ============================================
# ### Pertanyaan 4
# - Adakah siklus/pola waktu tertentu pada pembelian barang? (misal apakah lebih aktif di awal bulan?)
# ============================================

st.header('Pertanyaan Bisnis 4')
st.markdown('Adakah siklus/pola waktu tertentu pada pembelian barang?')

df_q4 = pd.read_csv('dashboard/tabel_order_timeseries.csv')

fig_q4 = px.line(
    df_q4.sort_values('date'),
    x = 'date',
    y = 'total_order',
    hover_data = {
        # 'date': False,
        'month': False,
        'total_order': ':.2f',
        'total_order_monthly': ':.2f',
        'total_spent': ':.2f',
        'total_spent_monthly': ':.2f'
    },
    title = 'Jumlah Pembelian (Order) Berdasarkan Tanggal',
    color = 'month',
    labels = {
        'date': 'Tanggal',
        'month': 'Bulan',
        'total_order': 'Jumlah Order Harian',
        'total_spent': 'Total Revenue Harian (R$)',
        'total_order_monthly': 'Jumlah Order Bulanan',
        'total_spent_monthly': 'Total Revenue Bulanan (R$)'
    },
    template = 'plotly'
)

# https://plotly.com/python/time-series/
fig_q4.update_layout(
    hovermode = 'x',
    xaxis = {
        'rangeslider': {'visible': True}
    }
)

st.plotly_chart(fig_q4)

st.caption('Double click legend (bagian kanan) untuk fokus ke range bulan tertentu.')
st.markdown(
    '''
    Jumlah order (pembelian) akan cenderung menurun di 3/4 bulan (minggu terakhir bulan), namun pola dan pengaruhnya tidak terlalu signifikan.
    Terlihat juga bulan November 2017 merupakan bulan yang paling menguntungkan dengan jumlah order sebanyak 7451 buah (R\$ 1,010,271).
    '''
)

# ============================================
# ### Pertanyaan 5
# - Berapa persen pertumbuhan customer dan revenue tiap bulannya?
# ============================================

st.header('Pertanyaan Bisnis 5')
st.markdown('Berapa persen pertumbuhan customer dan revenue tiap bulannya?')

df_q5 = pd.read_csv('dashboard/tabel_growth_bulanan.csv')

fig_q5 = px.line(
    df_q5,
    x = 'month',
    y = 'total_spent',
    color = 'customer_type',
    title = 'Pertumbuhan Jumlah Customer dan Revenue Per Bulan',
    hover_data = {
        # Urutan variabel di sini mempengaruhi urutannya di hover
        'month': False,
        'total_spent_pct': ':.2f',
        'spent_growth_pct': ':.2f',
        'total_order': ':.2f',
        'total_order_pct': ':.2f',
        'order_growth_pct': ':.2f'
    },
    labels = {
        'month': 'Bulan',
        'customer_type': 'Jenis Customer',
        'total_spent': 'Total Revenue (R$)',
        'total_spent_pct': 'Total Revenue (%)',
        'total_order': 'Jumlah Order',
        'total_order_pct': 'Jumlah Order (%)',
        # Kenaikan/penurunan merupakan perubahan sejak bulan sebelumnya
        'spent_growth_pct': 'Kenaikan Total Revenue (%)',
        'order_growth_pct': 'Kenaikan Jumlah Order (%)'
    },
    markers = True
)

fig_q5.update_layout(hovermode = 'x unified')

st.plotly_chart(fig_q5)

st.caption('Dari grafik di atas, terlihat bahwa sebagian besar customer yang melakukan order merupakan akun baru.')
st.markdown(
    '''
    Pada periode Sep 2016 - Nov 2017, pertumbuhan jumlah customer (~2-3%) dan revenue (~0.2-0.5%) cenderung terus meningkat.
    Setelah periode itu, pertumbuhan relatif stagnan (naik-turun) meskipun perbandingan jumlah order dari customer barunya (~96%) tetap lebih banyak dari customer lama (~3%).
    '''
)

# Untuk menghentikan cycle Streamlit (apabila lambat)
st.stop()