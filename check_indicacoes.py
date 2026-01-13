"""Verificar indicacoes no JSON"""
import json

data = json.load(open('data/monografias_backup.json', encoding='utf-8'))

# Buscar medicamentos que deveriam aparecer
print("=== MEDICAMENTOS PARA TOSSE ===")
for m in data:
    indicacoes = m.get('indicacoes', [])
    if 'tosse' in indicacoes or 'catarro' in indicacoes:
        print(f"  {m['nome']} - Classe: {m.get('classe_terapeutica', '')[:40]} - Indicacoes: {indicacoes}")

print("\n=== MEDICAMENTOS PARA HERPES ===")
for m in data:
    indicacoes = m.get('indicacoes', [])
    classe = m.get('classe_terapeutica', '').lower()
    if 'herpes' in indicacoes or 'antiviral' in classe:
        print(f"  {m['nome']} - Classe: {m.get('classe_terapeutica', '')[:40]} - Indicacoes: {indicacoes}")

print("\n=== MEDICAMENTOS PARA PRESSAO ALTA ===")
for m in data:
    indicacoes = m.get('indicacoes', [])
    if 'pressao alta' in indicacoes or 'hipertensao' in indicacoes:
        print(f"  {m['nome']} - Classe: {m.get('classe_terapeutica', '')[:40]} - Indicacoes: {indicacoes}")

print("\n=== MEDICAMENTOS PARA ASMA ===")
for m in data:
    indicacoes = m.get('indicacoes', [])
    if 'asma' in indicacoes or 'falta de ar' in indicacoes:
        print(f"  {m['nome']} - Classe: {m.get('classe_terapeutica', '')[:40]} - Indicacoes: {indicacoes}")
