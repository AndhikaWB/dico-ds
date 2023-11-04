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
# Proyek Analisis Data: E-Commerce Public Dataset
- Nama: -
- Email: -
- ID: -

Harap bersabar dalam menunggu hasil visualisasi, terutama pada bagian peta...
"""
)

# ============================================
# ### Pertanyaan 1:
# - Produk apa yang paling banyak diminati? Apa kategori dan harganya?
# ============================================

st.header('Pertanyaan 1')
st.caption('Produk apa yang paling banyak diminati? Apa kategori dan harganya?')

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
        'avg_price': 'Harga Rata-Rata',
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

# ============================================
# ### Pertanyaan 2:
# - Kategori apa yang paling banyak diminati?
# ============================================

st.header('Pertanyaan 2')
st.caption('Kategori apa yang paling banyak diminati?')

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
        'Persentase: %{percent}',
        # "XXX: %{customdata[0]}"
    ])
)

fig_q2.update_layout(uniformtext_minsize = 12, uniformtext_mode = 'hide')

st.plotly_chart(fig_q2)

# ============================================
# ### Pertanyaan 3:
# - Wilayah mana saja yang lebih menguntungkan dan padat pembeli?
# ============================================

st.header('Pertanyaan 3')
st.caption('Wilayah mana saja yang lebih menguntungkan dan padat pembeli?')

df_q3_sample = pd.read_csv('dashboard/tabel_sampel_koordinat.csv')

@st.cache_resource
def cache_map():
    # Buat peta baru dan letakkan posisinya di tengah-tengah semua lokasi
    map = folium.Map(location = df_q3_sample[['geolocation_lat', 'geolocation_lng']].mean().to_list(), zoom_start = 3)

    # Buat pembeda untuk tiap-tiap golongan pembeli (berdasarkan spent_rate)
    # Bisa pakai folium.FeatureGroup (semua titik tampil) atau folium.plugins.MarkerCluster (generalisasi titik)
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
        popup = f'<b>ID Customer:</b> {row["customer_id"]}</br>' \
                f'<b>Total Pembelian (R$):</b> {row["total_spent"]}<br>' \
                f'<b>Rating Pembelian:</b> {row["spent_rate"]}'

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
st_folium(map)

df_q3_grouped = pd.read_csv('dashboard/tabel_wilayah.csv')

fig_q3 = px.bar(
    df_q3_grouped,
    x = 'customer_city',
    y = 'total_spent',
    color = 'spent_rate',
    color_discrete_sequence = px.colors.qualitative.Pastel,
    title = 'Wilayah (Kota) yang Paling Menguntungkan',
    labels = {
        'spent_rate': 'Kategori',
        'customer_city': 'Kota',
        'total_spent': 'Total Pembelian (R$)',
        'customer_count': 'Jumlah Customer'
    },
    barmode = 'group',
    hover_data = [
        'customer_count'
    ]
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

# ============================================
# ### Pertanyaan 4
# - Adakah siklus/pola waktu tertentu pada pembelian barang? (misal apakah lebih aktif di awal bulan?)
# ============================================

st.header('Pertanyaan 4')
st.caption('Adakah siklus/pola waktu tertentu pada pembelian barang?')

df_q4 = pd.read_csv('dashboard/tabel_order_timeseries.csv')

fig_q4 = px.line(
    df_q4.sort_values('date'),
    x = 'date',
    y = 'total_order',
    hover_data = {
        'total_spent': True,
        # 'date': False,
        'month': False,
        'total_order_monthly': True,
        'total_spent_monthly': True
    },
    title = 'Jumlah Pembelian (Order) Berdasarkan Tanggal',
    color = 'month',
    labels = {
        'total_order': 'Jumlah Order Harian',
        'date': 'Tanggal',
        'total_spent': 'Total Pembelian Harian (R$)',
        'month': 'Bulan',
        'total_order_monthly': 'Jumlah Order Bulanan',
        'total_spent_monthly': 'Total Pembelian Bulanan (R$)'
    },
    template = 'plotly'
)

# https://plotly.com/python/time-series/
fig_q4.update_layout(
    hovermode = 'x unified',
    xaxis = {
        'rangeslider': {'visible': True}
    }
)

st.plotly_chart(fig_q4)
st.caption('Double click legend untuk fokus ke bulan tertentu')

# Untuk menghentikan cycle Streamlit (apabila lambat)
st.stop()