#Conversation storage currently not working

import os
import json
import streamlit as st
from openai import OpenAI
from llama_index.core import load_index_from_storage
from llama_index.core import StorageContext
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.agent.openai import OpenAIAgent
from llama_index.core.storage.chat_store import SimpleChatStore
from global_settings import INDEX_STORAGE, CONVERSATION_FILE

def load_chat_store():
    try:
        chat_store = SimpleChatStore.from_persist_path(
            CONVERSATION_FILE
        )
    except FileNotFoundError:
        chat_store = SimpleChatStore()
    return chat_store

def display_messages(chat_store, container):
    with container:
        for message in chat_store.get_messages(key="0"):
            with st.chat_message(message.role):
                st.markdown(message.content)

def initialize_chatbot(user_name, study_subject, 
                       chat_store, container, context):
    memory = ChatMemoryBuffer.from_defaults(
        token_limit=3000, 
        chat_store=chat_store, 
        chat_store_key="0"
    )  
    storage_context = StorageContext.from_defaults(
        persist_dir=INDEX_STORAGE
    )
    index = load_index_from_storage(
        storage_context, index_id="vector"
    )
    study_materials_engine = index.as_query_engine(
        similarity_top_k=3
    )
    study_materials_tool = QueryEngineTool(
        query_engine=study_materials_engine, 
        metadata=ToolMetadata(
            name="study_materials",
            description=(
                f"Dostarcza oficjalnych informacji na temat "
                f"{study_subject}. Używa niesformatowanej "
                f"treści pytania do narzędzia."
            ),
        )
    )
    agent = OpenAIAgent.from_tools(
        tools=[study_materials_tool], 
        memory=memory,
        system_prompt=(
            f"Masz na imię PITS, osobisty nauczyciel. Twoim "
            f"zadaniem jest pomoc {user_name} w nauce i "
            f"w lepszym zrozumieniu tematu: "
            f"{study_subject}. Obecnie omawiamy "
            f"slajd z taką zawartością: {context}"
        )
    )
    display_messages(chat_store, container)
    return agent

def chat_interface(agent, chat_store, container):  
    prompt = st.chat_input("Tutaj wpisz swoje pytanie:")
    if prompt:
        with container:
            with st.chat_message("user"):
                st.markdown(prompt)
            response = str(agent.chat(prompt))
            with st.chat_message("assistant"):
                st.markdown(response)
        #chat_store.persist(CONVERSATION_FILE)
