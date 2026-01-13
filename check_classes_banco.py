"""Verificar medicamentos por classe no banco"""
import json

data = json.load(open('data/monografias_backup.json', encoding='utf-8'))

classes_buscar = [
    ('antiácido', 'ANTIÁCIDO'),
    ('antiemético', 'ANTIEMÉTICO'),
    ('laxante', 'LAXANTE'),
    ('antifúngico', 'ANTIFÚNGICO'),
    ('broncodilatador', 'BRONCODILATADOR'),
    ('antidiarreico', 'ANTIDIARREICO'),
    ('hipoglicemiante', 'HIPOGLICEMIANTE'),
]

for classe_lower, classe_display in classes_buscar:
    print(f"\n=== {classe_display} ===")
    encontrados = []
    for m in data:
        ct = m.get('classe_terapeutica', '').lower()
        if classe_lower in ct:
            encontrados.append(m['nome'])
    
    if encontrados:
        print(f"Encontrados {len(encontrados)}:")
        for nome in encontrados[:5]:
            print(f"  - {nome}")
        if len(encontrados) > 5:
            print(f"  ... e mais {len(encontrados)-5}")
    else:
        print("  NENHUM ENCONTRADO!")
