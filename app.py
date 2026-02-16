import streamlit as st
import time
import warnings
from qdrant_client import QdrantClient
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from src import config

# --- SETUP ---
warnings.filterwarnings("ignore")
st.set_page_config(page_title="Atul AI", page_icon="🙏")

# --- INITIALIZE AI & DB ---
@st.cache_resource
def get_resources():
    try:
        client = QdrantClient(url=config.QDRANT_URL, api_key=config.QDRANT_API_KEY)
        llm = config.get_llm()
        embedder = config.get_embeddings()
        return client, llm, embedder
    except Exception as e:
        st.error(f"❌ Critical Error connecting to resources: {e}")
        return None, None, None

client, llm, embedder = get_resources()

# --- SIDEBAR ---
with st.sidebar:
    st.title("Atul AI")
    st.info("Ask questions about Srivaishnava Sampradayam")
    if st.button("Clear Conversation"):
        st.session_state.messages = []
        # Re-initialize with welcome message after clearing
        st.session_state.messages.append(AIMessage(content="Namaskaram 🙏 Adiyen is ***Atul*** your ShriVaishnava assistant. How can I help you today?"))
        st.rerun()

# --- CHAT HISTORY ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        AIMessage(content="Namaskaram 🙏 Adiyen is ***Atul***, your Srivaishnava assistant. How can I help you today?")
    ]

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message("user" if isinstance(message, HumanMessage) else "assistant"):
        st.markdown(message.content)

# --- HELPER: CONTEXTUAL REWRITER ---
def rewrite_query(user_input, history):
    """
    Rewrites the user's question to be self-contained for search.
    Ex: "Explain it in Kannada" -> "Explain Injimedu Swami's history in Kannada"
    """
    if not history:
        return user_input
        
    rewrite_prompt = ChatPromptTemplate.from_template(
        """Given a chat history and the latest user question which might reference context in the chat history, 
        formulate a standalone question which can be understood without the chat history. 
        Do NOT answer the question, just reformulate it if needed and otherwise return it as is.
        
        Chat History:
        {history}
        
        Latest Question: {question}
        
        Standalone Question:"""
    )
    
    # We use the existing LLM to do this small task
    chain = rewrite_prompt | llm
    response = chain.invoke({"history": history, "question": user_input})
    return response.content

# --- USER INPUT ---
if prompt := st.chat_input("Ask a question..."):
    if not client or not llm:
        st.error("System could not be initialized.")
        st.stop()

    # 1. Show user message
    st.session_state.messages.append(HumanMessage(content=prompt))
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Generate AI Response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # A. Build Chat History (Standard)
                history_msgs = st.session_state.messages[-6:-1] # Get history excluding the current prompt
                history_str = "\n".join(
                    [f"{'User' if isinstance(m, HumanMessage) else 'Assistant'}: {m.content}" 
                     for m in history_msgs]
                )

                # B. REWRITE QUERY (SMART) - This helps with follow-up questions that reference previous context
                search_query = rewrite_query(prompt, history_str)
                
                # Use the SMART query for retrieval
                query_vector = embedder.embed_query(search_query) 
                
                search_result = client.query_points(
                    collection_name=config.COLLECTION_NAME,
                    query=query_vector,
                    limit=5
                )
                hits = search_result.points

                # C. Build Context
                context_parts = []
                sources = set()
                
                for hit in hits:
                    payload = hit.payload
                    text = payload.get('page_content', '')
                    meta = payload.get('metadata', {})
                    link = meta.get('source', '')
                    title = meta.get('title', 'Source')
                    
                    if text:
                        # Add Source Title to context so AI knows where it came from
                        context_parts.append(f"Source: {title}\nContent: {text}")
                        if link: 
                            sources.add(link)

                # Join all chunks into one big string
                final_context = "\n\n".join(context_parts)
                # Handle "No Data" Case
                if not final_context:
                    final_context = "No specific archives found for this query."

                # D. Define Prompt Template (With Context + History)
                template = """
You are a knowledgeable and compassionate Srivaishnava scholar named **Atul**. 
Your goal is to share wisdom in a warm, conversational, and respectful tone based ONLY on the context provided below.

---
CONTEXT FROM ARCHIVES:
{context}
---

PREVIOUS CONVERSATION:
{chat_history}
---

CONVERSATIONAL RULES:
1.  **Strict Grounding:** Answer the user's latest question using ONLY the "CONTEXT FROM ARCHIVES". Do not use outside knowledge, internet information, or your internal training data.
2.  **Context Aware:** Use the "PREVIOUS CONVERSATION" to understand follow-up questions (e.g., if user asks "Tell me more", know what they are referring to).
3.  **Tone:** Speak naturally and spiritually. Use "we" or "our community".
4.  **No Meta-Talk:** NEVER say "Based on the provided text". State the wisdom directly as if you have known it for years.
5.  **Adaptability:** Adopt the user's language style to make it feel personal and natural.
6.  **Contextual Weaving:** Do not just copy-paste facts. Weave the information into a meaningful answer that directly addresses the user's intent.
7.  **Uncertainty:** If the answer is NOT in the archives, strictly reply: "Adiyen, I do not have a detailed record of that specific topic in my current archives. Please consult an Acharyan for more details or email sriapnswami@gmail.com / saransevaks@gmail.com." Do not try to make up an answer.
8.  **Delicate Topics:** If the question touches on delicate or sensitive topics like Anushtanam (practices), subjective interpretations, or highly sensitive topics, add this disclaimer: "Please note that practices may vary based on family traditions. For specific guidance, kindly reach out to an Acharyan or email sriapnswami@gmail.com / saransevaks@gmail.com."
9.  **Scope:** If the question is completely unrelated to Srivaishnavism/Spiritualism (e.g., politics, movies, coding), politely decline to answer.
10.  **Language:** If the user asks for a specific language (Tamil, Kannada, etc.), TRANSLATE your answer accordingly using the English context provided.

USER LATEST QUESTION: {question}

YOUR WISDOM:
"""
                
                # E. Format & Call AI
                formatted_prompt = template.format(
                    context=final_context, 
                    chat_history=history_str, 
                    question=prompt
                )
                
                response = llm.invoke(formatted_prompt)
                answer = response.content
                
                # F. Show Result
                st.markdown(answer)
                
                if sources and "Adiyen, I do not have" not in answer:
                    with st.expander("📚 Want to learn more?"):
                        for s in sources:
                            st.markdown(f"* [{s}]({s})") # Clickable Links
                
                # Save to history
                st.session_state.messages.append(AIMessage(content=answer))

            except Exception as e:
                st.error(f"Error: {e}")