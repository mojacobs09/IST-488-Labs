import streamlit as st 
from openai import OpenAI
import sys
import chromadb
from pathlib import Path
from PyPDF2 import PdfReader

# fix for using chromadb on strea,lit

__import__('pysqlite3')
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

# create Chroma Client
chroma_client = chromadb.PersistantClient(path='./ChromaDB_for_Lab')
collection = chroma_client.get_or_create_collection('Lab4Collection')


#creating the open AI Client
if 'openai_client' not in st.session_state:
    st.session_state.openai_client = OpenAI(api_key=st.secrets.OPEN_AI_KEY)

 #EXTRACTING text from THE PDF 
def extract_text_from_pdf(pdf_path):
    '''
    Extracts texts from a PDF file with error handling
    
    '''
    try:
        reader = PdfReader(pdf_path)
        text  = ''


        for page in reader.pages:
            text += page.extract_text()

        return text 
    
#collection = chromaDB collection, already established 
# text = extracted text from PDF files
# embeddings inserted into collection from OpenAI

def add_to_collection(collection, text, file_name):
    #creates an embedding
    client = st.session_state.openai_client
    response = client.embeddings.create(
        input=text,
        model='text-embedding-3-small' 
    )

    embedding = response.data[0].embedding
    #add embedding and document to ChromaDB
    collection.add(
        documents=[text],
        ids=file_name,
        embeddings=[embedding]
    )

#POPULATING THE TEXT WITH PDFS
def load_pdfs_to_collection(folder_path, collection):
    pdf_files = Path(folder_path).glob('*.pdf')
    for pdf_file in pdf_files:
        text = extract_text_from_pdf(pdf_file)
        if text:  # only add if text was extracted
            add_to_collection(collection, text, pdf_file.name)
    return True

#creating the vector database function 
def create_vector_db():
    # create Chroma Client
    chroma_client = chromadb.PersistentClient(path='./ChromaDB_for_Lab')
    collection = chroma_client.get_or_create_collection('Lab4Collection')
    
    # checking if collection is empty
    if collection.count() == 0:
        with st.spinner('Loading PDFs into collection...'):
            loaded = load_pdfs_to_collection('./Lab-04-Data/', collection)
            st.success(f'Loaded {collection.count()} documents!')
    
    return collection

if 'Lab4_VectorDB' not in st.session_state:
    st.session_state.Lab4_VectorDB = create_vector_db()

# Buffer function - keeps last 6 messages + system prompt
def trim_messages(messages, max_messages=6):
    """Keep system prompt + last 6 messages (3 user-assistant exchanges)"""
    system_msgs = [msg for msg in messages if msg['role'] == 'system']
    other_msgs = [msg for msg in messages if msg['role'] != 'system']
    
    trimmed = other_msgs[-max_messages:] if len(other_msgs) > max_messages else other_msgs
    
    return system_msgs + trimmed


#INCLUDING THE CODE FROM HW 3 








#collection = chromaDB collection, already established 
# text = extracted text from PDF files
# embeddings inserted into collection from OpenAI

def add_to_collection(collection, text, file_name):
    #creates an embedding
    client = st.session_state.openai_client
    response = client.embeddings.create(
        input=text,
        model='text-embedding-3-small' 
    )

    embedding = response.data[0].embedding
    #add embedding and document to ChromaDB
    collection.add(
        documents=[text],
        ids=file_name,
        embeddings=[embedding]
    )


    #CREATE THE FUNCTIONS FOR THIS




#populating the collection with pdfs
#uses the extract_text_from_pdf stuff
def load_pdfs_to_collection(folder_path, collection):

    pdf_files = Path(folder_path).glob('*.pdf')

    for pdf_file in pdf_files:
        text = extract_text_from_pdf(pdf_file)
        add_to_collection(collection, text, pdf_file.name)

    return True
 
#checking if collecton is empty

if collection.count() == 0:
    loaded = load_pdfs_to_collection('./Lab-04-Data/', collection)



# MAIN APP

st.title('Lab 4: Chatbot using RAG')

st.write('''
**How this chatbot works:**
- This chatbot uses RAG (Retrieval Augmented Generation)
- Enter a topic to research 
- The chatbot will use retrieved documents to answer your questions
- **Conversation Memory:** This bot will use a conversation bufer for six messages
''')

#side bar to test the vector bedding 

st.sidebar.subheader('Test Vector Database')
test_topic = st.sidebar.text_input('Test Topic', placeholder='e.g., Generative AI, Text Mining...')

if test_topic:
    client = st.session_state.openai_client
    response = client.embeddings.create(
        input=test_topic,
        model='text-embedding-3-small'
    )
    query_embedding = response.data[0].embedding
    
    # text related to the question prompt
    results = st.session_state.Lab4_VectorDB.query(
        query_embeddings=[query_embedding],
        n_results=3
    )
    
    # display the results
    st.sidebar.subheader(f'Top 3 Results for: {test_topic}')
    for i in range(len(results['ids'][0])):
        doc_id = results['ids'][0][i]
        st.sidebar.write(f'**{i+1}. {doc_id}**')

# Initialize messages with system prompt
if 'messages' not in st.session_state:
    st.session_state['messages'] = [
        {'role': 'system', 'content': '''You are a helpful assistant that answers questions using the provided context from PDF documents.
After answering each question, ask "Do you want more info?"
If the user says yes, provide more detailed information and ask again.
If the user says no, ask "What else can I help you with?"'''},
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
    context = "\n\n".join([f"From {results['ids'][0][i]}:\n{results['documents'][0][i][:1000]}" 
                           for i in range(len(results['documents'][0]))])
    
    # Add context to the current conversation
    messages_with_context = trim_messages(st.session_state.messages, max_messages=6)
    # Insert context into system message
    for msg in messages_with_context:
        if msg['role'] == 'system':
            msg['content'] = msg['content'] + f"\n\nRelevant context from documents:\n{context}"
    
    # Get response from OpenAI
    stream = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=messages_with_context,
        stream=True
    )
    
    with st.chat_message('assistant'):
        response = st.write_stream(stream)
    
    st.session_state.messages.append({'role': 'assistant', 'content': response})


topic = st.sidebar.text_input('Topic', placeholder = 'Type your topic (e.g., Gen AI)...')

if topic:
    client = st.session_state.openai_client
    response = client.embeddings.create(
        input=topic,
        model='text-embedding-3-small'
    )
    query_embedding = response.data[0].embedding
    #text related to the question prompt
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=3
    )

#display the results

    st.subheader(f'Results for: {topic}')

    for i in range (len(results['documents'][0])):
        doc = results['documents'][0][i]
        doc_id = results['ids'][0][i]

        st.write(f'**{i+1}. {doc_id}**')
else: 
    st.info('Enter a topic in the sidebar to search the collection')






