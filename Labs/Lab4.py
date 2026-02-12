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
chroma_client = chromadb.PersistentClient(path='./ChromaDB_for_Lab')
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
        text = ''
        for page in reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return ""
    
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
        add_to_collection(collection, text, pdf_file.name)

    return True
 
#checking if collecton is empty

if collection.count() == 0:
    loaded = load_pdfs_to_collection('./Lab-04-Data/', collection)


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
    st.sidebar.subheader(f'Top Results for: {test_topic}')
    for i in range(len(results['ids'][0])):
        doc_id = results['ids'][0][i]
        st.sidebar.write(f'**{i+1}. {doc_id}**')
else: 
    st.info('Enter a topic in the sidebar to search the collection')
