import json
import re
import os

# --- CONFIGURATION ---
INPUT_FILE = "scraped_articles_final.json"
OUTPUT_FILE = "cleaned_articles.json"

def clean_text_logic(text):
    """
    The Master Cleaning Logic.
    Edit this function to change how text is cleaned.
    """
    if not text:
        return ""

    # 1. Remove Phone Numbers (Aggressive Pattern)
    # Matches +91..., 98450..., 94444-44444
    text = re.sub(r'(?:\+91|91)?[\s-]?\d{5}[\s-]?\d{5}', '', text)
    
    # 2. Remove Zoom/Meeting IDs
    text = re.sub(r'(?i)(meeting\s?id|passcode|zoom)\s?[:\-]?\s?\d+', '', text)
    
    # 3. Remove URLs inside the text
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
    
    # 4. Remove Specific "Noise Phrases"
    noise_phrases = [
        "Please note that this article has both the Tamil version",
        "written by Sri APN Swami",
        "translation done by his sishyas",
        "Watch this upanyasam Live",
        "FreeConferenceCall App",
        "Contact details to purchase",
        "WhatsApp Contact",
        "Download and Read",
        "Global Stotra Parayana Kainkaryam"
    ]
    
    for phrase in noise_phrases:
        text = text.replace(phrase, "")

    # 5. Fix formatting (remove massive gaps created by deletions)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    return text.strip()

def main():
    print(f"🧹 Starting Data Cleaning Process...")
    
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Error: Input file '{INPUT_FILE}' not found.")
        return

    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
            
        print(f"   👉 Loaded {len(raw_data)} raw articles.")
        
        cleaned_data = []
        skipped_count = 0
        
        for entry in raw_data:
            original_content = entry.get('content', '')
            
            # Run the cleaning logic
            clean_content = clean_text_logic(original_content)
            
            # Filter: If the article is too short after cleaning, drop it.
            if len(clean_content) < 50:
                skipped_count += 1
                continue
                
            # Create a new clean entry (keeping metadata)
            new_entry = {
                "title": entry.get('title'),
                "link": entry.get('link'),
                "date": entry.get('date'),
                "content": clean_content
            }
            cleaned_data.append(new_entry)

        # Save the new file
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, indent=4, ensure_ascii=False)
            
        print(f"   ✅ Cleaning Complete!")
        print(f"   🗑️  Dropped {skipped_count} empty/junk articles.")
        print(f"   Qw  Saved {len(cleaned_data)} high-quality articles to '{OUTPUT_FILE}'")

    except Exception as e:
        print(f"❌ Critical Error: {e}")

if __name__ == "__main__":
    main()