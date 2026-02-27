import json
import os

# -------- Settings (dynamic paths) --------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))

# Input Files (The 4 Clean Files you just made)
FILES_TO_MERGE = [
    os.path.join(PROJECT_ROOT, "data", "processed", "nhs_conditions_tagged.json"),
    os.path.join(PROJECT_ROOT, "data", "processed", "nhs_medicines_tagged.json"),
    os.path.join(PROJECT_ROOT, "data", "processed", "nhs_symptoms_tagged.json"),
    os.path.join(PROJECT_ROOT, "data", "processed", "mayo_tests_tagged.json")
]

# Output File (JSONL format is faster for loading into Vector DB)
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "data", "processed", "symptoguide_master.jsonl")

def main():
    print("------------------------------------------------")
    print("   🧬 SYMPTOGUIDE DATA MERGER (FINAL) 🧬    ")
    print("------------------------------------------------")
    
    total_entries = 0
    all_data = []

    # 1. Read each file
    for file_path in FILES_TO_MERGE:
        if not os.path.exists(file_path):
            print(f"[ERROR] File not found: {file_path}")
            continue
            
        print(f"[READING] {os.path.basename(file_path)}...")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Validation Check
                if isinstance(data, list):
                    all_data.extend(data)
                    count = len(data)
                    total_entries += count
                    print(f"   -> Added {count} entries.")
                else:
                    print(f"   -> [WARNING] content is not a list. Skipped.")
        except Exception as e:
            print(f"   -> [ERROR] Failed to read: {e}")

    # 2. Save as JSON Lines (.jsonl)
    # JSONL is better because you can read it line-by-line without loading 100MB into RAM.
    print(f"\n[SAVING] Writing {total_entries} entries to Master File...")
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for entry in all_data:
            # We dump each object as a single line
            json_string = json.dumps(entry, ensure_ascii=False)
            f.write(json_string + "\n")

    print(f"\n[SUCCESS] Master Dataset Ready: {OUTPUT_FILE}")
    print("You are now ready to build the Vector Database! 🚀")

if __name__ == "__main__":
    main()