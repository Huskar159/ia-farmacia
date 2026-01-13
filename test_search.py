"""Teste rapido do vectorstore - v2"""
import os
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

load_dotenv()

vectorstore_path = os.getenv("VECTORSTORE_PATH", "data/vectorstore")

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

vectorstore = Chroma(
    persist_directory=vectorstore_path,
    embedding_function=embeddings
)

# Testar buscas diferentes
buscas = [
    "mucolítico tosse catarro",
    "acetilcisteína",
    "analgésico dor febre",
    "paracetamol"
]

for busca in buscas:
    print(f"\n{'='*60}")
    print(f"Busca: '{busca}'")
    print('='*60)
    
    resultados = vectorstore.similarity_search_with_score(busca, k=5)
    
    for i, (doc, score) in enumerate(resultados):
        nome = doc.metadata.get('nome', 'N/A')
        classe = doc.metadata.get('classe_terapeutica', '')
        indicacoes = doc.metadata.get('indicacoes', '')
        print(f"{i+1}. [{score:.2f}] {nome}")
        if classe:
            print(f"      Classe: {classe[:50]}")
        if indicacoes:
            print(f"      Indicacoes: {indicacoes[:50]}")
