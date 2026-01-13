"""Verificar classes terapeuticas existentes"""
import json

data = json.load(open('data/monografias_backup.json', encoding='utf-8'))

# Coletar todas as classes unicas
classes = set()
for m in data:
    classe = m.get('classe_terapeutica', '')
    if classe:
        classes.add(classe)

print(f"Total de classes unicas: {len(classes)}")
print("\nClasses encontradas:")
for c in sorted(classes):
    print(f"  - {c}")
