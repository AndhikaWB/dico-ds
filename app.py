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

df_list = {
    'customers': pd.read_csv('data/olist_customers_dataset.csv'),
    'geolocation': pd.read_csv('data/olist_geolocation_dataset.csv'),
    'order_items': pd.read_csv('data/olist_order_items_dataset.csv'),
    'order_payments': pd.read_csv('data/olist_order_payments_dataset.csv'),
    'order_reviews': pd.read_csv('data/olist_order_reviews_dataset.csv'),
    'orders': pd.read_csv('data/olist_orders_dataset.csv'),
    'products': pd.read_csv('data/olist_products_dataset.csv'),
    'sellers': pd.read_csv('data/olist_sellers_dataset.csv'),
    'product_category': pd.read_csv('data/product_category_name_translation.csv')
}

# ===============================
# Konversi zip code ke string
# ===============================

# Bila tipe data masih int, maka top dan freq nya tidak akan terlihat ketika di-describe
df_list['customers']['customer_zip_code_prefix'] = df_list['customers']['customer_zip_code_prefix'].astype('object')
df_list['geolocation']['geolocation_zip_code_prefix'] = df_list['geolocation']['geolocation_zip_code_prefix'].astype('object')
df_list['sellers']['seller_zip_code_prefix'] = df_list['sellers']['seller_zip_code_prefix'].astype('object')

for key in ['customers', 'geolocation']:
    print('* ' + key + f' (length: {len(df_list[key])})')
    print(df_list[key].dtypes)
    print()

# ===============================
# Konversi string ke datetime
# ===============================

df_to_date_list = {
    # Nama tabel: Nama kolom
    'order_items': ['shipping_limit_date'],
    'order_reviews': ['review_creation_date', 'review_answer_timestamp'],
    'orders': [
        'order_purchase_timestamp',
        'order_approved_at',
        'order_delivered_carrier_date',
        'order_delivered_customer_date',
        'order_estimated_delivery_date'
    ]
}

for key in df_to_date_list:
    for val in df_to_date_list[key]:
        df_list[key][val] = pd.to_datetime(
            df_list[key][val],
            # https://strftime.org/
            format = '%Y-%m-%d %H:%M:%S'
        )

# Drop kolom duplikat pada tabel geolocation
df_list['geolocation'].drop_duplicates(ignore_index = True, inplace = True)

# ============================================
# Imputasi nilai kosong pada tabel order
# ============================================

# Hilangkan baris null pada order yang belum di-approve
df_list['orders'].dropna(subset = ['order_approved_at'], inplace = True)

# Hitung rata-rata (modus) jeda waktu (misal X hari) dari approve hingga sampai ke kurir/pembeli
# Berbeda dengan fungsi sebelumnya, fungsi ini menggunakan modus dari 1 tabel (bukan hanya tetangga serupa)
days_carrier = (df_list['orders']['order_delivered_carrier_date'] - df_list['orders']['order_approved_at']).dt.days.mode()[0]
days_customer = (df_list['orders']['order_delivered_customer_date'] - df_list['orders']['order_approved_at']).dt.days.mode()[0]

def fill_date_after_approve(row):
    if pd.notnull(row['order_approved_at']):
        # Bila order sudah di-approve, isi data kosong dengan formula: order_approved_at + jeda waktu rata-rata sampai ke kurir/pembeli
        if pd.isnull(row['order_delivered_carrier_date']):
            row['order_delivered_carrier_date'] = row['order_approved_at'] + pd.Timedelta(days = days_carrier)
        if pd.isnull(row['order_delivered_customer_date']):
            row['order_delivered_customer_date'] = row['order_approved_at'] + pd.Timedelta(days = days_customer)
    return row

df_list['orders'] = df_list['orders'].apply(fill_date_after_approve, axis = 'columns')

# ============================================
# Eliminasi zip code duplikat
# ============================================

df_list['geolocation'].drop_duplicates(
    subset = 'geolocation_zip_code_prefix',
    keep = 'first',
    inplace = True
)

# ============================================
# ### Pertanyaan 1:
# - Produk apa yang paling banyak diminati? Apa kategori dan harganya?
# ============================================

st.header('Pertanyaan 1')
st.caption('Produk apa yang paling banyak diminati? Apa kategori dan harganya?')

df_q1 = df_list["order_items"]

# Hitung banyak produk dan rata-rata harganya
df_q1 = df_q1.groupby('product_id').agg(
    count = ('product_id', 'count'),
    avg_price = ('price', 'mean')
).reset_index().sort_values('count', ignore_index = True, ascending = False)

