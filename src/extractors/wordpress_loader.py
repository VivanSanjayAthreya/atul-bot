import json
import os
from langchain_core.documents import Document

def load_cleaned_json(json_path):
    """
    Reads the cleaned_articles.json and converts it into standard AI Documents.
    Returns a list of LangChain Document objects.
    """
    # Check if file exists
    if not os.path.exists(json_path):
        print(f"❌ Error: File '{json_path}' not found.")
        print(f"   (Looked in: {os.path.abspath(json_path)})")
        return []

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            articles = json.load(f)
    except json.JSONDecodeError:
        print(f"❌ Error: '{json_path}' is not a valid JSON file.")
        return []
    
    documents = []
    print(f"📂 Loader: Parsing {len(articles)} articles from JSON...")

    for art in articles:
        # 1. Construct the text the AI will actually read
        # We combine Title + Content to give it full context
        enhanced_content = f"Title: {art.get('title', 'Untitled')}\n\n{art.get('content', '')}"
        
        # 2. Extract metadata for citations
        # 'link' from WordPress becomes 'source' for the bot
        source_link = art.get('link', '')
        
        # 3. Create the Document object
        doc = Document(
            page_content=enhanced_content,
            metadata={
                "source": source_link,
                "title": art.get('title', ''),
                "type": "article"
            }
        )
        documents.append(doc)
        
    print(f"   👉 Successfully loaded {len(documents)} documents.")
    return documents