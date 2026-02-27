import requests
from bs4 import BeautifulSoup
import json
import os
import time
import string

# -------- Settings (dynamic paths) --------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))

DATA_DIR = os.path.join(PROJECT_ROOT, "data", "raw", "nhs_medicines")
OUTPUT_FILE = os.path.join(DATA_DIR, "nhs_medicines.json")

os.makedirs(DATA_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def get_medicine_links_for_letter(letter):
    """
    Fetches medicine links for a specific letter from the NHS A-Z index.
    The URL pattern is typically /medicines/ [Letter] is handled via anchors or sub-pages.
    We will try the direct sub-page pattern first: https://www.nhs.uk/medicines/
    """
    # NHS site often groups them like this, or lists all on one page. 
    # Let's try to find the specific A-Z section.
    
    # Strategy: Visit the main medicines page and look for the specific letter section
    # NOTE: NHS recently changed this to be dynamic. 
    # Reliable fallback: Use the specific letter endpoint if it exists, or parse the big list.
    
    url = f"https://www.nhs.uk/medicines/"
    
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        
        links = []
        
        # The new NHS structure usually has a huge list separated by letters.
        # We find the section for the current letter.
        
        # 1. Find the container for this letter (e.g., <h2 id="A">A</h2>)
        letter_header = soup.find("h2", id=letter.upper()) or soup.find("a", {"name": letter.upper()})
        
        if letter_header:
            # The list usually follows the header (e.g., in a <ul> or <div>)
            # We look at the NEXT sibling element which should be the list
            next_element = letter_header.find_next("ul") 
            
            if next_element:
                for a in next_element.find_all("a", href=True):
                    href = a['href']
                    # Ensure it's a medicine link (usually starts with /medicines/)
                    if href.startswith("/medicines/"):
                        full_url = "https://www.nhs.uk" + href
                        links.append({
                            "name": a.get_text(strip=True),
                            "url": full_url
                        })
        
        return links

    except Exception as e:
        print(f"[ERROR] Failed to fetch index for {letter}: {e}")
        return []

def scrape_medicine_details(url):
    """Deep scrapes the medicine page."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code != 200: return ""
        
        soup = BeautifulSoup(r.text, "html.parser")
        main_content = soup.find("main") or soup.find("article")
        if not main_content: return ""

        # Extract meaningful text
        text_parts = []
        
        # Priority Sections
        target_headers = ["About", "Key facts", "Who can take", "Side effects", "How to take"]
        
        # Find all content
        for element in main_content.find_all(['p', 'h2', 'li']):
            text = element.get_text(strip=True)
            # Basic filter to keep it relevant
            if len(text) > 10 and "Crown copyright" not in text:
                text_parts.append(text)
        
        # Limit size to avoid noise (First 2000 chars is usually the best info)
        full_text = " ".join(text_parts)
        return full_text[:3000] 

    except Exception:
        return ""

def main():
    print("------------------------------------------------")
    print("   🏥 NHS MEDICINES SCRAPER V2 (FIXED) 🏥    ")
    print("------------------------------------------------")
    
    all_medicines = []
    
    # 1. Gather Links
    print("\n[PHASE 1] Scanning A-Z Index...")
    
    # We fetch the main page ONCE, then parse it for each letter to save requests
    # But since the function logic is per-letter, we can loop.
    # Actually, for the main NHS page, it loads ALL medicines on one page usually.
    # Let's try parsing the SINGLE main page for ALL letters at once.
    
    url = "https://www.nhs.uk/medicines/"
    print(f"   -> Fetching {url}...")
    r = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(r.text, "html.parser")
    
    # Find all links in the 'AZ-list' or main content
    main_wrapper = soup.find("main")
    if main_wrapper:
        found_links = main_wrapper.find_all("a", href=True)
        print(f"   -> Found {len(found_links)} total links on page. Filtering...")
        
        for a in found_links:
            href = a['href']
            text = a.get_text(strip=True)
            
            # Smart Filter: Must be in /medicines/ folder and not be the index itself
            if href.startswith("/medicines/") and len(text) > 2 and "Medicines A to Z" not in text:
                full_url = "https://www.nhs.uk" + href
                
                # Check duplication
                if not any(m['url'] == full_url for m in all_medicines):
                    all_medicines.append({"name": text, "url": full_url})
    
    print(f"[INFO] Successfully found {len(all_medicines)} unique medicines.")
    
    # 2. Deep Scrape
    print("\n[PHASE 2] Scraping Medicine Details...")
    final_data = []
    
    for idx, item in enumerate(all_medicines):
        print(f"   [{idx+1}/{len(all_medicines)}] Scraping: {item['name']}...")
        
        desc = scrape_medicine_details(item['url'])
        
        if desc:
            final_data.append({
                "entity_type": "medicine",
                "name": item['name'],
                "text": desc,
                "url": item['url'],
                "source": "NHS",
                "embedding_context": f"Medicine: {item['name']}. Usage & Side Effects: {desc[:800]}"
            })
        
        # Save every 10 items
        if (idx+1) % 10 == 0:
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(final_data, f, ensure_ascii=False, indent=2)

    # Final Save
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
        
    print(f"\n[DONE] Saved {len(final_data)} medicines to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()