df_q1['avg_price'] = df_q1['avg_price'].round() 

# Merge dengan tabel produk untuk melihat kategori produknya
df_q1 = df_q1.merge(
    df_list['products'][['product_id', 'product_category_name']],
    how = 'left',
    on = 'product_id'
)

# Merge dengan tabel translasi kategori produk
df_q1 = df_q1.merge(
    df_list['product_category'],
    how = 'left',
    on = 'product_category_name'
)

# Filter kolom yang diperlukan saja
df_q1 = df_q1[['product_id', 'count', 'avg_price', 'product_category_name_english']]

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

# Gabungkan tabel-tabel dan kolom-kolom yang saling berhubungan terlebih dahulu
df_q3 = df_list['order_items']

# Kalkulasi total harga produk-produk dari tiap order
df_q3 = df_q3.groupby('order_id').agg(
    total_price = ('price', 'sum')
).reset_index()

# Gabungkan dengan tabel customer untuk mendapatkan customer id
df_q3 = df_q3.merge(
    df_list['orders'][['order_id', 'customer_id']],
    how = 'inner',
    on = 'order_id'
)

# Hilangkan order id dan jumlahkan tiap-tiap biaya order sebagai total pembelian customer
df_q3 = df_q3.groupby('customer_id').agg(
    total_spent = ('total_price', 'sum')
).reset_index().sort_values('total_spent', ignore_index = True, ascending = False)

# Dapatkan zip code customer
df_q3 = df_q3.merge(
    df_list['customers'][['customer_id', 'customer_zip_code_prefix', 'customer_city', 'customer_state']],
    how = 'inner',
    on = 'customer_id'
)

# Dapatkan koordinat customer
df_q3 = df_q3.merge(
    df_list['geolocation'][['geolocation_zip_code_prefix', 'geolocation_lat', 'geolocation_lng']],
    how = 'inner',
    left_on = 'customer_zip_code_prefix',
    right_on = 'geolocation_zip_code_prefix'
)

# Simpan customer_zip_code_prefix, buang geolocation_zip_code_prefix
df_q3.drop(columns = ['geolocation_zip_code_prefix'], inplace = True)

# Sort ulang data dari total pembelian terbesar ke terkecil
df_q3 = df_q3.sort_values('total_spent', ignore_index = True, ascending = False)

spent_quant1 = df_q3['total_spent'].quantile(0.25)
spent_quant3 = df_q3['total_spent'].quantile(0.75)

spent_iqr = spent_quant3 - spent_quant1
spent_max = spent_quant3 + (1.5 * spent_iqr)
spent_min = spent_quant1 - (1.5 * spent_iqr)

print(f'Outlier atas: > {spent_max}')
print(f'Outlier bawah: < {spent_min}')

# Histogram
fig = px.histogram(
    df_q3,
    x = 'total_spent',
    title = 'Pengecekan Outlier Melalui Histogram',
    color_discrete_sequence = px.colors.sequential.Emrld,
    range_x = [0, 3000]
)
fig.update_layout(hovermode = 'x')

# Imputasi data berdasarkan nilai min dan max dari rumus IQR sebelumnya
df_q3['total_spent'].mask(df_q3['total_spent'] > spent_max, spent_max, inplace = True)
# df_q3['total_spent'].mask(df_q3['total_spent'] < spent_min, spent_min, inplace = True)

spent_rate = df_q3['total_spent'].quantile([0.33, 0.66])
print(f'Quantile 0.33: {spent_rate.iloc[0]}')
print(f'Quantile 0.66: {spent_rate.iloc[1]}')

def cluster_total_spent(row):
    if row['total_spent'] >= spent_rate.iloc[1]:
        row['spent_rate'] = 'high'
    elif row['total_spent'] >= spent_rate.iloc[0]:
        row['spent_rate'] = 'med'
    else:
        row['spent_rate'] = 'low'
    return row

df_q3 = df_q3.apply(
    cluster_total_spent,
    axis = 'columns'
)

# ==============================
# Sebelum stratified sampling
# ==============================

expected_ratio = df_q3['spent_rate'].value_counts(normalize = True)
print(expected_ratio)
print(f'Length: {len(df_q3)}')
print()

# ==============================
# Proses stratified sampling
# ==============================

df_q3_sample = df_q3.groupby('spent_rate').apply(
    lambda x: x.sample(frac = 0.05, random_state = 4321)
).droplevel(0)

