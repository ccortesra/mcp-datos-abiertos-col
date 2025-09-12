FROM python:3.12-slim-bookworm

# Install system dependencies for Chrome and Selenium
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/chromedriver /usr/local/bin/chromedriver \
    && chmod +x /usr/bin/chromedriver

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY main.py /app/
COPY scraping.py /app/
COPY pyproject.toml /app/

# Set environment variables
ENV PYTHONPATH=/app
ENV HEADLESS_MODE=true

# Run the MCP server
ENTRYPOINT ["python", "main.py"]