# -*- coding: utf-8 -*-
"""
Created on Tue May 17 14:32:39 2022

@author: Matheus Guerreiro
"""
import pandas as pd
import numpy as np
import geopandas
import folium
from streamlit_folium import folium_static
from folium.plugins import MarkerCluster
from datetime import datetime
import streamlit as st
import plotly.express as px
(pd.set_option('display.float_format', lambda x: '%.3f' % x))
st.set_page_config(layout='wide')

@st.cache_data
def get_data(path):
    data = pd.read_csv(path)
    return data

@st.cache_data
def get_geofile(url):
    geofile = geopandas.read_file(url)
    return geofile

# Get Data
path = 'kc_house_data.csv'
data = get_data(path)

# Get geodata
url = 'https://opendata.arcgis.com/datasets/83fc2e72903343aabff6de8cb445b81c_2.geojson'
geofile = get_geofile( url )


data['level'] = data['price'].apply(lambda x: 'Level 0' if x < 321950 else
                                                'Level 1' if (x >= 321950) & (x < 450000) else
                                                   'Level 2' if (x >= 450000) and (x < 650000) else 'Level 3' )

data['dormitory_type'] = data['bedrooms'].apply(lambda x: 'studio' if x == 1 else
                                                'apartment' if x == 2 else
                                                   'house' if x == 3 else 'NA' )
                                                   

    
# Adding New Features
data['m2'] = data['sqft_lot15'].apply(lambda x: x * 0.09)
data['price_m2'] = data['price'] / data['m2']

# =============== DATA OVERVIEW =============== #
f_attributes = st.sidebar.multiselect('Enter columns', data.columns)
f_zipcode = st.sidebar.multiselect('Enter zipcode', data['zipcode'].unique())

st.title('Data Overview')
if (f_zipcode != []) & (f_attributes != []):
    data = data.loc[data['zipcode'].isin(f_zipcode), f_attributes]
    
elif (f_zipcode != []) & (f_attributes == []):
    data = data.loc[data['zipcode'].isin(f_zipcode), :]
    
elif (f_zipcode == []) & (f_attributes != []):
    data = data.loc[:, f_attributes]
    
else:
    data = data.copy()
    
    
st.dataframe(data)
    
    
# ------------------- Graphs Side-by-Side -----------------------#
c1, c2 = st.columns((2, 2))
    
# =============== AVERAGE METRICS ===============#
df1 = data[['id', 'zipcode']].groupby('zipcode').count().reset_index()
df2 = data[['price', 'zipcode']].groupby('zipcode').mean().reset_index()
df3 = data[['sqft_living', 'zipcode']].groupby('zipcode').mean().reset_index()
df4 = data[['price_m2', 'zipcode']].groupby('zipcode').mean().reset_index()

# Merge
m1 = pd.merge(df1, df2, on='zipcode', how='inner')
m2 = pd.merge(m1, df3, on='zipcode', how='inner')
df = pd.merge(m2, df4, on='zipcode', how='inner')

# Attributes
c1.header('Average Values')
c1.dataframe(df, height=600)

# =============== DESCRIPTIVE STATISTCS ===============#
# Descriptive Analysis
num_attributes = data.select_dtypes(include=['int64', 'float64'])

# Central Tendency - Mean and Median
media = pd.DataFrame(num_attributes.apply(np.mean, axis=0))
mediana = pd.DataFrame(num_attributes.apply(np.median, axis=0))

# Dispersion - Std Dev, Min, Max
std = pd.DataFrame(num_attributes.apply(np.std, axis=0))
min_ = pd.DataFrame(num_attributes.apply(np.min, axis=0))
max_ = pd.DataFrame(num_attributes.apply(np.max, axis=0))

df1 = pd.concat([min_, max_, media, mediana, std], axis=1).reset_index()
df1.columns = ['Attributes', 'Min', 'Max', 'Mean', 'Median', 'Standard Deviation']

c2.header('Descriptive Analysis')
c2.dataframe(df1, height=600)

# ============================= PORTFOLIO DENSITY ================================== #
st.title('Region Overview')

# Set up columns for layout
c1, c2 = st.columns((2, 2))

# Add some spacing between columns
c1.write("")
c2.write("")

c1.header('Portfolio Density')
df = data.sample(1000, replace=True)

# Base Map - Folium
density_map = folium.Map(location=[data['lat'].mean(), data['long'].mean()], default_zoom_start=15)
marker_cluster = MarkerCluster().add_to(density_map)

for name, row in df.iterrows():
    folium.Marker( [row['lat'], row['long']] , 
    popup='Price US${0} on: {1}. Features: {2} sqft, {3} bedrooms, {4} bathrooms, Year Built {5}'.format(row['price'],
                                                                row['date'],
                                                                row['sqft_living'], 
                                                                row['bedrooms'], 
                                                                row['bathrooms'], 
                                                                row['yr_built'] )).add_to( marker_cluster )

with c1:
    # Add some padding to the map container
    c1.markdown("<style>#map1 { padding-bottom: 10px; }</style>", unsafe_allow_html=True)
    folium_static(density_map)

