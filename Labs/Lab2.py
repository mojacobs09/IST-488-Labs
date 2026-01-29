import streamlit as st
from openai import OpenAI

# Show title and description.
st.title("My Document question answering")
st.write(
    "Upload a document below and ask a question about it – GPT will answer! "
    "To use this app, you need to provide an OpenAI API key, which you can get [here](https://platform.openai.com/account/api-keys). "
)

openai_api_key = st.secrets.OPENAI_API_KEY

# Create an OpenAI client.
client = OpenAI(api_key=openai_api_key)

# Let the user upload a file via `st.file_uploader`.
uploaded_file = st.file_uploader(
     "Upload a document (.txt or .md)", type=("txt", "md")

# Ask the user for a question via `st.text_area`.

if uploaded_file and question:
    # Process the uploaded file and question.
    document = uploaded_file.read().decode()
    messages = [
        {
            "role": "user",
            "content": f"Here's a document: {document} \n\n---\n\n {question}",
        }
    ]

    #summary choice

    st.sidebar.header(":red[Summary Type]") 
    summary_type = st.sidebar.selectbox (
        "Choose a summary type",
        ('Summarize in 100 words', 'Summarize in 2 connecting paragraghs', 'Summarize in 5 bullet points')

    )
# check box make the user select the higher model
    use_advance = st.checkbox('Use Advanced Model')

    if use_advance:
        model_name = 'gpt-5-mini'
    else: 
        model_name = "gpt-5.1"


    # Generate an answer using the OpenAI API.
    stream = client.chat.completions.create(
        model="gpt-5-chat-latest",
        messages=messages,
        stream=True,
    )
    # Stream the response to the app using `st.write_stream`.
    st.write_stream(stream)