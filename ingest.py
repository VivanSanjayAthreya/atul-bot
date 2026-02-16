import os
import time
from qdrant_client import QdrantClient, models
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.extractors.wordpress_loader import load_cleaned_json
from src.database import upload_chunks, url_exists_in_db
from src.extractors.youtube_loader import load_youtube_json
from src import config

# --- CONFIGURATION ---
ARTICLES_JSON_FILE = os.path.join("data", "cleaned_articles.json")
YOUTUBE_JSON_FILE = os.path.join("data", "youtube_dump.json")

def ensure_database_setup(client):
    """
    Ensures the Qdrant collection has the necessary search index 
    for 'metadata.source'. Without this, filtering will fail.
    """
    print("⚙️  Verifying database structure...")
    try:
        client.create_payload_index(
            collection_name=config.COLLECTION_NAME,
            field_name="metadata.source",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )
        # Give the server a moment to register the change
        time.sleep(1)
    except Exception:
        # If it already exists, it might throw a harmless error, which we ignore
        pass

def run_pipeline():
    print("🤖 STARTING SMART INGESTION...")
    print("-" * 50)
    
    # 1. Setup Client
    client = QdrantClient(url=config.QDRANT_URL, api_key=config.QDRANT_API_KEY)
    ensure_database_setup(client)
    
    all_docs = []

    # 2. Load Articles
    if os.path.exists(ARTICLES_JSON_FILE):
        print(f"📄 Checking {ARTICLES_JSON_FILE}...")
        article_docs = load_cleaned_json(ARTICLES_JSON_FILE)
        if article_docs:
            print(f"   👉 Found {len(article_docs)} articles.")
            all_docs.extend(article_docs)
    else:
        print(f"⚠️  File not found: {ARTICLES_JSON_FILE} (Skipping articles)")

    # 3. Load YouTube
    if os.path.exists(YOUTUBE_JSON_FILE):
        print(f"🎥 Checking {YOUTUBE_JSON_FILE}...")
        yt_docs = load_youtube_json(YOUTUBE_JSON_FILE)
        if yt_docs:
            print(f"   👉 Found {len(yt_docs)} videos.")
            all_docs.extend(yt_docs)
    else:
        print(f"⚠️  File not found: {YOUTUBE_JSON_FILE} (Skipping YouTube)")

    if not all_docs:
        print("\n❌ No documents found from ANY source. Exiting.")
        return

    print(f"\n🔍 Processing {len(all_docs)} total items one by one...")
    
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    new_items_count = 0
    skipped_count = 0

    # 4. THE SMART LOOP
    for i, doc in enumerate(all_docs):
        # We use 'source' because that's where we stored the URL
        link = doc.metadata.get("source", "Unknown URL")
        
        # A. CHECK (Idempotency)
        if link and url_exists_in_db(client, link):
            # print(f"   [Skip] Already exists: {link}") 
            skipped_count += 1
            continue
            
        # B. SPLIT (Only if it's new!)
        print(f"   [NEW] Processing: {link}")
        chunks = splitter.split_documents([doc])
        
        # C. UPLOAD
        if chunks:
            upload_chunks(chunks)
            new_items_count += 1

    print("-" * 50)
    print(f"🎉 DONE!")
    print(f"   - Skipped: {skipped_count} (Already in DB)")
    print(f"   - Uploaded: {new_items_count} new items")

if __name__ == "__main__":
    run_pipeline()