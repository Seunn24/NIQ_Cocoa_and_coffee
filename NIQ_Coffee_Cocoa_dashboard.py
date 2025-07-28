import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(
    page_title="🌱 Cocoa & Coffee Dashboard",
    layout="wide",
)
st.title("🌱 Cocoa & Coffee Products Dashboard")

@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    return pd.read_excel(path)

df = load_data('NIQ_coffee_cocoa.xlsx')

# ──────────────────────────────────────────────────────────────────────────────
# CLEAN & PREP
# ──────────────────────────────────────────────────────────────────────────────
df['commodity_code'] = df['commodity_code'].astype(str).str.strip()

commodities = ["0901","1801 00","1803 00","1804 00","1805 10","1806"]

df['commodity_code'] = pd.Categorical(
    df['commodity_code'],
    categories=commodities,
    ordered=True,
)

coffee_codes = df[df['commodity_code']=="0901"]['Subscriber Code'].unique().tolist()
cocoa_codes = df[df['commodity_code']=="1806"]['Subscriber Code'].unique().tolist()
own_label_codes = coffee_codes + cocoa_codes

df['label_type'] = np.where(
    df['Subscriber Code'].isin(own_label_codes),
    'Own-label',
    'Branded'
)

df['scope'] = np.where(
    df['commodity_code'].notna(),
    'In scope',
    'Not in scope'
)

df['ingredients_clean'] = (
    df['Ingredients'].fillna('').astype(str).str.lower()
)
df['potential'] = df['ingredients_clean'].str.contains('coffee|cocoa', na=False)

df['scope2'] = np.where(
    df['commodity_code'].notna(),
    'In-scope',
    np.where(df['potential'],
             'Potentially-in-scope',
             'Out-of-scope')
)

# ──────────────────────────────────────────────────────────────────────────────
# CHART 1 – TREEMAP: Scope - Label-Type
# ──────────────────────────────────────────────────────────────────────────────
treemap_df = (
    df.groupby(['scope','label_type'])
      .size()
      .reset_index(name='count')
)
fig1 = px.treemap(
    treemap_df,
    path=['scope','label_type'],
    values='count',
    title='Overall Scope & Label-Type Breakdown'
)
st.plotly_chart(fig1, use_container_width=True)

# ──────────────────────────────────────────────────────────────────────────────
# CHART 2 – STACKED BAR: Branded vs Own-label by Commodity
# ──────────────────────────────────────────────────────────────────────────────
stacked_df = (
    df[df['scope']=='In scope']
      .groupby(['label_type','commodity_code'])
      .size()
      .reset_index(name='count')
)
fig2 = px.bar(
    stacked_df,
    x='label_type',
    y='count',
    color='commodity_code',
    title='In-Scope Commodities by Label-Type',
    barmode='stack',
)
st.plotly_chart(fig2, use_container_width=True)

# ──────────────────────────────────────────────────────────────────────────────
# CHART 3 – CLUSTER BAR: 7 HS Codes × In-scope vs Potentially-in-scope
# ──────────────────────────────────────────────────────────────────────────────
cluster_df = (
    df[df['commodity_code'].isin(commodities)]
      .groupby(['commodity_code','scope2'])
      .size()
      .reset_index(name='count')
)
fig3 = px.bar(
    cluster_df,
    x='commodity_code',
    y='count',
    color='scope2',
    category_orders={'commodity_code': commodities},  
    title='Commodity Scope Status',
    barmode='group',
)
# force discrete axis
fig3.update_xaxes(type='category')
st.plotly_chart(fig3, use_container_width=True)

# ──────────────────────────────────────────────────────────────────────────────
# CHART 4 – STACKED BAR: 7 HS Codes × Branded vs Own-label
# ──────────────────────────────────────────────────────────────────────────────
stacked5_df = (
    df[df['commodity_code'].isin(commodities)]
      .groupby(['commodity_code','label_type'])
      .size()
      .reset_index(name='count')
)
fig5 = px.bar(
    stacked5_df,
    x='commodity_code',
    y='count',
    color='label_type',
    category_orders={'commodity_code': commodities},
    title='Commodities by Label-Type',
    barmode='stack',
)
fig5.update_xaxes(type='category')
st.plotly_chart(fig5, use_container_width=True)
