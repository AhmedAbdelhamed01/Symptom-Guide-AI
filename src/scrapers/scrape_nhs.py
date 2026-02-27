# File: scripts/scraping/scrape_nhs.py

import requests
from bs4 import BeautifulSoup
import json
import os
import time
from urllib.parse import urljoin

# -------- إعدادات المشروع --------
BASE_URL = "https://www.nhs.uk/conditions/"
DATA_DIR = "data/raw/nhs"
os.makedirs(DATA_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/115.0.0.0 Safari/537.36"
}

# -------- دوال مساعدة --------
def save_json(data, filename):
    """احفظ JSON"""
    path = os.path.join(DATA_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def scrape_page(url):
    """سحب محتوى صفحة وتحويلها لنصوص"""
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # عنوان الصفحة
        title = soup.find("h1")
        title_text = title.get_text(strip=True) if title else ""

        # محتوى نصي رئيسي
        content_div = soup.find("div", class_="nhsuk-u-body-copy") or soup
        paragraphs = [p.get_text(strip=True) for p in content_div.find_all("p")]

        return {
            "url": url,
            "title": title_text,
            "content": "\n".join(paragraphs)
        }
    except Exception as e:
        print(f"[ERROR] Failed {url}: {e}")
        return None

def get_all_conditions_links():
    """سحب كل الروابط من صفحة conditions"""
    try:
        r = requests.get(BASE_URL, headers=HEADERS, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        links = []

        for a in soup.find_all("a", href=True):
            href = a['href']
            # روابط داخلية فقط
            if href.startswith("/conditions/") and href != "/conditions/":
                full_url = urljoin(BASE_URL, href)
                if full_url not in links:
                    links.append(full_url)
        return links
    except Exception as e:
        print(f"[ERROR] Could not fetch condition links: {e}")
        return []

# -------- Main Scraper --------
def main():
    condition_links = get_all_conditions_links()
    print(f"[INFO] Found {len(condition_links)} conditions")

    all_data = []
    for idx, url in enumerate(condition_links, start=1):
        print(f"[INFO] Scraping {idx}/{len(condition_links)}: {url}")
        data = scrape_page(url)
        if data:
            all_data.append(data)
        time.sleep(1)  # احترام قواعد الموقع

    # حفظ كل البيانات مرة واحدة
    save_json(all_data, "nhs_conditions.json")
    print("[INFO] Scraping finished. Data saved in 'data/raw/nhs/nhs_conditions.json'")

if __name__ == "__main__":
    main()
