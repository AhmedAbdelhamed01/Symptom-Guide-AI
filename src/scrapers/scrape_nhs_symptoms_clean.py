import requests
from bs4 import BeautifulSoup
import json
import os
import time

# -------- Settings (dynamic paths) --------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))

DATA_DIR = os.path.join(PROJECT_ROOT, "data", "raw", "nhs_symptoms")
OUTPUT_FILE = os.path.join(DATA_DIR, "nhs_symptoms_clean.json")

os.makedirs(DATA_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def get_clean_symptom_links():
    """Fetches the index but filters out the garbage A-Z links."""
    url = "https://www.nhs.uk/symptoms/"
    print(f"[INFO] Scanning Index: {url}")
    
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        
        real_links = []
        seen_urls = set()
        
        # The main list is usually in a container
        main_content = soup.find("main") or soup.find("body")
        
        for a in main_content.find_all("a", href=True):
            href = a['href']
            text = a.get_text(strip=True)
            
            # 1. FILTER: Must look like a content page
            # Good: "/symptoms/cough/" or "/conditions/stomach-ache/" (sometimes they link to conditions)
            # Bad: "#a", "#b" (These are just the alphabet buttons)
            if "#" in href:
                continue
                
            if href.startswith("/symptoms/") or href.startswith("/conditions/"):
                full_url = "https://www.nhs.uk" + href
                
                # 2. FILTER: Junk Text
                if "Symptoms A to Z" in text or len(text) < 3:
                    continue
                
                if full_url not in seen_urls:
                    seen_urls.add(full_url)
                    real_links.append({"name": text, "url": full_url})
        
        return real_links

    except Exception as e:
        print(f"[ERROR] Index failed: {e}")
        return []

def scrape_page_content(url):
    """Extracts the 'Check if you have...' and 'What to do' sections."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        
        main_content = soup.find("main") or soup.find("article")
        if not main_content: return ""

        text_parts = []
        
        # Grab headers (h2) and paragraphs/lists (p, ul)
        # NHS usually structures symptoms with "Check if you have..."
        for tag in main_content.find_all(['h2', 'p', 'li']):
            text = tag.get_text(strip=True)
            
            # Clean common junk
            junk_phrases = ["Crown copyright", "Page last reviewed", "Back to top", "Cookies"]
            if any(junk in text for junk in junk_phrases):
                continue
                
            if len(text) > 10:
                # Add a marker for headers to help the AI understand structure
                if tag.name == "h2":
                    text_parts.append(f"\n## {text}")
                else:
                    text_parts.append(text)
        
        return "\n".join(text_parts)

    except:
        return ""

def main():
    print("---------------------------------------------")
    print("   🏥 NHS SYMPTOMS SCRAPER (CLEANER) 🏥    ")
    print("---------------------------------------------")
    
    # 1. Get Links
    links = get_clean_symptom_links()
    print(f"[INFO] Found {len(links)} actual symptom pages.")
    
    # 2. Deep Scrape
    final_data = []
    
    for idx, item in enumerate(links):
        print(f"   [{idx+1}/{len(links)}] Scraping: {item['name']}...")
        
        content = scrape_page_content(item['url'])
        
        if len(content) > 100: # Only save if we got real text
            final_data.append({
                "entity_type": "symptom_guide", # Distinct tag for these useful guides
                "name": item['name'],
                "text": content,
                "url": item['url'],
                "source": "NHS",
                "embedding_context": f"Symptom Guide for {item['name']}: {content[:500]}"
            })
        
        time.sleep(0.5) # Be polite
        
        # Save often
        if idx % 10 == 0:
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(final_data, f, ensure_ascii=False, indent=2)

    # Final Save
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n[DONE] Saved {len(final_data)} clean symptom guides to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()