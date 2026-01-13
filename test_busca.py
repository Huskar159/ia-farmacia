"""Testar busca diretamente no vectorstore"""
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

# Testar buscas específicas
buscas = [
    "tosse com catarro",
    "ACETILCISTEÍNA mucolítico tosse",  # busca direta pelo nome
    "herpes virus antiviral",
    "ACICLOVIR antiviral herpes",
    "pressão alta hipertensão",
    "CAPTOPRIL anti-hipertensivo",
    "asma falta de ar broncodilatador",
    "AMINOFILINA broncodilatador asma"
]

for busca in buscas:
    print(f"\n{'='*60}")
    print(f"Busca: '{busca}'")
    print('='*60)
    
    resultados = vectorstore.similarity_search_with_score(busca, k=3)
    
    for i, (doc, score) in enumerate(resultados):
        nome = doc.metadata.get('nome', 'N/A')
        indicacoes = doc.metadata.get('indicacoes', '')
        # Mostrar primeiras 100 chars do conteudo
        conteudo = doc.page_content[:150].replace('\n', ' ')
        print(f"{i+1}. [{score:.2f}] {nome}")
        print(f"      Indicacoes: {indicacoes[:60]}...")
        print(f"      Texto: {conteudo}...")
