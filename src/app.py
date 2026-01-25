"""
Interface Web do Assistente de Farmácia Magistral.
Desenvolvido com Streamlit para uso interno por farmacêuticos.
Suporta deploy local (.env) e Streamlit Cloud (st.secrets).
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv

import streamlit as st

# Carregar variáveis de ambiente
# Prioridade: st.secrets (Streamlit Cloud) > .env (local)
load_dotenv()

def get_secret(key: str, default: str = "") -> str:
    """Obtém secret do Streamlit Cloud ou .env local."""
    try:
        # Tentar Streamlit secrets primeiro (para cloud)
        return st.secrets.get(key, os.getenv(key, default))
    except:
        # Fallback para .env local
        return os.getenv(key, default)

# Configurar variáveis de ambiente para o sistema
if "GOOGLE_API_KEY" not in os.environ:
    api_key = get_secret("GOOGLE_API_KEY")
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key

# Também exportar GEMINI_MODEL se definido nos secrets
if "GEMINI_MODEL" not in os.environ:
    gemini_model = get_secret("GEMINI_MODEL")
    if gemini_model:
        os.environ["GEMINI_MODEL"] = gemini_model

# Exportar configurações do Groq se definidas nos secrets
if "GROQ_API_KEY" not in os.environ:
    groq_key = get_secret("GROQ_API_KEY")
    if groq_key:
        os.environ["GROQ_API_KEY"] = groq_key

if "LLM_PROVIDER" not in os.environ:
    llm_provider = get_secret("LLM_PROVIDER")
    if llm_provider:
        os.environ["LLM_PROVIDER"] = llm_provider

from precificacao import calcular_preco, formatar_orcamento


# Configuração da página
st.set_page_config(
    page_title="Assistente Farmácia Magistral",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# CSS customizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
    }
    .warning-box {
        background-color: #FFF3CD;
        border-left: 5px solid #FFC107;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #D4EDDA;
        border-left: 5px solid #28A745;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #F8D7DA;
        border-left: 5px solid #DC3545;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


def inicializar_sessao():
    """Inicializa variáveis de sessão."""
    if "assistente" not in st.session_state:
        vectorstore_path = os.getenv("VECTORSTORE_PATH", "data/vectorstore")
        
        # Verificar se vectorstore existe
        if not os.path.exists(vectorstore_path):
            st.error("❌ Base de dados não encontrada! Execute primeiro: `python src/ingestor.py`")
            st.stop()
        
        with st.spinner("🔄 Iniciando motor de IA... Por favor, aguarde alguns segundos..."):
            from core_ai import AssistenteFarmaceutico
            st.session_state.assistente = AssistenteFarmaceutico(vectorstore_path)
    
    if "historico" not in st.session_state:
        st.session_state.historico = []


def exibir_disclaimer():
    """Exibe aviso legal obrigatório."""
    st.markdown("""
    <div class="warning-box">
        <h3>⚠️ AVISO LEGAL - USO EXCLUSIVO PROFISSIONAL</h3>
        <p><strong>Este sistema é uma ferramenta de AUXÍLIO para farmacêuticos habilitados.</strong></p>
        <ul>
            <li>Todas as recomendações DEVEM ser validadas por profissional responsável técnico</li>
            <li>Este sistema NÃO substitui avaliação clínica ou diagnóstico médico</li>
            <li>Baseado na Farmacopeia Brasileira 6ª Edição</li>
            <li>Uso restrito a ambiente profissional regulamentado</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)


def exibir_sidebar():
    """Exibe menu lateral com informações."""
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/pill.png", width=80)
        st.title("💊 Farmácia Magistral")
        st.markdown("---")
        
        st.subheader("📊 Status do Sistema")
        provider = os.getenv("LLM_PROVIDER", "gemini").upper()
        st.success(f"✅ Modelo: {provider}")
        
        vectorstore_path = os.getenv("VECTORSTORE_PATH", "data/vectorstore")
        if os.path.exists(vectorstore_path):
            st.success("✅ Base de dados: OK")
        else:
            st.error("❌ Base não indexada")
        
        st.markdown("---")
        
        st.subheader("📖 Guia Rápido")
        st.markdown("""
        1. Digite os **sintomas** do paciente
        2. Clique em **Gerar Recomendação**
        3. Revise a **fórmula** proposta
        4. Valide os **alertas** de segurança
        5. Visualize o **orçamento**
        6. Registre no **histórico**
        """)
        
        st.markdown("---")
        
        if st.button("🗑️ Limpar Histórico", use_container_width=True):
            st.session_state.historico = []
            st.rerun()


