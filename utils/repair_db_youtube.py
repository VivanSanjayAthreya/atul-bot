from qdrant_client import QdrantClient, models
from src import config

# 1. Connect
client = QdrantClient(url=config.QDRANT_URL, api_key=config.QDRANT_API_KEY)

# 2. List of Corrupted Videos (Identified from your logs)
bad_urls = [
"https://www.youtube.com/watch?v=1YB0lsw8oRI"
]

print(f"🧹 Starting cleanup of {len(bad_urls)} corrupted videos...")

for url in bad_urls:
    print(f"   Deleting: {url}")
    client.delete(
        collection_name=config.COLLECTION_NAME,
        points_selector=models.FilterSelector(
            filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="metadata.source",
                        match=models.MatchValue(value=url),
                    )
                ]
            )
        ),
    )

print("\n✅ Cleanup Complete! You can now re-run ingest.py safely.")