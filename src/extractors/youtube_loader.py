import json
import os
from langchain_core.documents import Document

def load_youtube_json(json_path):
    """
    Reads the youtube_dump.json and converts it into standard AI Documents.
    """
    if not os.path.exists(json_path):
        print(f"❌ Error: File '{json_path}' not found.")
        print("   (Run 'src/extractors/youtube.py' first!)")
        return []

    with open(json_path, 'r', encoding='utf-8') as f:
        videos = json.load(f)
    
    documents = []
    print(f"🎥 Loader: Loading {len(videos)} videos from JSON...")

    for vid in videos:
        # Construct content for AI
        enhanced_content = f"Video Title: {vid.get('title', 'Unknown')}\n"
        enhanced_content += f"Author: {vid.get('author', '')}\n\n"
        enhanced_content += vid.get('content', '')
        
        doc = Document(
            page_content=enhanced_content,
            metadata={
                "source": vid.get('source', ''),
                "title": vid.get('title', ''),
                "type": "youtube",
                "thumbnail": vid.get('thumbnail', '') # Store thumbnail for UI!
            }
        )
        documents.append(doc)
        
    return documents