import json
import websocket
import datetime
import pandas as pd
import boto3
import requests  # <--- NEW LIBRARY
import time # <--- Added time for sleep
import os
from io import BytesIO

# --- CONFIGURATION ---
SOCKET = "wss://stream.binance.com:9443/ws/btcusdt@trade"
BUCKET_NAME = "crypto-lake-taras-2025-november" # <--- CHECK THIS IS CORRECT

# --- TELEGRAM CONFIG ---
# Securely load from environment, or crash if missing
try:
    TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
    TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
except KeyError as e:
    print(f"❌ Error: Missing environment variable {e}")
    exit(1)

WHALE_THRESHOLD = 1.0

# Global variables
batch_data = []
last_upload_time = datetime.datetime.now()
s3_client = boto3.client('s3')

def send_telegram_alert(trade):
    """Sends a message to your phone"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    side = "🟢 BUY" if trade['buyer_maker'] == False else "🔴 SELL"
    message = (
        f"🚨 <b>WHALE ALERT</b> 🚨\n\n"
        f"{side} <b>{trade['quantity']:.4f} BTC</b>\n"
        f"Price: ${trade['price']:,.2f}\n"
        f"Value: ${trade['quantity'] * trade['price']:,.0f}\n"
        f"Time: {trade['time']}"
    )
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=5) # Added timeout
    except Exception as e:
        print(f"Failed to send alert: {e}")

def upload_to_s3(df):
    """Writes to S3"""
    try:
        filename = f"btc_trades_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.parquet"
        out_buffer = BytesIO()
        df.to_parquet(out_buffer, index=False)
        s3_client.put_object(Bucket=BUCKET_NAME, Key=filename, Body=out_buffer.getvalue())
        print(f"✅ Uploaded {len(df)} trades to S3")
    except Exception as e:
        print(f"❌ Upload Failed: {e}")

def on_message(ws, message):
    global batch_data, last_upload_time
    try:
        data = json.loads(message)
        trade = {
            'time': datetime.datetime.fromtimestamp(data['T'] / 1000),
            'price': float(data['p']),
            'quantity': float(data['q']),
            'buyer_maker': data['m']
        }
        
        if trade['quantity'] >= WHALE_THRESHOLD:
            send_telegram_alert(trade)

        batch_data.append(trade)
        
        # Check Upload Timer
        if (datetime.datetime.now() - last_upload_time).seconds >= 60:
            if len(batch_data) > 0:
                df = pd.DataFrame(batch_data)
                upload_to_s3(df)
                batch_data = []
                last_upload_time = datetime.datetime.now()
    except Exception as e:
        print(f"Error processing message: {e}")

def on_error(ws, error):
    print(f"⚠️ Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print(">>> Connection Closed")

def on_open(ws):
    print(">>> Connected. Listening for Whales...")

# --- THE IMMORTAL LOOP ---
if __name__ == "__main__":
    while True:
        try:
            ws = websocket.WebSocketApp(
                SOCKET, 
                on_open=on_open, 
                on_message=on_message, 
                on_error=on_error, 
                on_close=on_close
            )
            # ping_interval=60: Send a heartbeat every 60s to check if Binance is alive
            # ping_timeout=10: If Binance doesn't reply in 10s, kill connection so we can reconnect
            ws.run_forever(ping_interval=60, ping_timeout=10)
        except Exception as e:
            print(f"Crash detected: {e}")
        
        print("Reconnecting in 5 seconds...")
        time.sleep(5)