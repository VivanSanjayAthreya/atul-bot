# src/config.py
import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables once
load_dotenv()

# API Keys
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

# Configuration Constants
EMBEDDING_MODEL = "gemini-embedding-001"
COLLECTION_NAME = "srivaishnava_knowledge"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100

# Validation
if not all([GOOGLE_API_KEY, QDRANT_URL, QDRANT_API_KEY]):
    raise ValueError("❌ CRITICAL: Missing API Keys in .env file")

# Shared Embedding Function
def get_embeddings():
    return GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL,
        google_api_key=GOOGLE_API_KEY
    )

def get_llm():
    return ChatGoogleGenerativeAI(
        # Try the most stable current model
        model="gemini-2.5-flash", 
        google_api_key=GOOGLE_API_KEY,
        temperature=0.3,
        convert_system_message_to_human=True
    )