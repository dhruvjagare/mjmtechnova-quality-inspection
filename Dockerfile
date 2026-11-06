# Lightweight official Python image
FROM python:3.11-slim

# System tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY python_vs/ /app/python_vs/
COPY frontend/dist/ /app/frontend/dist/

WORKDIR /app/python_vs

# Render uses port 10000 by default, or the PORT environment variable
ENV PORT=10000
EXPOSE 10000

CMD ["sh", "-c", "uvicorn api:app --host 0.0.0.0 --port ${PORT:-10000}"]
