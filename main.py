import json
import os
import time
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Qdrant
from qdrant_client import QdrantClient, models
from src import config 

# --- CONFIGURATION ---
JSON_FILE = "cleaned_articles.json" 
BATCH_SIZE = 10  # Reduced from 50 to avoid hitting limits

def main():
    print(f"🚀 PATIENT MODE: Ingesting data from {JSON_FILE}...")

    # 1. LOAD DATA
    if not os.path.exists(JSON_FILE):
        print(f"❌ ERROR: File '{JSON_FILE}' not found.")
        return

    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        articles = json.load(f)

    documents = []
    print(f"   👉 Found {len(articles)} articles. Preparing context...")

    for art in articles:
        enhanced_content = f"Title: {art.get('title', 'Untitled')}\nDate: {art.get('date', '')}\n\n{art.get('content', '')}"
        doc = Document(
            page_content=enhanced_content,
            metadata={"source": art.get('link', ''), "title": art.get('title', ''), "type": "article"}
        )
        documents.append(doc)

    # 2. CHUNK DATA
    print("✂️  Splitting text into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    splits = text_splitter.split_documents(documents)
    print(f"   👉 Created {len(splits)} chunks.")

    # 3. CONNECT TO DB
    print(f"🔌 Connecting to Qdrant...")
    client = QdrantClient(url=config.QDRANT_URL, api_key=config.QDRANT_API_KEY)

    # Check/Create Collection
    if not client.collection_exists(config.COLLECTION_NAME):
        # Detect dimensions first
        try:
            print("   🧪 Testing model dimensions...")
            test_embeddings = config.get_embeddings().embed_query("test")
            vector_size = len(test_embeddings)
            print(f"   📏 Detected Vector Size: {vector_size}")
            
            print(f"   🆕 Creating collection '{config.COLLECTION_NAME}'...")
            client.create_collection(
                collection_name=config.COLLECTION_NAME,
                vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE)
            )
        except Exception as e:
            print(f"   ❌ Failed to initialize DB: {e}")
            return
    else:
        print(f"   ✅ Collection '{config.COLLECTION_NAME}' is ready.")

    vector_store = Qdrant(
        client=client,
        collection_name=config.COLLECTION_NAME,
        embeddings=config.get_embeddings(),
    )

    # 4. SMART RETRY UPLOAD LOOP
    print(f"🚀 Uploading in batches of {BATCH_SIZE}...")
    
    total_chunks = len(splits)
    current_index = 3770
    
    while current_index < total_chunks:
        # Select the batch
        batch = splits[current_index : current_index + BATCH_SIZE]
        
        try:
            vector_store.add_documents(batch)
            
            # SUCCESS: Move the index forward
            current_index += BATCH_SIZE
            progress = min(current_index, total_chunks)
            print(f"      ✅ Progress: {progress}/{total_chunks} chunks saved.")
            
            # Polite pause
            time.sleep(2) 
            
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                print("      ⏳ Hit Speed Limit. Sleeping 60 seconds... (Don't worry, I'll retry)")
                time.sleep(60)
                # We do NOT increment current_index, so it tries the SAME batch again.
            else:
                print(f"      ❌ Critical Error: {e}")
                # Skip bad batch to prevent infinite loop on real errors
                current_index += BATCH_SIZE 

    print("\n🎉 UPLOAD COMPLETE! All data is safely stored.")

if __name__ == "__main__":
    main()