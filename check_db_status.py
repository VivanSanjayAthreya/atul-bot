from qdrant_client import QdrantClient
from src import config

def inspect_brain():
    print("🧠 Connecting to the Srivaishnava Knowledge Base...")
    
    # 1. Initialize Client
    client = QdrantClient(
        url=config.QDRANT_URL, 
        api_key=config.QDRANT_API_KEY
    )
    
    # 2. Check Total Count
    try:
        collection_info = client.get_collection(collection_name=config.COLLECTION_NAME)
        count_result = client.count(collection_name=config.COLLECTION_NAME)
        
        print("-" * 50)
        print(f"✅ Collection Status: {collection_info.status}")
        print(f"📊 Total Chunks Uploaded: {count_result.count}")
        print("-" * 50)

        if count_result.count >= 3972:
            print("🌟 SUCCESS: All 3,972 chunks appear to be present!")
        else:
            print(f"⚠️ Note: You have {count_result.count}/3972 chunks. You may need to run main.py again.")

        # 3. Peek at the Data (Verification)
        print("\n🔍 Peeking at the latest 3 entries to verify metadata/links:")
        
        # We use scroll to see the raw data
        points, _ = client.scroll(
            collection_name=config.COLLECTION_NAME,
            limit=3,
            with_payload=True
        )

        for i, point in enumerate(points):
            payload = point.payload
            meta = payload.get('metadata', {})
            print(f"\n--- Entry #{i+1} ---")
            print(f"Title : {meta.get('title', 'N/A')}")
            print(f"Link  : {meta.get('source', 'N/A')}")
            print(f"Snippet: {payload.get('page_content', '')[:150]}...")

    except Exception as e:
        print(f"❌ Error connecting to Qdrant: {e}")

if __name__ == "__main__":
    inspect_brain()