import streamlit as st 
from openai import OpenAI
import sys
import chromadb
from pathlib import Path
from PyPDF2 import PdfReader

# fix for using chromadb on streamlit
__import__('pysqlite3')
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')



# creating the OpenAI Client
if 'openai_client' not in st.session_state:
    st.session_state.openai_client = OpenAI(api_key=st.secrets.OPENAI_API_KEY)

# EXTRACTING text from THE PDF 
def extract_text_from_pdf(pdf_path):
    '''
    Extracts texts from a PDF file with error handling
    '''
    try:
        reader = PdfReader(pdf_path)
        text = ''
        for page in reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return ""

# collection = chromaDB collection, already established 
# text = extracted text from PDF files
# embeddings inserted into collection from OpenAI
def add_to_collection(collection, text, file_name):
    # creates an embedding
    client = st.session_state.openai_client
    response = client.embeddings.create(
        input=text,
        model='text-embedding-3-small' 
    )
    embedding = response.data[0].embedding
    
    # add embedding and document to ChromaDB
    collection.add(
        documents=[text],
        ids=[file_name],
        embeddings=[embedding],
        metadatas=[{"filename": file_name}]
    )

# POPULATING THE COLLECTION WITH PDFS
def load_pdfs_to_collection(folder_path, collection):
    pdf_files = list(Path(folder_path).glob('*.pdf'))
    
    for pdf_file in pdf_files:
        text = extract_text_from_pdf(pdf_file)
        if text:
            add_to_collection(collection, text, pdf_file.name)
    return True

# creating the vector database function 
def create_vector_db():
    # create Chroma Client
    chroma_client = chromadb.PersistentClient(path='./ChromaDB_for_Lab')
    collection = chroma_client.get_or_create_collection('Lab4Collection')
    
    # checking if collection is empty
    if collection.count() == 0:
        with st.spinner('Loading PDFs into collection...'):
            loaded = load_pdfs_to_collection('./Labs/Lab-04-Data/', collection)
            st.success(f'Loaded {collection.count()} documents!')
    
    return collection

# Only create the ChromaDB once - store in session_state
if 'Lab4_VectorDB' not in st.session_state:
    st.session_state.Lab4_VectorDB = create_vector_db()

# Buffer function - keeps last 6 messages + system prompt
def trim_messages(messages, max_messages=6):
    """Keep system prompt + last 6 messages (3 user-assistant exchanges)"""
    system_msgs = [msg for msg in messages if msg['role'] == 'system']
    other_msgs = [msg for msg in messages if msg['role'] != 'system']
    
    trimmed = other_msgs[-max_messages:] if len(other_msgs) > max_messages else other_msgs
    
    return system_msgs + trimmed

# MAIN APP
st.title('Lab 4: Chatbot using RAG')

st.write('''
**How this chatbot works:**
- This chatbot uses RAG (Retrieval Augmented Generation) with 7 PDF documents
- Ask questions and the bot will search relevant documents to provide accurate answers
- The bot will clearly indicate when it's using information from the documents
- **Conversation Memory:** This bot uses a buffer of 6 messages (3 user-assistant exchanges)
''')

# Initialize messages with system prompt
if 'messages' not in st.session_state:
    st.session_state['messages'] = [
        {'role': 'system', 'content': '''You are a helpful assistant that answers questions using provided context from PDF documents.

When answering questions:
- If you find relevant information in the provided documents, start your answer with "Based on the documents..." or "According to [document name]..."
- Clearly cite which document(s) you're using in your response
- If the documents don't contain relevant information, say "I don't have information about that in the available documents" and provide a general answer if appropriate
- After answering, ask "Do you want more info?" If yes, provide more details. If no, ask "What else can I help you with?"'''},
        {'role': 'assistant', 'content': 'How can I help you? Ask me anything about the documents!'}
    ]

# Display chat messages
for msg in st.session_state.messages:
    if msg['role'] != 'system':
        chat_msg = st.chat_message(msg['role'])
        chat_msg.write(msg['content'])

# Chat input
if prompt := st.chat_input('What is up?'):
    st.session_state.messages.append({'role': 'user', 'content': prompt})
    
    with st.chat_message('user'):
        st.markdown(prompt)
    
    # Get relevant context from vector database
    client = st.session_state.openai_client
    embedding_response = client.embeddings.create(
        input=prompt,
        model='text-embedding-3-small'
    )
    query_embedding = embedding_response.data[0].embedding
    
    # Query the vector database
    results = st.session_state.Lab4_VectorDB.query(
        query_embeddings=[query_embedding],
        n_results=3
    )
    
    # Build context from retrieved documents
    context = ""
    for i in range(len(results['documents'][0])):
        doc_content = results['documents'][0][i][:2000]
        doc_name = results['ids'][0][i]
        context += f"\n\n--- Document: {doc_name} ---\n{doc_content}\n"
    
    # Prepare messages with context
    messages_to_send = trim_messages(st.session_state.messages, max_messages=6)
    
    # Add context to system message for this request
    messages_with_context = []
    for msg in messages_to_send:
        if msg['role'] == 'system':
            messages_with_context.append({
                'role': 'system',
                'content': msg['content'] + f"\n\nHere are the relevant documents for context:\n{context}"
            })
        else:
            messages_with_context.append(msg)
    
    # Get response from OpenAI
    stream = client.chat.completions.create(
        model='gpt-5-2025-08-07',
        messages=messages_with_context,
        stream=True
    )
    
    with st.chat_message('assistant'):
        response = st.write_stream(stream)
    
    st.session_state.messages.append({'role': 'assistant', 'content': response})