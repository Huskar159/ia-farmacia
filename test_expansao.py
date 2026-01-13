"""Testar expansão inteligente para sintomas variados"""
import os
import sys
sys.path.insert(0, "src")

from core_ai import AssistenteFarmaceutico

assistente = AssistenteFarmaceutico("data/vectorstore")

# Testar sintomas variados
sintomas = [
    "dor no peito",
    "pontada no lado esquerdo do peito",
    "to com uma pontada no peito",
    "my chest hurts",  # inglês
    "dor d cabesa",    # erro ortográfico
]

print("=" * 60)
print("🧪 TESTE DE EXPANSÃO INTELIGENTE")
print("=" * 60)

for sintoma in sintomas:
    print(f"\n📝 Sintoma: '{sintoma}'")
    
    # Testar expansão LLM
    expansao_llm = assistente.expandir_query_inteligente(sintoma)
    print(f"   🤖 LLM sugeriu: {expansao_llm[:80]}...")
