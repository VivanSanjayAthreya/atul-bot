import streamlit as st
import warnings
from qdrant_client import QdrantClient
from langchain_core.messages import HumanMessage, AIMessage
from src import config

# --- SETUP ---
warnings.filterwarnings("ignore")
st.set_page_config(page_title="Atul AI", page_icon="🙏")

# --- INITIALIZE AI & DB ---
@st.cache_resource
def get_resources():
    client = QdrantClient(url=config.QDRANT_URL, api_key=config.QDRANT_API_KEY)
    llm = config.get_llm()
    embedder = config.get_embeddings()
    return client, llm, embedder

client, llm, embedder = get_resources()

# --- SIDEBAR ---
with st.sidebar:
    st.title("Atul AI 🙏")
    st.info("Ask questions about ShriVaishnava sampradayam")
    if st.button("Clear Conversation"):
        st.session_state.messages = []
        # Re-initialize with welcome message after clearing
        st.session_state.messages.append(AIMessage(content="🙏 Adiyen Namaskaram! I am ***Atul*** your ShriVaishnava assistant. How can I help you today?"))
        st.rerun()

# --- CHAT HISTORY ---
if "messages" not in st.session_state:
    # 🌟 INITIALIZE WITH WELCOME MESSAGE
    st.session_state.messages = [
        AIMessage(content="🙏 Adiyen Namaskaram! I am ***Atul*** your ShriVaishnava assistant. How can I help you today?")
    ]

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message("user" if isinstance(message, HumanMessage) else "assistant"):
        st.markdown(message.content)

# --- USER INPUT ---
if prompt := st.chat_input("Ask a question..."):
    # 1. Show user message
    st.session_state.messages.append(HumanMessage(content=prompt))
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Generate AI Response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # A. Search
                query_vector = embedder.embed_query(prompt)
                hits = client.query_points(
                    collection_name=config.COLLECTION_NAME,
                    query=query_vector,
                    limit=4
                ).points

                # B. Build Context & Links
                context_parts = []
                sources = set()
                for hit in hits:
                    payload = hit.payload
                    text = payload.get('page_content', '')
                    meta = payload.get('metadata', {})
                    link = meta.get('source', '')
                    title = meta.get('title', 'Article')
                    if text:
                        context_parts.append(text)
                        if link: sources.add(f"{link}")

                # C. Build History String for AI
                history_str = "\n".join([f"{'User' if isinstance(m, HumanMessage) else 'Bot'}: {m.content}" for m in st.session_state.messages[-5:]])

                # D. Call AI
                template = f"""
                You are a knowledgeable and compassionate Srivaishnava scholar. 
                Your goal is to share wisdom in a warm, conversational, and respectful tone.

                CONVERSATIONAL RULES:
                1. Speak naturally. NEVER use phrases like "Based on the context," "According to the provided text," or "The documents state."
                2. Do not explain where you got the information from in your sentences; just state the wisdom directly as if you already know it.
                3. Always understand the context in which the knowledge is fetched. Don't just copy-paste facts. Weave them into a meaningful answer that matches with the words used by the user. 
                4. Aways use the user's language style and tone to make it feel more personal and less robotic.
                5. If the answer is not in your knowledge, say: "I am sorry, I don't have a detailed record of that specific topic in my current archives."
                6. Use "we" or "our community" to sound more like a member of the tradition.

                Conversation History:
                {history_str}

                Context:
                {" ".join(context_parts)}

                Question: {prompt}
                """
                
                response = llm.invoke(template)
                answer = response.content
                
                # E. Show Result
                st.markdown(answer)
                if sources:
                    with st.expander("📚 View Sources & References"):
                        for s in sources:
                            st.markdown(f"* {s}")
                
                # Save to history
                st.session_state.messages.append(AIMessage(content=answer))

            except Exception as e:
                st.error(f"Error: {e}")