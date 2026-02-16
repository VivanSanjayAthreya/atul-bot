import time
from langchain_community.vectorstores import Qdrant
from qdrant_client import QdrantClient, models
from src import config

# 1. HELPER: Check if a URL exists
def url_exists_in_db(client, url):
    """
    Returns True if the database already contains chunks from this source URL.
    This is a crucial check to prevent duplicates, especially when re-running the pipeline."""
    try:
        result, _ = client.scroll(
            collection_name=config.COLLECTION_NAME,
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="metadata.source",
                        match=models.MatchValue(value=url),
                    )
                ]
            ),
            limit=1
        )
        return len(result) > 0
    except Exception:
        return False

# 2. ENGINE: The Upload Logic
def upload_chunks(chunks, batch_size=10):
    """
    Uploads chunks with robust retry logic.
    """
    # 1. Setup Client
    client = QdrantClient(
        url=config.QDRANT_URL, 
        api_key=config.QDRANT_API_KEY,
        timeout=60 
    )

    # 2. Setup Vector Store (Uses config.get_embeddings() now!)
    vector_store = Qdrant(
        client=client,
        collection_name=config.COLLECTION_NAME,
        embeddings=config.get_embeddings(),
    )

    total_chunks = len(chunks)
    current_index = 0
    
    print(f"🚀 Engine: Uploading {total_chunks} chunks in batches of {batch_size}...")

    # 3. The Smart Loop
    while current_index < total_chunks:
        batch = chunks[current_index : current_index + batch_size]
        
        try:
            vector_store.add_documents(batch)
            current_index += batch_size
            print(f"   Saved {min(current_index, total_chunks)}/{total_chunks} chunks...")
            # (Commented out to reduce noise in the main loop)
            time.sleep(1)
            
        except Exception as e:
            error_msg = str(e).lower()
            
            # HANDLE RATE LIMITS
            if "429" in error_msg or "resource_exhausted" in error_msg or "timed out" in error_msg:
                print(f"   ⏳ Hit Limit/Timeout. Sleeping 60s... (Retrying batch)")
                time.sleep(60)
                # We do NOT increment current_index, so it retries the same batch
            
            # HANDLE CRITICAL ERRORS
            else:
                print(f"   ❌ Critical Error on batch starting at {current_index}: {e}")
                # Skip bad batch to avoid infinite loop
                current_index += batch_size