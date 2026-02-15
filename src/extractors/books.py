import os
import glob
from langchain_community.document_loaders import TextLoader

def load_local_books(folder_path="books"):
    print(f"\n📚 [Books] Reading from '{folder_path}'...")
    docs = []
    
    if not os.path.exists(folder_path):
        print(f"   ⚠️ Folder '{folder_path}' does not exist.")
        return docs

    files = glob.glob(f"{folder_path}/*.txt")
    for file in files:
        try:
            loader = TextLoader(file, encoding='utf-8')
            docs.extend(loader.load())
            print(f"   ✅ Read: {os.path.basename(file)}")
        except Exception as e:
            print(f"   ❌ Error reading {file}: {e}")
            
    return docs