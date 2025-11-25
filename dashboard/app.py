import streamlit as st
import pandas as pd
import boto3
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import datetime

# --- CONFIG ---
BUCKET_NAME = "crypto-lake-taras-2025-november" # <--- YOUR BUCKET
st.set_page_config(page_title="Crypto Volatility Monitor", layout="wide")

# --- AUTHENTICATION ---
if "aws" in st.secrets:
    s3 = boto3.client('s3',
                      aws_access_key_id=st.secrets["aws"]["aws_access_key_id"],
                      aws_secret_access_key=st.secrets["aws"]["aws_secret_access_key"],
                      region_name=st.secrets["aws"]["aws_default_region"])
else:
    s3 = boto3.client('s3')

@st.cache_data(ttl=60)
def load_data():
    today = datetime.datetime.now()
    yesterday = today - datetime.timedelta(days=1)
    
    prefixes = [
        f"btc_trades_{today.strftime('%Y%m%d')}",
        f"btc_trades_{yesterday.strftime('%Y%m%d')}"
    ]
    
    all_files = []
    paginator = s3.get_paginator('list_objects_v2')

    for prefix in prefixes:
        for page in paginator.paginate(Bucket=BUCKET_NAME, Prefix=prefix):
            if 'Contents' in page:
                all_files.extend(page['Contents'])

    if not all_files:
        return pd.DataFrame()

    # Load last 250 files to ensure we cover the time window
    recent_files = sorted(all_files, key=lambda x: x['LastModified'], reverse=True)[:250]
    
    data_frames = []
    for file in recent_files:
        try:
            obj = s3.get_object(Bucket=BUCKET_NAME, Key=file['Key'])
            df = pd.read_parquet(BytesIO(obj['Body'].read()))
            data_frames.append(df)
        except Exception:
            continue

    if not data_frames:
        return pd.DataFrame()

    final_df = pd.concat(data_frames)
    final_df['time'] = pd.to_datetime(final_df['time'])
    
    # --- FINAL OPTIMIZATION: TIME FILTER ---
    # Only keep the last 4 hours. Everything else is history.
    cutoff_time = pd.Timestamp.now() - pd.Timedelta(hours=4)
    final_df = final_df[final_df['time'] > cutoff_time]
    
    final_df = final_df.sort_values(by='time')
    return final_df

# --- UI ---
st.title("🐋 Real-Time Whale Tracker")
st.markdown("Monitoring BTC/USDT Volatility • **Last 4 Hours Window**")

if st.button("Refresh Data"):
    st.cache_data.clear()

df = load_data()

if not df.empty:
    col1, col2, col3 = st.columns(3)
    col1.metric("Recent Trades", f"{len(df):,}")
    col2.metric("Bitcoin Price", f"${df['price'].iloc[-1]:,.2f}")
    
    # 1. CANDLESTICK CHART (Resampled)
    df_resampled = df.set_index('time').resample('1min').agg({
        'price': ['first', 'max', 'min', 'last'],
        'quantity': 'sum'
    })
    df_resampled.columns = ['open', 'high', 'low', 'close', 'volume']
    df_resampled = df_resampled.dropna()

    st.subheader("Price Action (1-Min Candles)")
    fig_price = go.Figure(data=[go.Candlestick(
        x=df_resampled.index,
        open=df_resampled['open'], high=df_resampled['high'],
        low=df_resampled['low'], close=df_resampled['close']
    )])
    fig_price.update_layout(xaxis_rangeslider_visible=False, height=500)
    st.plotly_chart(fig_price, width='stretch')

    # 2. WHALE BUBBLES (> 0.5 BTC)
    st.subheader("Whale Volume Detection (> 0.5 BTC)")
    whales = df[df['quantity'] > 0.5]
    
    if not whales.empty:
        fig_vol = px.scatter(
            whales, x='time', y='price', size='quantity', 
            color='quantity', color_continuous_scale='RdBu_r',
            title="Institutional Liquidity Events"
        )
        st.plotly_chart(fig_vol, use_container_width=True)
    else:
        st.info("Quiet market. No large whales in the last 4 hours.")

else:
    st.warning("No recent data found. Bot might be sleeping.")