# Price Map - Folium
c2.header('Price Density')

df = data[['price', 'zipcode']].groupby('zipcode').mean().reset_index()
df.columns = ['ZIP', 'PRICE']

#df = df.sample(10)

geofile = geofile[geofile['ZIP'].isin(df['ZIP'].tolist())]

region_price_map = folium.Map(location=[data['lat'].mean(), data['long'].mean()], default_zoom_start=15)

region_price_map.choropleth(data = df,
                            geo_data = geofile,
                            columns=['ZIP', 'PRICE'],
                            key_on='feature.properties.ZIP',
                            fill_color='YlOrRd',
                            fill_opacity = 0.7,
                            line_opacity = 0.2,
                            legend_name = 'AVG PRICE')

with c2:
    # Add some padding to the map container
    c2.markdown("<style>#map2 { padding-bottom: 10px; }</style>", unsafe_allow_html=True)
    folium_static(region_price_map)
    
# ============================= DISTRIBUTION COMERCIAL REAL STATE ================================== #
st.sidebar.title('Comercial Options')
st.title('Comercial Attributes')

# ========= FILTERS ========== #
min_year_built = int(data['yr_built'].min())
max_year_built = int(data['yr_built'].max())
data['date'] = pd.to_datetime(data['date'])
dates = []
dates.append(data['date'].unique())

st.sidebar.subheader('Select Max Year Built')
f_year_built = st.sidebar.slider('Year Built', min_year_built, max_year_built, min_year_built)

st.header('Average Price per Year Built')

# data selection
df = data.loc[data['yr_built'] < f_year_built]

# Average Price per Year
df = df[['yr_built', 'price']].groupby('yr_built').mean().reset_index()
fig = px.line(df, x='yr_built', y='price', markers=True)
st.plotly_chart(fig, use_container_width=True)


# Average Price per Day
st.header('Average Price per Day')
st.sidebar.subheader('Select Max Date')

#Filters
min_date = datetime.strptime(datetime.strftime(data['date'].min(), '%Y-%m-%d'), '%Y-%m-%d')
max_date = datetime.strptime(datetime.strftime(data['date'].max(), '%Y-%m-%d'), '%Y-%m-%d')
mode_date = datetime.strptime(datetime.strftime(data['date'].mode()[0], '%Y-%m-%d'), '%Y-%m-%d')

st.sidebar.subheader('Select max date')
f_date = st.sidebar.slider('Date', min_date, max_date, mode_date)

# Data Filtering
data['date'] = pd.to_datetime(data['date'])
df = data.loc[data['date'] < f_date]
df = df[['date', 'price']].groupby('date').mean().reset_index()
fig = px.line(df, x='date', y='price')
st.plotly_chart(fig, use_container_width=True)

# ============== HISTOGRAMA ============== #
st.header('Price Distribution')
st.sidebar.subheader('Select Max Price')

# filter
min_price = int(data['price'].min())
max_price = int(data['price'].max())
avg_price = int(data['price'].mean())

# data filtering
f_price = st.sidebar.slider('Price', min_price, max_price, avg_price)
df = data.loc[data['price'] < f_price]

# data plot
fig = px.histogram(df, x='price', nbins=50, text_auto=True)
st.plotly_chart(fig, use_container_width=True)

# =============================== #
# DISTRIBUIÇÃO DOS IMÓVEIS POR CATEGORIAS FÍSICAS
# =============================== #
st.title('House attributes')
c1, c2 = st.columns((1, 1))

st.sidebar.title('House attributes options')

f_bedrooms=st.sidebar.selectbox('Maximum number of bedrooms', np.sort(data['bedrooms'].unique()), index=4)
df = data[data['bedrooms']<=f_bedrooms]
c1.header('# of houses given a maximum of bedrooms')
fig = px.histogram(df, x='bedrooms', nbins=19)
c1.plotly_chart(fig, use_container_width=True)

f_bathrooms=st.sidebar.selectbox('Maximum number of bathrooms', np.sort(data['bathrooms'].unique()), index=2)
df = data[data['bathrooms']<=f_bathrooms]
c1.header('# of houses given a maximum of bathrooms')
fig = px.histogram(data, x='bathrooms', nbins=19)
c1.plotly_chart(fig, use_container_width=True)

f_floors=st.sidebar.selectbox('Maximum number of floors', np.sort(data['floors'].unique()), index=2)
df = data[data['floors']<=f_floors]
c2.header('# of houses given a maximum of floors')
fig = px.histogram(data, x='floors', nbins=19)
c2.plotly_chart(fig, use_container_width=True)

f_waterfront=st.sidebar.selectbox('Maximum number of waterfront', np.sort(data['waterfront'].unique()), index=0)
df = data[data['waterfront']<=f_waterfront]
c2.header('# of houses given a maximum of waterfront')
fig = px.histogram(data, x='waterfront', nbins=19)
c2.plotly_chart(fig, use_container_width=True)