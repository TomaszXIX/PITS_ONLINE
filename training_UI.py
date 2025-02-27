import streamlit as st
from slides import Slide, SlideDeck
import json
from openai import OpenAI
from pathlib import Path
from conversation_engine import initialize_chatbot, chat_interface, load_chat_store

def show_training_UI(user_name, study_subject):
    # Wczytanie slajdów
    slide_deck = SlideDeck.load_from_file("cache/slides.json")
    
    # Wyświetlenie tytułu i kontrolek nawigacyjnych slajdu
    st.sidebar.markdown("## " + slide_deck.topic)
    current_slide_index = st.sidebar.number_input("Slajd numer:", min_value=0, max_value=len(slide_deck.slides)-1, value=0, step=1)
    current_slide = slide_deck.slides[current_slide_index]
    if st.sidebar.button("Zmiana tekstu"):
            st.session_state.show_narration = not st.session_state.get('show_narration', False)

    # Wyświetlenie slajdów i narracji w głównej części ekranu
    col1, col2 = st.columns([0.7,0.3],gap="medium")
    with col1:
        st.markdown(current_slide.render(display_narration=st.session_state.get('show_narration', False)), unsafe_allow_html=True)

    # Integracja czatbota w pasku bocznym
    with col2:
        st.header("💬 Czatbot PITS")
        st.success(f"Witaj, {user_name}. Odpowiem na Twoje pytania na temat: {study_subject}")
        #with st.spinner("Preparing the chatbot..."):
        chat_store = load_chat_store()
        container = st.container(height=600)
        context = current_slide.render(display_narration=False)
        agent = initialize_chatbot(user_name, study_subject, chat_store, container, context)
        chat_interface(agent, chat_store, container)
        
