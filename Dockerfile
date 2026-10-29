FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CHROME_BIN=/usr/bin/google-chrome \
    CHROMEDRIVER_PATH=/usr/local/bin/chromedriver

# Google Chrome + matching ChromeDriver (Chrome for Testing)
RUN apt-get update \
 && apt-get install -y --no-install-recommends wget curl unzip ca-certificates gnupg \
 && wget -q -O /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
 && apt-get install -y --no-install-recommends /tmp/chrome.deb \
 && CHROME_VERSION=$(google-chrome --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+') \
 && CHROME_MAJOR=${CHROME_VERSION%%.*} \
 && DRIVER_VERSION=$(curl -fsSL https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_${CHROME_MAJOR} || echo ${CHROME_VERSION}) \
 && wget -q -O /tmp/chromedriver.zip https://storage.googleapis.com/chrome-for-testing-public/${DRIVER_VERSION}/linux64/chromedriver-linux64.zip \
 && unzip -q /tmp/chromedriver.zip -d /tmp \
 && mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver \
 && chmod +x /usr/local/bin/chromedriver \
 && echo "Chrome ${CHROME_VERSION} / ChromeDriver ${DRIVER_VERSION}" \
 && rm -rf /tmp/* /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py scraper.py summarizer.py ./

RUN useradd -m appuser
USER appuser

EXPOSE 7000

# API starts automatically when the container runs
CMD ["gunicorn", "--bind", "0.0.0.0:7000", "--workers", "1", "--threads", "4", "--timeout", "180", "app:app"]
