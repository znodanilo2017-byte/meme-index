# 1. Lightweight, fast Python base image
FROM python:3.11-slim

# 2. Don't buffer logs (EC2 shows prints instantly)
ENV PYTHONUNBUFFERED=1

# 3. Create working directory
WORKDIR /app

# 4. Install system deps (needed for pyarrow)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# 5. Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy your bot code
COPY main.py .

# 7. Start the bot
CMD ["python", "main.py"]

