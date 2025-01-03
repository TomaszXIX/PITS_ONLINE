# Przygotuwuje pytanie testowe na podstawie wczytanych plików.

from llama_index.core import load_index_from_storage, StorageContext
from llama_index.program.evaporate.df import DFRowsProgram
from llama_index.program.openai import OpenAIPydanticProgram
from global_settings import INDEX_STORAGE, QUIZ_SIZE, QUIZ_FILE
import pandas as pd

def build_quiz(topic):
    df = pd.DataFrame(
        {
            "Pytanie_nr": pd.Series(dtype="int"),
            "Pytanie_tekst": pd.Series(dtype="str"),
            "Opcja1": pd.Series(dtype="str"),
            "Opcja2": pd.Series(dtype="str"),
            "Opcja3": pd.Series(dtype="str"),
            "Opcja4": pd.Series(dtype="str"),
            "Poprawna_odpowiedź": pd.Series(dtype="str"),
            "Uzasadnienie": pd.Series(dtype="str"),
        }
    )
    storage_context = StorageContext.from_defaults(persist_dir=INDEX_STORAGE)
    vector_index = load_index_from_storage(
        storage_context, index_id="vector"
    )
    df_rows_program = DFRowsProgram.from_defaults(
        pydantic_program_cls=OpenAIPydanticProgram, df=df
    )
    query_engine = vector_index.as_query_engine()
    response = query_engine.query(
        f"Utwórz {QUIZ_SIZE} różnych pytań quizowych, które będą odpowiednie do testowania wiedzy kandydata na temat {topic}. Każde pytanie będzie miało 4 opcje odpowiedzi. Pytania muszą być ogólnotematyczne, a nie specyficzne dla dostarczonego tekstu. Dla każdego pytania podaj również poprawną odpowiedź oraz uzasadnienie odpowiedzi. Uzasadnienie nie może odnosić się do dostarczonego kontekstu, żadnych egzaminów ani nazwy tematu. Tylko jedna  opowiedź powinna być poprawna."
    )
    result_obj = df_rows_program(input_str=response)
    new_df=result_obj.to_df(existing_df=df)
    new_df.to_csv(QUIZ_FILE, index=False)
    return new_df
   