stratified_ratio = df_q3_sample['spent_rate'].value_counts(normalize = True)
print(stratified_ratio)
print(f'Length: {len(df_q3_sample)}')

# ============================================
# Peta
# ============================================

class CircleWithProps(folium.Circle):
    def __init__(
        self,
        location,
        popup = None,
        tooltip = None,
        radius = 50,
        props = None,
        **kwargs
    ):
        super(CircleWithProps, self).__init__(
            location = location,
            popup = popup,
            tooltip = tooltip,
            radius = radius,
            **kwargs
        )

        self.options['props'] = props

# Secara default, warna cluster diberikan berdasarkan banyaknya data/poin pada lokasi
# Untuk memberi warna berdasarkan rata-rata (modus) golongan customer, maka perlu diubah fungsinya

cluster_function = {}
bg_color = {
    'low': 'rgba(198, 74, 53, 0.5)',
    'med': 'rgba(233, 155, 72, 0.5)',
    'high': 'rgba(128, 174, 64, 0.5)'
}

for idx, (key, val) in enumerate(bg_color.items()):
    cluster_function[key] = f'''
        function(cluster) {{
            var markers = cluster.getAllChildMarkers();
            var count = cluster.getChildCount();
            var bg_color = '{val}';

            return L.divIcon({{
                html: '<div style="background-color: ' + bg_color + '"><span><small>' + count + '</small></span></div>',
                className: 'leaflet-marker-icon marker-cluster',
                iconSize: [40, 40]
            }});
        }}
    '''

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

            circle = CircleWithProps(
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

# Tampilkan peta
map = cache_map()

st.markdown('##### Peta Sebaran Domisili Pembeli')
st_folium(map)

df_q3_grouped = df_q3.groupby(['spent_rate', 'customer_state', 'customer_city']).agg(
    customer_count = ('spent_rate', 'count'),
    total_spent = ('total_spent', 'sum')
).reset_index().sort_values(['total_spent', 'customer_count'], ignore_index = True, ascending = False)

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

df_q4 = df_list['order_items'].groupby(['order_id']).agg(
    total_price = ('price', 'sum')
)

df_q4 = df_q4.merge(
    df_list['orders'][['order_id', 'order_purchase_timestamp']],
    how = 'inner',
    on = 'order_id'
)

df_q4['date'] = df_q4['order_purchase_timestamp'].dt.date
df_q4['month'] = df_q4['order_purchase_timestamp'].dt.strftime('%b-%Y')

df_q4 = df_q4.groupby(['month', 'date']).agg(
    total_order = ('order_id', 'count'),
    total_spent = ('total_price', 'sum')
).reset_index().sort_values('total_order', ignore_index = True, ascending = False)

df_q4 = df_q4.merge(
    df_q4.groupby('month').agg(
        total_order_monthly = ('total_order', 'sum'),
        total_spent_monthly = ('total_spent', 'sum')
    ).reset_index(),
    on = 'month'
)

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

st.header('Conclusion')
st.markdown(
'''
- **Pertanyaan 1:** Produk yang paling diminati (3 besar) adalah `aca2eb`, `99a478`, dan `422879`. Masing-masing produk tersebut berharga rata-rata R$ 71, R$ 88, dan R$ 55. Lalu, ketiga produk tersebut juga memiliki kategori yang berbeda, yaitu furniture/decoration, bed/bath/table, dan garden tools
- **Pertanyaan 2:** Kategori produk yang paling diminati adalah `bed/bath/table` dengan persentase 9.87% (11k produk), `health & beauty` dengan persentase 8.58% (9k produk), dan `sports leisure` dengan persentase 7.67% (8k produk)
- **Pertanyaan 3:** Wilayah yang paling menguntungkan adalah `Sao Paulo`, `Rio de Janeiro`, dan `Belo Horizonte`. Lalu, terlihat juga bahwa keuntungan ketiga kota tersebut didominasi oleh customer dengan klasifikasi spent_rate `high` (meskipun jumlah akunnya lebih sedikit daripada akun dengan rate di bawahnya yaitu `low` dan `med`)
- **Pertanyaan 4:** Jumlah pembelian (order) akan cenderung menurun di 3/4 bulan (minggu terakhir bulan), namun pola dan pengaruhnya tidak terlalu signifikan. Terlihat juga bulan November 2017 merupakan bulan yang paling menguntungkan dengan jumlah pembelian sebanyak 7451 buah (R$ 1,010,271)
'''
)

# Untuk menghentikan cycle Streamlit
st.stop()