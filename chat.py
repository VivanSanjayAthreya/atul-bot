import warnings
import time
from qdrant_client import QdrantClient
from langchain_core.prompts import PromptTemplate 
from langchain_core.messages import HumanMessage, AIMessage # New imports for history
from src import config

# Silence warnings
warnings.filterwarnings("ignore")

def start_chat():
    print("Atul")
    
    # 1. Connect to Qdrant & AI
    client = QdrantClient(url=config.QDRANT_URL, api_key=config.QDRANT_API_KEY)
    llm = config.get_llm()
    embedder = config.get_embeddings()

    # 2. Setup Chat History
    # This list will store HumanMessage and AIMessage objects
    chat_history = [] 
    # Limit to last 5 exchanges to avoid cluttering the brain
    MAX_HISTORY = 10 

    # 3. Define the Prompt (Updated to include History)
    template = PromptTemplate.from_template("""
    You are a helpful assistant for the Srivaishnava community.
    Use the following pieces of context and the conversation history to answer the question.
    
    RULES:
    1. If the answer is not in the context, say "I don't have enough information on that topic yet."
    2. Keep the answer spiritual, respectful, and accurate.

    Conversation History:
    {history}

    Context from Articles:
    {context}

    Question: {question}
    
    Answer:
    """)

    print("\n🙏 Namaskaram! I am ready. Ask me anything about the articles.")
    print("-" * 60)

    while True:
        try:
            query = input("\nYou: ")
        except KeyboardInterrupt:
            print("\n👋 Dhanyosmi!")
            break
        
        if query.lower() in ["quit", "exit", "bye", "clear"]:
            if query.lower() == "clear":
                chat_history = []
                print("✨ Chat history cleared!")
                continue
            print("👋 Dhanyosmi!")
            break
            
        if not query.strip():
            continue
            
        print("   Thinking...")
        try:
            # --- STEP A: EMBEDDING & SEARCH ---
            query_vector = embedder.embed_query(query)
            hits = client.query_points(
                collection_name=config.COLLECTION_NAME,
                query=query_vector,
                limit=4
            ).points
            
            # --- STEP B: BUILD CONTEXT & LINKS ---
            context_parts = []
            current_sources = set()
            
            for hit in hits:
                payload = hit.payload
                text = payload.get('page_content', '')
                metadata = payload.get('metadata', {})
                link = metadata.get('source', 'Link not available')
                title = metadata.get('title', 'Article')
                
                if text:
                    context_parts.append(text)
                    current_sources.add(f"{title}: {link}")

            context_text = "\n\n".join(context_parts)
            
            # --- STEP C: FORMAT HISTORY ---
            # Turn history into a string the AI can read
            history_str = ""
            for msg in chat_history:
                prefix = "User" if isinstance(msg, HumanMessage) else "Bot"
                history_str += f"{prefix}: {msg.content}\n"

            # --- STEP D: GENERATE ANSWER ---
            formatted_prompt = template.format(
                history=history_str if history_str else "No previous history.",
                context=context_text,
                question=query
            )
            
            response = llm.invoke(formatted_prompt)
            ai_answer = response.content
            
            print(f"\nAtul: {ai_answer}")
            
            # --- STEP E: UPDATE HISTORY ---
            # Save the exchange to memory
            chat_history.append(HumanMessage(content=query))
            chat_history.append(AIMessage(content=ai_answer))
            
            # Keep history short (prevent memory bloat)
            if len(chat_history) > MAX_HISTORY:
                chat_history = chat_history[-MAX_HISTORY:]

            # Display Links
            if current_sources:
                print("\n   🔗 Read more:")
                for source in current_sources:
                    print(f"   - {source}")

        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    start_chat()