"""Analisar conteúdo do Volume 1 da Farmacopeia"""
from pypdf import PdfReader

pdf_path = "data/raw/volume1.pdf"
reader = PdfReader(pdf_path)

print(f"📖 Volume 1 - Total de páginas: {len(reader.pages)}")
print("=" * 60)

# Analisar sumário (primeiras páginas)
print("\n📋 PRIMEIRAS 10 PÁGINAS (Sumário/Índice):")
print("-" * 40)
for i in range(min(10, len(reader.pages))):
    page = reader.pages[i]
    text = page.extract_text()
    if text and text.strip():
        print(f"\n--- Página {i+1} ---")
        print(text[:400])

# Pular para o meio e ver conteúdo
print("\n\n📋 PÁGINAS DO MEIO (Conteúdo):")
print("-" * 40)
middle = len(reader.pages) // 2
for i in range(middle, min(middle + 3, len(reader.pages))):
    page = reader.pages[i]
    text = page.extract_text()
    if text and text.strip():
        print(f"\n--- Página {i+1} ---")
        print(text[:600])

# Procurar por termos úteis
print("\n\n🔍 BUSCANDO TERMOS ÚTEIS:")
print("-" * 40)

termos = ["classe terapêutica", "indicação", "indicações", "tratamento", "sintoma", "monografia"]
encontrados = {termo: 0 for termo in termos}

for i, page in enumerate(reader.pages):
    text = page.extract_text()
    if text:
        text_lower = text.lower()
        for termo in termos:
            if termo in text_lower:
                encontrados[termo] += 1

for termo, count in encontrados.items():
    print(f"  '{termo}': encontrado em {count} páginas")
