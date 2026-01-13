import pdfplumber
import re

# Analisar Volume 2 - extrair nome e classe corretamente
pdf = pdfplumber.open('data/raw/volume2.pdf')

print("=== Analisando estrutura das monografias ===")

# Vamos analisar paginas individuais para entender o padrao
for i in range(16, 25):  # Paginas 16-24
    text = pdf.pages[i].extract_text()
    if text:
        print(f"\n{'='*60}")
        print(f"PAGINA {i+1}")
        print('='*60)
        
        lines = text.split('\n')
        # Mostrar primeiras 15 linhas para entender estrutura
        for j, line in enumerate(lines[:15]):
            print(f"{j+1:2d}: {line}")
        
        # Buscar CLASSE TERAPEUTICA
        for j, line in enumerate(lines):
            if "CLASSE TERAPÊUTICA" in line:
                print(f"\n>> CLASSE TERAPEUTICA encontrada na linha {j+1}:")
                for k in range(j, min(j+3, len(lines))):
                    print(f"   {lines[k]}")
                break

pdf.close()
