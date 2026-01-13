"""Verificar quais classes NAO estao cobertas pelo mapeamento"""
import json

data = json.load(open('data/monografias_backup.json', encoding='utf-8'))

# Mapeamento atual (chaves)
mapeamento_chaves = [
    'analgésico', 'antipirético', 'opioide', 'agonista',
    'anti-inflamatório', 'antirreumático', 'corticosteroide',
    'antibacteriano', 'antibiótico', 'antimicrobiano', 'tuberculostático',
    'antifúngico', 'antiviral', 'antirretroviral',
    'anti-helmíntico', 'antiparasitário', 'escabicida',
    'broncodilatador', 'antiasmático', 'adrenérgico', 'mucolítico', 'expectorante', 'descongestionante',
    'anti-hipertensivo', 'antiarrítmico', 'antianginoso', 'vasodilatador', 'diurético', 'cardiotônico',
    'ansiolítico', 'benzodiazepínico', 'sedativo', 'hipnótico', 'anticonvulsivante', 'antidepressivo',
    'antipsicótico', 'neuroléptico', 'antiparkinsoniano', 'relaxante muscular',
    'antiácido', 'antissecretor', 'antiemético', 'laxante', 'antiespasmódico', 'colagogo',
    'hipoglicemiante', 'antidiabético',
    'anti-histamínico', 'antialérgico', 'antipruriginoso',
    'vitamina', 'suplemento', 'hematopoiético', 'antianêmico',
    'protetor', 'ceratolítico', 'queratolítico', 'despigmentante',
    'anestésico', 'anticoagulante', 'hormônio', 'contraceptivo', 'imunossupressor'
]

# Verificar classes nao cobertas
classes_nao_cobertas = set()
for m in data:
    classe = m.get('classe_terapeutica', '').lower()
    if classe:
        coberta = any(chave in classe for chave in mapeamento_chaves)
        if not coberta:
            classes_nao_cobertas.add(m.get('classe_terapeutica', ''))

print(f"Classes NAO cobertas pelo mapeamento: {len(classes_nao_cobertas)}")
print()
for c in sorted(classes_nao_cobertas):
    print(f"  - {c}")
