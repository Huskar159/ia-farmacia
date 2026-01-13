import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("❌ GOOGLE_API_KEY não encontrada no .env")
    exit()

genai.configure(api_key=api_key)

print("🔍 Buscando modelos disponíveis para sua chave...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f" - {m.name}")
except Exception as e:
    print(f"❌ Erro ao listar modelos: {e}")