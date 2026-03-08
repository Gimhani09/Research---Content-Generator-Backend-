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
    # Font support (Noto covers Sinhala, Latin, and most Unicode blocks)
    fonts-noto \
    # Utilities
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Ensure Python output is unbuffered so logs are visible in HF Spaces
ENV PYTHONUNBUFFERED=1

# Install Python dependencies first (layer caching) with retry
COPY requirements_hf.txt .
RUN pip install --no-cache-dir -r requirements_hf.txt || \
    (sleep 5 && pip install --no-cache-dir -r requirements_hf.txt) || \
    (sleep 10 && pip install --no-cache-dir -r requirements_hf.txt)

# Install Playwright Chromium browser with retry
RUN playwright install chromium || \
    (sleep 5 && playwright install chromium) || \
    (sleep 10 && playwright install chromium)

# Copy project files
COPY . .

# Create output directories and download Google Fonts
RUN mkdir -p final_posters generated_backgrounds generated_images fonts && \
    wget -q -O fonts/AbhayaLibre-ExtraBold.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/abhayalibre/AbhayaLibre-ExtraBold.ttf" && \
    wget -q -O fonts/AbhayaLibre-Bold.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/abhayalibre/AbhayaLibre-Bold.ttf" && \
    wget -q -O "fonts/GemunuLibre[wght].ttf" "https://raw.githubusercontent.com/google/fonts/main/ofl/gemunulibre/GemunuLibre%5Bwght%5D.ttf" && \
    wget -q -O "fonts/NotoSansSinhala-VariableFont_wdth,wght.ttf" "https://raw.githubusercontent.com/google/fonts/main/ofl/notosanssinhala/NotoSansSinhala%5Bwdth%2Cwght%5D.ttf" && \
    echo "Fonts downloaded successfully" || echo "Font download failed (will fallback to CDN)"

# Hugging Face Spaces uses port 7860
EXPOSE 7860

# Start FastAPI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
