# Use Python 3.11 slim image as base for smaller image size.
FROM python:3.11-slim

# Prevent Python from writing .pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Ensure output is flushed immediately (useful for logs).
ENV PYTHONUNBUFFERED=1

# Set Flask and port environment variables.
ENV FLASK_APP=src.app
ENV PORT=5001

# Install Chromium + dependencies.
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    fonts-liberation \
    libnss3 \
    libxss1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libgbm1 \
    libu2f-udev \
    xdg-utils \
    ca-certificates \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Verify that Chromium and Chromedriver are installed by printing their versions.
RUN chromium --version && chromedriver --version

# Set Chrome/Chromium environment variables for Selenium.
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver
ENV DISPLAY=:99

# Create working directory inside container.
WORKDIR /app

# Install dependencies first (for Docker layer caching).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install gunicorn for production WSGI serving.
RUN pip install --no-cache-dir gunicorn

# Copy application code into the container.
COPY . .

# Port used by the Flask application.
EXPOSE ${PORT}

# Run the Flask app with gunicorn for production.
# Workers=1 for concurrent requests; threads=1 for Selenium threads.
# Only use 1 worker and 1 thread to not exceed the memory limit of the free tier on Render.
CMD ["sh","-c","exec gunicorn --bind 0.0.0.0:${PORT} --workers 1 --threads 1 --timeout 120 ${FLASK_APP}:app"]