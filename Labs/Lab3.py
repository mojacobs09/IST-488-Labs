import streamlit as st
from openai import OpenAI

st.title('My LAB3 queston answering bot')

openAI_model= st.sidebar.selectbox('Which Model?',
                                   ('mini', 'regular'))
if openAI_model == 'mini':
    model_to_use = 'gpt-4o-mini'

else:
    model_to_use = 'gpt-4o'

#create an opem AI client

if 'client' not in st.session_state:
    api_key = st.secrets ['OPENAI_API_KEY']
    st.session_state.client = OpenAI(api_key=api_key)

if 'messages' not in st.session_state:
    st.session_state['messages'] = [
        {'role': 'system', 'content': '''You are a helpful assistant that explains things simply for 10-year-olds.
After answering each question, ask "Do you want more info?"
If the user says yes, provide more detailed information and ask again.
If the user says no, ask "What else can I help you with?"'''},
        {'role': 'assistant', 'content': 'How can I help you?'}
    ]
for msg in st.session_state.messages:
    if msg['role'] != 'system':  # Don't show system message
        chat_msg = st.chat_message(msg['role'])
        chat_msg.write(msg['content'])

if prompt := st.chat.input('What is up?'):
    st.session_statemessages.append({'role': 'user', 'content': prompt})

with st.chat_message('user'):
     st.markdown(prompt)

client = st.session_state.client
stream = client.chat.completions.create(
         model=model_to_use,
         messages = st.session_state.messages,
         stream=True)
     
with st.chat_message('assistant'):
         response = st.write_stream(stream)
st.session_state.messages.append({'role': 'user', 'content': prompt})


#going to make a function to write the buffer 

def trim_msgs(messages, max_user_messages=2):
    system_msgs = [msg for msg in messages if msg['role'] == 'system']
    other_msgs = [msg for msg in messages if msg['role'] != 'system']
    
    trimmed = []
    user_count = 0
    for msg in reversed(other_msgs):
        if msg['role'] == 'user':
            user_count += 1
        if user_count <= max_user_messages:
            trimmed.insert(0, msg)
    
    return system_msgs + trimmed

def count_tokens(messages, model="gpt-4o"):
    """Calculate total tokens in messages"""
    encoding = tiktoken.encoding_for_model(model)
    
    total_tokens = 0
    for message in messages:
        total_tokens += len(encoding.encode(message['content']))
    
    return total_tokens


def trim_messages_by_tokens(messages, max_tokens, model="gpt-4o"):
    """Keep messages that fit within max_tokens"""
    trimmed = []
    current_tokens = 0
    
    # Go through messages backwards
    for msg in reversed(messages):
        msg_tokens = count_tokens([msg], model)
        
        # Add message if it fits
        if current_tokens + msg_tokens <= max_tokens:
            trimmed.insert(0, msg)
            current_tokens += msg_tokens
    
    return trimmed


