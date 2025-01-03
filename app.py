from user_onboarding import user_onboarding
from session_functions import load_session, delete_session, save_session
from logging_functions import reset_log
from quiz_UI import show_quiz
from training_UI import show_training_UI
import streamlit as st
import os

def main():
    st.set_page_config(layout="wide")
    st.sidebar.title('PITS')
    st.sidebar.markdown('### Twój osobisty inteligentny nauczyciel')

    if 'OPENAI_API_KEY' not in st.session_state or not st.session_state['OPENAI_API_KEY']:
        api_key = st.text_input("Wpisz swój klucz OpenAI (zostaw to pole puste, jeśli uruchamiasz aplikację lokalnie): ")
        st.session_state['OPENAI_API_KEY'] = api_key
        os.environ['OPENAI_API_KEY'] = api_key

    # Sprawdź, czy użytkownik wraca i czy zdecydował się na quiz.
    if 'show_quiz' in st.session_state and st.session_state['show_quiz']:
        show_quiz(st.session_state['study_subject'])  # Natychmiast wyświetl ekran quizu.
    elif 'resume_session' in st.session_state and st.session_state['resume_session']:
        # Jeśli wznawiasz, wyczyść poprzednią zawartość i wyświetl interfejs użytkownika do szkolenia.
        st.session_state['show_quiz'] = False  # Upewnij się, że quiz nie jest wyświetlany.
        show_training_UI(st.session_state['user_name'], st.session_state['study_subject'])
    elif not load_session(st.session_state):
        user_onboarding()  # Pokaż ekran powitalny dla nowych użytkowników.
    else:
        # Dla powracających użytkowników wyświetl opcje wznowienia lub rozpoczęcia nowej sesji.
        st.write(f"Witaj z powrotem {st.session_state['user_name']}!")
        col1, col2 = st.columns(2)
        if col1.button(f"Wróć do nauki {st.session_state['study_subject']}"):
            # Oznacz sesję do wznowienia i uruchom ponownie, aby wyczyścić poprzednią zawartość.
            st.session_state['resume_session'] = True
            st.rerun()
        if col2.button('Rozpocznij nową sesję'):
            delete_session(st.session_state)
            reset_log()
            # Wyczyść stan sesji i uruchom ponownie, aby rozpocząć od nowa.
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

if __name__ == "__main__":
    main()
