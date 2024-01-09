import time
import logging
import os

import streamlit as st
from openai import OpenAI

# Add your API key and assistant ID directly
openai_api_key = '<your-key>'
assistant_id = '<your-assistant-id>'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

st.set_page_config(
    page_title='OpenAI Assistant',
    layout='centered',
)

st.markdown("""
    <style>
        .reportview-container {
            margin-top: -2em;
        }
        #MainMenu {visibility: hidden;}
        .stDeployButton {display:none;}
        footer {visibility: hidden;}
        #stDecoration {display:none;}
    </style>
""", unsafe_allow_html=True)

client = OpenAI(api_key=openai_api_key)

def wait_on_run(run, thread_id):
    while run.status in ["queued", "in_progress"]:
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
        logging.info(f"Run Status: {run.status}")
        time.sleep(0.5)
    return run

def st_message(message, is_user):
    role = "You" if is_user else "Assistant"
    st.text(f"{role}: {message}")

def send_message():
    if st.session_state.user_input and st.session_state.thread_id:
        try:
            # Add user message to the thread and to the chat
            client.beta.threads.messages.create(
                thread_id=st.session_state.thread_id,
                role="user",
                content=st.session_state.user_input
            )
            st.session_state.messages.append({'message': st.session_state.user_input, 'is_user': True})
            logging.info(f"User message sent: {st.session_state.user_input}")

            # Create and wait for the run
            run = client.beta.threads.runs.create(
                thread_id=st.session_state.thread_id,
                assistant_id=assistant_id
            )
            run = wait_on_run(run, st.session_state.thread_id)
            logging.info("Assistant response received.")

        except Exception as e:
            logging.error(f"Error in sending message: {str(e)}")

        # Retrieve and append assistant's message
        messages_response = client.beta.threads.messages.list(thread_id=st.session_state.thread_id)
        for message in messages_response:
            if message.role == "assistant":
                message_content = message.content
                if isinstance(message_content, list) and message_content:
                    message_text = " ".join([content.text.value for content in message_content if content.type == 'text'])
                    if message_text not in [m['message'] for m in st.session_state.messages]:
                        st.session_state.messages.append({'message': message_text, 'is_user': False})

        # Clear the input field after sending the message
        st.session_state.user_input = ""

def app():
    st.title("OpenAI Assistant")

    if 'thread_id' not in st.session_state:
        st.session_state.thread_id = None
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'user_input' not in st.session_state:
        st.session_state.user_input = ""

    # Display chat messages
    for chat_message in st.session_state.messages:
        st_message(chat_message['message'], is_user=chat_message['is_user'])

    # User Input
    st.text_input("Ask a question:", key="user_input", on_change=send_message, placeholder="Press enter to send")

    # Check if a thread needs to be created
    if st.session_state.thread_id is None:
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id

app()
