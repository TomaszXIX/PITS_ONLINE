from llama_index.core import VectorStoreIndex, TreeIndex, load_index_from_storage
from llama_index.core import StorageContext
from global_settings import INDEX_STORAGE
from document_uploader import ingest_documents

def build_indexes(nodes):
    try:
        storage_context = StorageContext.from_defaults(
            persist_dir=INDEX_STORAGE
        )
        vector_index = load_index_from_storage(
            storage_context, index_id="vector"
        )
        tree_index = load_index_from_storage(
            storage_context, index_id="tree"
        )
        print("Wszystkie indeksy zostały wczytane z pamięci.")
    except Exception as e:
        print(f"Podczas wczytywania indeksów wystąpił błąd: {e}")
        storage_context = StorageContext.from_defaults()
        vector_index = VectorStoreIndex(
            nodes, storage_context=storage_context
        )
        vector_index.set_index_id("vector")
        tree_index = TreeIndex(
            nodes, storage_context=storage_context
        )
        tree_index.set_index_id("tree")
        storage_context.persist(
            persist_dir=INDEX_STORAGE
        )
        print("Utworzono i zapisano nowe indeksy.")
    return vector_index, tree_index

