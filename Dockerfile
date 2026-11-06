# Use official Python lightweight image
FROM python:3.11-slim

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set up a new user 'user' with UID 1000 for Hugging Face Spaces security
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1

WORKDIR $HOME/app

# Install Python requirements
COPY --chown=user:user python_vs/requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt fastapi uvicorn python-multipart

# Copy backend files and dataset
COPY --chown=user:user python_vs/ $HOME/app/python_vs/

# Copy built React frontend files
COPY --chown=user:user frontend/dist/ $HOME/app/frontend/dist/

WORKDIR $HOME/app/python_vs

# Hugging Face Spaces uses port 7860
EXPOSE 7860

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "7860"]
