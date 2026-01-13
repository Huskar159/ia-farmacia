"""Debug: Por que o LLM rejeita 'pontada no lado esquerdo do peito'?"""
import os
import sys
sys.path.insert(0, "src")

from core_ai import AssistenteFarmaceutico

assistente = AssistenteFarmaceutico("data/vectorstore")

sintoma = "pontada no lado esquerdo do peito"

print("=" * 60)
print(f"🔍 DEBUG COMPLETO: '{sintoma}'")
print("=" * 60)

# 1. Testar expansão LLM
print("\n1️⃣ EXPANSÃO LLM:")
expansao = assistente.expandir_query_inteligente(sintoma)
print(f"   Resultado: {expansao}")

# 2. Buscar insumos
print("\n2️⃣ BUSCA DE INSUMOS:")
insumos = assistente.buscar_insumos_relevantes(sintoma, top_k=5)
print(f"   Encontrados: {len(insumos)} insumos")
for i, ins in enumerate(insumos[:5], 1):
    nome = ins['metadata'].get('nome', 'N/A')
    classe = ins['metadata'].get('classe_terapeutica', 'N/A')
    print(f"   {i}. {nome} ({classe})")

# 3. Ver o prompt que seria enviado
print("\n3️⃣ PROMPT PARA O LLM:")
if insumos:
    prompt = assistente.criar_prompt_recomendacao(sintoma, insumos)
    print(f"   (Tamanho: {len(prompt)} caracteres)")
    print(f"   Primeiros 500 chars: {prompt[:500]}...")

# 4. Gerar recomendação
print("\n4️⃣ RESULTADO FINAL:")
resultado = assistente.gerar_recomendacao(sintoma)
if "erro" in resultado:
    print(f"   ❌ ERRO: {resultado.get('erro')}")
    print(f"   Tipo: {resultado.get('tipo_erro')}")
else:
    formula = resultado.get("formula", {})
    print(f"   ✅ Formula: {formula.get('nome_sugerido')}")
    for ins in formula.get("insumos", []):
        print(f"      - {ins.get('nome')}: {ins.get('dose')}")
