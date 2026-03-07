# ============================================================
# Hugging Face Spaces — Dockerfile
# Gemini + HarfBuzz (Playwright/Chromium) pipeline
# ============================================================

FROM python:3.10-slim

# Install system dependencies required by Chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Chromium system libraries
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxext6 \
    # Font support (needed for Sinhala Unicode rendering)
    fonts-noto \
    fonts-noto-cjk \
    # Utilities
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Ensure Python output is unbuffered so logs are visible in HF Spaces
ENV PYTHONUNBUFFERED=1

# Install Python dependencies first (layer caching)
COPY requirements_hf.txt .
RUN pip install --no-cache-dir -r requirements_hf.txt

# Install Playwright Chromium browser
RUN playwright install chromium
# Note: system deps already installed above via apt-get, no need for 'playwright install-deps'

# Copy project files
COPY . .

# Create output directories
RUN mkdir -p final_posters generated_backgrounds generated_images fonts

# Hugging Face Spaces uses port 7860
EXPOSE 7860

# Start FastAPI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