def exibir_resultado(resultado: dict):
    """Exibe resultado da recomendação de forma estruturada."""
    
    # Verificar se há erro
    if "erro" in resultado:
        tipo_erro = resultado.get("tipo_erro", "ERRO_GENERICO")
        
        if tipo_erro == "LIMITACAO_FARMACOPEIA":
            # Erro por limitação da Farmacopeia - mostrar de forma explicativa
            st.markdown("""
            <div style="background-color: #FFF3CD; border-left: 5px solid #FFC107; padding: 1.5rem; border-radius: 5px; margin: 1rem 0;">
                <h3>⚠️ Medicamento Não Disponível na Farmacopeia</h3>
            </div>
            """, unsafe_allow_html=True)
            
            st.info(f"""
**📋 Sintomas informados:** {resultado.get('sintomas_informados', 'N/A')}

**📚 Por que não encontramos um medicamento?**

A Farmacopeia Brasileira 6ª Edição é um documento oficial que contém monografias de medicamentos específicos. 
Nem todos os medicamentos existentes no mercado estão catalogados neste documento.

**Isso NÃO significa que não existe tratamento** - apenas que o medicamento adequado não está disponível 
na base de dados oficial utilizada por este sistema.
            """)
            
            st.markdown("### 💡 Sugestões:")
            sugestoes = resultado.get("sugestoes", [])
            for sugestao in sugestoes:
                st.markdown(f"- {sugestao}")
            
            st.markdown("""
---
**📖 Sobre a Farmacopeia Brasileira:**  
Este sistema utiliza exclusivamente dados extraídos da Farmacopeia Brasileira 6ª Edição (Volumes 1 e 2), 
que é a referência oficial para padrões de qualidade de medicamentos no Brasil.
            """)
        else:
            # Erro genérico
            st.markdown(f"""
            <div class="error-box">
                <h3>❌ Erro na Geração</h3>
                <p><strong>{resultado['erro']}</strong></p>
                {f"<p><em>{resultado.get('detalhes', '')}</em></p>" if 'detalhes' in resultado else ""}
            </div>
            """, unsafe_allow_html=True)
        return
    
    # === ALERTAS CRÍTICOS (Medicamentos Controlados) ===
    alertas_criticos = resultado.get("alertas_criticos", [])
    if alertas_criticos:
        st.markdown("""
        <div style="background-color: #FF4444; color: white; padding: 1.5rem; border-radius: 10px; margin-bottom: 1.5rem;">
            <h2 style="color: white; margin: 0;">🚨 ATENÇÃO: MEDICAMENTO CONTROLADO DETECTADO</h2>
            <p style="margin: 0.5rem 0 0 0;">Esta recomendação requer análise cuidadosa do farmacêutico responsável.</p>
        </div>
        """, unsafe_allow_html=True)
        
        for alerta in alertas_criticos:
            st.error(alerta)
        
        st.markdown("---")
    
    # Exibir fórmula
    formula = resultado.get("formula", {})
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 💊 Fórmula Recomendada")
        
        st.markdown(f"**Nome Sugerido:** {formula.get('nome_sugerido', 'N/A')}")
        st.markdown(f"**Forma Farmacêutica:** {formula.get('forma_farmaceutica', 'N/A').capitalize()}")
        st.markdown(f"**Quantidade Total:** {formula.get('quantidade_total', 'N/A')}")
        
        st.markdown("#### 🧪 Composição:")
        for i, insumo in enumerate(formula.get("insumos", []), 1):
            nome_insumo = insumo.get('nome', 'N/A')
            dose_insumo = insumo.get('dose', 'N/A')
            
            # Verificar se é medicamento controlado para destacar
            medicamentos_controlados = resultado.get("medicamentos_controlados", [])
            eh_controlado = any(med["nome"].upper() in nome_insumo.upper() for med in medicamentos_controlados)
            
            if eh_controlado:
                with st.expander(f"🚨 {i}. {nome_insumo} - {dose_insumo} (CONTROLADO)"):
                    st.write(f"**Justificativa:** {insumo.get('justificativa', 'Não especificada')}")
                    st.error("⚠️ Este é um medicamento controlado. Requer receita especial.")
            else:
                with st.expander(f"{i}. {nome_insumo} - {dose_insumo}"):
                    st.write(f"**Justificativa:** {insumo.get('justificativa', 'Não especificada')}")
        
        st.markdown("#### 📋 Posologia:")
        st.info(resultado.get("posologia", "Não especificada"))
        
        st.markdown("#### 📚 Justificativa Técnica:")
        st.write(resultado.get("justificativa_tecnica", "Não fornecida"))
    
    with col2:
        # Se tem medicamentos controlados, mostrar seção especial primeiro
        if alertas_criticos:
            st.markdown("### 🚨 Medicamentos Controlados")
            for med in resultado.get("medicamentos_controlados", []):
                st.markdown(f"""
                <div style="background-color: #FFE4E1; border-left: 4px solid #FF4444; padding: 0.8rem; margin-bottom: 0.5rem; border-radius: 4px;">
                    <strong>{med['nome']}</strong><br>
                    <small>Tarja: {med['tarja']} | {med['classe']}</small><br>
                    <small style="color: #CC0000;">Risco: {med['risco']}</small>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("---")
        
        st.markdown("### ⚠️ Alertas de Segurança")
        
        alertas = resultado.get("alertas_seguranca", [])
        if alertas:
            for alerta in alertas:
                st.warning(alerta)
        else:
            if not alertas_criticos:
                st.success("✅ Nenhum alerta específico")
            else:
                st.info("ℹ️ Verifique os alertas críticos acima.")
        
        st.markdown("### 📖 Referências")
        referencias = resultado.get("referencias", ["Farmacopeia Brasileira 6ª Ed."])
        for ref in referencias:
            st.caption(f"• {ref}")
    
    # Calcular e exibir preço
    st.markdown("---")
    st.markdown("### 💰 Precificação")
    
    try:
        precificacao = calcular_preco(formula)
        
        col_preco1, col_preco2, col_preco3, col_preco4 = st.columns(4)
        
        with col_preco1:
            st.metric("Insumos", f"R$ {precificacao['custo_insumos']:.2f}")
        with col_preco2:
            st.metric("Mão de Obra", f"R$ {precificacao['custo_mao_obra']:.2f}")
        with col_preco3:
            st.metric("Embalagem", f"R$ {precificacao['custo_embalagem']:.2f}")
        with col_preco4:
            st.metric("💵 TOTAL", f"R$ {precificacao['preco_final']:.2f}", delta=None)
        
        with st.expander("📊 Detalhamento de Custos"):
            for item in precificacao["detalhamento_insumos"]:
                st.write(f"**{item['insumo']}**")
                st.write(f"  - Dose unitária: {item['dose_unitaria']}")
                st.write(f"  - Quantidade: {item['quantidade']} unidades")
                st.write(f"  - Subtotal: R$ {item['subtotal']:.2f}")
                if "observacao" in item:
                    st.caption(item['observacao'])
                st.markdown("---")
        
        # Botão para adicionar ao histórico
        if st.button("➕ Adicionar ao Histórico", use_container_width=True):
            st.session_state.historico.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "sintomas": resultado['metadados']['sintomas_originais'],
                "formula": formula.get('nome_sugerido', 'Sem nome'),
                "preco": precificacao['preco_final']
            })
            st.success("✅ Adicionado ao histórico!")
            st.rerun()
    
    except Exception as e:
        st.error(f"Erro ao calcular preço: {str(e)}")


def exibir_historico():
    """Exibe histórico de recomendações."""
    if not st.session_state.historico:
        st.info("📝 Nenhuma recomendação no histórico ainda.")
        return
    
    st.markdown("### 📋 Histórico de Atendimentos")
    
    for i, item in enumerate(reversed(st.session_state.historico), 1):
        with st.expander(f"{i}. {item['timestamp']} - {item['formula']}"):
            st.write(f"**Sintomas:** {item['sintomas']}")
            st.write(f"**Fórmula:** {item['formula']}")
            st.write(f"**Preço:** R$ {item['preco']:.2f}")


def main():
    """Função principal da aplicação."""
    
    # Inicializar
    inicializar_sessao()
    
    # Sidebar
    exibir_sidebar()
    
    # Header
    st.markdown('<h1 class="main-header">💊 Assistente de Farmácia Magistral</h1>', unsafe_allow_html=True)
    
    # Disclaimer
    exibir_disclaimer()
    
    # Interface principal
    st.markdown("---")
    
    # Tabs
    tab1, tab2 = st.tabs(["🔍 Gerar Recomendação", "📋 Histórico"])
    
    with tab1:
        st.markdown("### 🩺 Sintomas do Paciente")
        
        sintomas = st.text_area(
            "Digite os sintomas relatados:",
            placeholder="Ex: dor de cabeça forte, febre e náusea há 2 dias",
            height=100,
            help="Descreva os sintomas de forma clara e objetiva"
        )
        
        col_btn1, col_btn2 = st.columns([1, 3])
        
        with col_btn1:
            gerar_btn = st.button("🚀 Gerar Recomendação", type="primary", use_container_width=True)
        
        if gerar_btn:
            if not sintomas.strip():
                st.warning("⚠️ Por favor, insira os sintomas do paciente.")
            else:
                with st.spinner("🔄 Processando... Buscando insumos na Farmacopeia..."):
                    resultado = st.session_state.assistente.gerar_recomendacao(sintomas)
                
                st.markdown("---")
                exibir_resultado(resultado)
    
    with tab2:
        exibir_historico()
    
    # Footer
    st.markdown("---")
    st.caption("Desenvolvido com ❤️ para farmacêuticos | Baseado na Farmacopeia Brasileira 6ª Edição")


if __name__ == "__main__":
    main()