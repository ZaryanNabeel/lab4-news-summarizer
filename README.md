# Lab Assignment 4 - Selenium News Summarizer API

**Registration:** FA23-BDS-039  
**News source:** MIT Technology Review (039 % 20 + 1 = 20)  
**Language:** Python (Selenium + headless Google Chrome + ChromeDriver, Flask/Gunicorn)

## How it works
1. `GET /get?keyword=<kw>` launches headless Chrome via Selenium.
2. Searches technologyreview.com and takes the first article result
   (falls back to a site-restricted DuckDuckGo search if the site search returns nothing).
3. Opens the article, extracts the body text and produces an extractive summary.
4. Returns JSON: `registration, newssource, keyword, url, summary`.

`GET /` shows the registration number.

## Build & run
```bash
docker build -t zaryannabeel/news-summarizer-api:v1 .
docker run -d --name newsapi -p 7000:7000 --shm-size=1g zaryannabeel/news-summarizer-api:v1
curl "http://localhost:7000/get?keyword=artificial%20intelligence"
```

## Push
```bash
docker login -u zaryannabeel
docker push zaryannabeel/news-summarizer-api:v1
```
