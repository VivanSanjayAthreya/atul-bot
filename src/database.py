# src/database.py
import time
from langchain_community.vectorstores import Qdrant
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src import config

def ingest_documents(documents):
    if not documents:
        print("⚠️  No documents provided to ingest.")
        return

    print(f"\n🚜 Ingestion Engine started for {len(documents)} documents...")

    # 1. Split Text
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP
    )
    splits = text_splitter.split_documents(documents)
    print(f"   ✂️  Split into {len(splits)} chunks.")

    # 2. Upload in Batches (To avoid hitting API limits)
    batch_size = 50  # Upload 50 chunks at a time
    total_batches = (len(splits) // batch_size) + 1

    print(f"   🚀 Uploading to Qdrant in {total_batches} batches...")

    for i in range(0, len(splits), batch_size):
        batch = splits[i : i + batch_size]
        try:
            Qdrant.from_documents(
                batch,
                config.get_embeddings(),
                url=config.QDRANT_URL,
                api_key=config.QDRANT_API_KEY,
                collection_name=config.COLLECTION_NAME,
                force_recreate=False 
            )
            print(f"      ✅ Batch {i//batch_size + 1}/{total_batches} uploaded.")
            
            # CRITICAL: Sleep for 2 seconds between batches to be nice to Gemini Free Tier
            time.sleep(2) 
            
        except Exception as e:
            print(f"      ❌ Error on batch {i//batch_size + 1}: {e}")
            # If we hit a rate limit, wait longer (60 seconds) and try to continue
            if "429" in str(e):
                print("      ⏳ Hit Rate Limit. Sleeping for 60 seconds...")
                time.sleep(60)

    print("   🎉 Ingestion Complete.")