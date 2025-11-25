import streamlit as st
import pandas as pd
import boto3
import plotly.express as px
from io import BytesIO
import datetime

# --- CONFIG ---
BUCKET_NAME = "crypto-lake-taras-2025-november" # <--- YOUR BUCKET NAME
st.set_page_config(page_title="Crypto Volatility Monitor", layout="wide")

# --- AUTHENTICATION ---
# Check if we are in the Cloud (Streamlit Secrets exist) or on Laptop
if "aws" in st.secrets:
    # We are on Streamlit Cloud -> Use the secrets you pasted
    s3 = boto3.client('s3',
                      aws_access_key_id=st.secrets["aws"]["aws_access_key_id"],
                      aws_secret_access_key=st.secrets["aws"]["aws_secret_access_key"],
                      region_name=st.secrets["aws"]["aws_default_region"])
else:
    # We are on Laptop -> Use local ~/.aws/credentials automatically
    s3 = boto3.client('s3')

@st.cache_data(ttl=60) # Cache data for 60 seconds to save S3 costs/speed
def load_data():
    """Fetches data for Today AND Yesterday using Pagination (Fixes 1000 file limit)."""
    
    # 1. Calculate Date Prefixes (Today and Yesterday)
    # This prevents us from scanning the whole bucket (40MB+), saving cost/time.
    today = datetime.datetime.now()
    yesterday = today - datetime.timedelta(days=1)
    
    prefixes = [
        f"btc_trades_{today.strftime('%Y%m%d')}",      # e.g., btc_trades_20251125
        f"btc_trades_{yesterday.strftime('%Y%m%d')}"   # e.g., btc_trades_20251124
    ]
    
    all_files = []
    paginator = s3.get_paginator('list_objects_v2')

    # 2. Fetch ALL files for these days (Paginator handles the >1000 limit)
    for prefix in prefixes:
        for page in paginator.paginate(Bucket=BUCKET_NAME, Prefix=prefix):
            if 'Contents' in page:
                all_files.extend(page['Contents'])

    if not all_files:
        return pd.DataFrame()

    # 3. Sort by time and take the last 200 files (To keep the dashboard fast)
    # We don't need to download 3,000 files to show a "Real-time" chart.
    recent_files = sorted(all_files, key=lambda x: x['LastModified'], reverse=True)[:200]
    
    # 4. Download actual data
    data_frames = []
    for file in recent_files:
        try:
            obj = s3.get_object(Bucket=BUCKET_NAME, Key=file['Key'])
            df = pd.read_parquet(BytesIO(obj['Body'].read()))
            data_frames.append(df)
        except Exception as e:
            print(f"Error reading {file['Key']}: {e}")

    if not data_frames:
        return pd.DataFrame()

    # 5. Merge
    final_df = pd.concat(data_frames)
    final_df['time'] = pd.to_datetime(final_df['time'])
    final_df = final_df.sort_values(by='time')
    
    return final_df

# --- THE UI ---
st.title("🐋 Real-Time Whale Tracker")
st.markdown(f"**Data Source:** AWS S3 Data Lake ({BUCKET_NAME})")

if st.button("Refresh Data"):
    st.cache_data.clear()

# Load Data
df = load_data()

if not df.empty:
    # Convert time to datetime
    df['time'] = pd.to_datetime(df['time'])
    df = df.sort_values(by='time')
    
    # KPI Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Trades Tracked", len(df))
    col2.metric("Bitcoin Price", f"${df['price'].iloc[-1]:,.2f}")
    col3.metric("Max Trade Size", f"{df['quantity'].max():.4f} BTC")

    # --- CHART 1: Price History ---
    st.subheader("Bitcoin Price Action")
    fig_price = px.line(df, x='time', y='price', title='BTC/USDT Real-Time Feed')
    st.plotly_chart(fig_price, width='stretch')

    # --- CHART 2: Whale Detector (Scatter Plot) ---
    st.subheader("Whale Volume Detection")
    # Filter for trades larger than 0.05 BTC
    whales = df[df['quantity'] > 0.05]
    
    if not whales.empty:
        fig_vol = px.scatter(
            whales, 
            x='time', 
            y='price', 
            size='quantity', 
            color='quantity',
            hover_data=['quantity', 'buyer_maker'],
            title='Large Trades (>0.05 BTC)'
        )
        st.plotly_chart(fig_vol, use_container_width=True)
    else:
        st.info("No whales detected in the last few minutes.")

    # --- RAW DATA TABLE ---
    with st.expander("View Raw Data (Parquet Stream)"):
        st.dataframe(df.sort_values(by='time', ascending=False))

else:
    st.warning("No data found in S3 yet. Is the bot running?")