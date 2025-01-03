# pip install llama-index-program-evaporate

from llama_index.core import TreeIndex, load_index_from_storage
from llama_index.core.storage import StorageContext 
from llama_index.core.extractors import KeywordExtractor
from llama_index.program.openai import OpenAIPydanticProgram
from llama_index.program.evaporate.df import DFRowsProgram
from llama_index.core.schema import TextNode
from llama_index.llms.openai import OpenAI

from global_settings import STORAGE_PATH, INDEX_STORAGE, CACHE_FILE, SLIDES_FILE
from logging_functions import log_action
from document_uploader import ingest_documents
from slides import Slide, SlideDeck
import pandas as pd
import streamlit as st
from collections import Counter

def generate_slides(topic):
    llm = OpenAI(temperature=0.5, model="gpt-4-1106-preview", max_tokens=4096)
    
    with st.spinner("Wczytywanie dokumentów..."):
        embedded_nodes = ingest_documents() # albo przesyła wszystko, albo używa zapisanych w pamięci podręcznej dokumentów, aby zwrócić węzły
        st.info("Dokumenty wczytane!")
    with st.spinner("Przygotwanie streszczeńi słów kluczowych..."):
        summary_nodes = []
        for node in embedded_nodes:
            # tworzymy kolejny zestaw węzłów zawierających jedynie podsumowania
            summary = node.metadata["section_summary"]
            summary_node = TextNode(text=summary)
            summary_nodes.append(node)

        # wyodrębniamy słowa kluczowe z podsumowań
        key_extractor = KeywordExtractor (keywords=10)
        entities =  key_extractor.extract(summary_nodes)
        flattened_keywords = []
        for entity in entities:
            if 'excerpt_keywords' in entity:
                excerpt_keywords = entity['excerpt_keywords']
                flattened_keywords.extend([keyword.strip() for keyword in excerpt_keywords.split(',')])
        keyword_counts = Counter(flattened_keywords)
        
        # Sortujemy słowa kluczowe według liczby ich wystąpień w porządku malejącym
        sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
        keywords_only = [keyword for keyword, count in sorted_keywords if count > 1]
        
        # eliminujemy wszelkie ogólne słowa kluczowe niezwiązane z tematem, używając dużego modelu językowego
        specific_keywords=""
        for i in range(0, len(keywords_only), 15):
            group = keywords_only[i:i+15]
            group_str = ', '.join(group)  # Przekształacenie listy na łańcuch znaków
            response = llm.complete(f"Wyeliminuj wszelkie słowa kluczowe, które są ogólne i nie są ściśle związane z tematem {topic}. Sformatuj jako oddzielone przecinkami. Wymień tylko pozostałe słowa kluczowe.: " + group_str)
            specific_keywords +=str(response) +','
        st.info("Słowa kluczowe i streszczenia gotowe!")
     
    with st.spinner("Tworzenie zarysu kursu..."):
        # generujemy zarys kursu, używając dużego modelu językowego
        response = llm.complete(f"Stwórz zarys kursu w języku polskim o ustalonej strukturze na temat {topic}. Zarys powinien być podzielony na sekcje, a każda sekcja powinna być podzielona na kilka tematów. Każda sekcja powinna zawierać wystarczającą liczbę tematów, aby pokryć cały obszar wiedzy. Zarys będzie zawierał stopniowe wprowadzanie koncepcji, zaczynając od ogólnego wprowadzenia do tematu, a następnie obejmować bardziej zaawansowane obszary. Odpowiedź powinna zawierać jedną linię na sekcję w tym formacie: <TYTUŁ SEKCJI, TEMAT 1, TEMAT 2, TEMAT 3, ... TEMAT n>. Upewnij się, że zarys w pełni pokrywa następujące słowa kluczowe: {specific_keywords}.")
        
        df = pd.DataFrame({"Section": pd.Series(dtype="str"),"Topics": pd.Series(dtype="str")})
        df_rows_program = DFRowsProgram.from_defaults(pydantic_program_cls=OpenAIPydanticProgram, df=df)
        result_obj = df_rows_program(input_str=response)
        outline=result_obj.to_df(existing_df=df)
        #outline.to_csv('course_outline.csv', sep=';', index=False) # opcjonalnie, zapisujemy zarys w pliku CSV
        st.info("Zarys kursu gotowy!")
        
    with st.spinner("Tworzenie slajdów kursu i treśći. To może zająć trochę czasu...."):
        #wczytanie zapisynych indeksów
        storage_context = StorageContext.from_defaults(persist_dir=INDEX_STORAGE)
        tree_index = load_index_from_storage(storage_context, index_id="tree")
       
        #outline = pd.read_csv('course_outline.csv', delimiter=';') 
        # tworzymy slajdy i narrację dla każdego slajdu
        slides = [] 
        for index, row in outline.iterrows():
            section = row['Section']
            topics = row['Topics'].split('; ')
            for slide_topic in topics:
                print(f"Generowanie treści dla: {section} - {slide_topic}")
                query_engine = tree_index.as_query_engine(response_mode="compact")
                narration = str(query_engine.query(f"Jesteś ekspertem i nauczycielem z dziedziny: {topic}. Aktulanie omawiasz '{section}'. Wprowadż i wyjaśnij '{slide_topic}' swojemu studentowi. Odpowiadaj jak byś był nauczycielem."))
                summary = llm.complete(f"Podsumuj kluczowe pojęcia z tego tekstu w maksymalnie 7 bardzo krótkich punktach slajdów bez użycia czasowników: {narration}\n Temat prezetacji to {topic}\n Tytuł slajdu to {section+'-'+slide_topic} Wymień punkty listy oddzieone za pomocą przecinków, w ten sposób: PUNKT1, PUNKT2, ...: ")
                bullets = str(summary).split(';')
                # Utwórz nowy obiekt Slide i dodaj go do listy
                slide = Slide(section, slide_topic, narration, bullets)
                slides.append(slide)
        st.info("Slajdy i treść wygenerowana!")
        
    slide_deck = SlideDeck(topic, slides)
    slide_deck.save_to_file(SLIDES_FILE)
    

    