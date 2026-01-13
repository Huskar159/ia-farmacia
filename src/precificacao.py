import re

# Tabela de preços base (R$ por mg ou ml)
# Valores fictícios para exemplo
TABELA_PRECOS = {
    "PARACETAMOL": 0.0005,
    "DIPIRONA": 0.0004,
    "IBUPROFENO": 0.0006,
    "CAFEÍNA": 0.0012,
    "VITAMINA C": 0.0008,
    "COLÁGENO": 0.0025,
    # Preço padrão para insumos não listados especificamente
    "DEFAULT": 0.0020
}

CUSTO_MAO_DE_OBRA = 15.00
CUSTO_EMBALAGEM_BASE = 5.00

def parse_dose(dose_str):
    """Extrai valor numérico e unidade da dose (ex: '500mg' -> 500.0, 'mg')."""
    if not dose_str:
        return 0, ""
        
    # Remove espaços e converte vírgula para ponto
    dose_str = dose_str.lower().replace(',', '.').strip()
    
    # Regex para separar número de texto
    match = re.search(r"(\d+\.?\d*)\s*([a-z]+)", dose_str)
    if match:
        valor = float(match.group(1))
        unidade = match.group(2)
        return valor, unidade
    return 0, ""

def parse_quantidade(qtd_str):
    """Extrai quantidade total numérica da string (ex: '30 cápsulas' -> 30)."""
    if not qtd_str:
        return 30 # Padrão
    match = re.search(r"(\d+)", str(qtd_str))
    if match:
        return int(match.group(1))
    return 30

def calcular_preco(formula):
    """Calcula o orçamento detalhado da fórmula."""
    insumos = formula.get("insumos", [])
    qtd_total = parse_quantidade(formula.get("quantidade_total", "30"))
    
    custo_insumos = 0
    detalhamento = []
    
    for item in insumos:
        nome = item.get("nome", "").upper()
        dose_str = item.get("dose", "0mg")
        valor_dose, unidade = parse_dose(dose_str)
        
        # Normalizar unidades para mg (simplificado)
        if unidade == "g":
            valor_dose *= 1000
        elif unidade == "mcg":
            valor_dose /= 1000
            
        # Buscar preço na tabela (busca parcial)
        preco_mg = TABELA_PRECOS["DEFAULT"]
        for k, v in TABELA_PRECOS.items():
            if k in nome:
                preco_mg = v
                break
        
        custo_item = valor_dose * preco_mg * qtd_total
        custo_insumos += custo_item
        
        detalhamento.append({
            "insumo": item.get("nome", "Insumo"),
            "dose_unitaria": dose_str,
            "quantidade": qtd_total,
            "subtotal": custo_item
        })
        
    preco_final = custo_insumos + CUSTO_MAO_DE_OBRA + CUSTO_EMBALAGEM_BASE
    
    return {
        "custo_insumos": round(custo_insumos, 2),
        "custo_mao_obra": round(CUSTO_MAO_DE_OBRA, 2),
        "custo_embalagem": round(CUSTO_EMBALAGEM_BASE, 2),
        "preco_final": round(preco_final, 2),
        "detalhamento_insumos": detalhamento
    }

def formatar_orcamento(preco_dict):
    return f"R$ {preco_dict['preco_final']:.2f}"