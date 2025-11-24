# 🐳 Real-Time Crypto Volatility Pipeline

### *End-to-End MLOps Pipeline on AWS*

**Live Dashboard:** [Streamlit App](https://meme-index.streamlit.app)

---

## 🚀 The Project
This system captures high-frequency cryptocurrency trade data, detects large-volume (“Whale”) anomalies, and visualizes market microstructure in real time.

Unlike static analysis, the pipeline runs 24/7 in the cloud, streaming live WebSocket data and persisting it for historical analytics.

---

## 🏗️ Architecture Overview
* **Ingestion:** Python WebSocket client listening to Binance live trade feed  
* **Containerization:** Docker (Multi-arch build for ARM/AMD64)  
* **Compute:** AWS EC2 (t3.micro) running Docker in detached mode  
* **Infrastructure as Code:** Terraform (EC2, Security Groups, IAM Roles)  
* **Storage / Data Lake:** AWS S3 (Parquet format)  
* **Frontend / Dashboard:** Streamlit + Plotly (CI/CD via GitHub)

---

## 🏗️ Architecture Diagram

![Real-Time Crypto Volatility Pipeline](./diagram_meme_index.png)

---

## 🛠️ Tech Stack
| Component | Technology |
| :--- | :--- |
| **Cloud Provider** | AWS (eu-central-1) |
| **IaC** | Terraform |
| **Container** | Docker (Multi-arch build for ARM/AMD64) |
| **Language** | Python 3.11 |
| **Libraries** | `boto3`, `pandas`, `streamlit`, `websocket-client`, `plotly`, `fastparquet` |
| **Frontend / Dashboard** | Streamlit + Plotly |
| **Data Storage** | AWS S3 (Parquet format) |

---

## 📸 Visuals

![Header](./AppHeader.png)
![Price Dashboard](./BitcoinPriceDashboard.png)
![Whale Detector](./WhaleDetector.png)
![Historical Charts](./HistoricalCharts.png)

---

## 🔧 How to Run Locally
1. Clone the repo  
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
3. streamlit run app.py

---
*Built by Danylo Yuzefchyk - Infrastructure & Data Engineer*