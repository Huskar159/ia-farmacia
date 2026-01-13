# 💊 Assistente de Farmácia Magistral

Sistema de recomendação de fórmulas magistrais baseado na **Farmacopeia Brasileira 6ª Edição**.

Analisa sintomas do paciente usando IA (Google Gemini) e sugere medicamentos manipulados apropriados.

## 🚀 Demo

[Acessar aplicação](https://farmacia-magistral.streamlit.app) *(após deploy)*

## ✨ Funcionalidades

- 🔍 **Análise inteligente de sintomas** - Entende linguagem natural, gírias e erros ortográficos
- 💊 **Recomendação de fórmulas** - Baseado em 588 monografias da Farmacopeia
- ⚠️ **Alertas de segurança** - Contraindicações e interações medicamentosas
- 💰 **Precificação automática** - Calcula custo da fórmula manipulada
- 📚 **100% Farmacopeia Brasileira** - Fonte oficial, não inventa medicamentos

## 📋 Pré-requisitos

- Python 3.11+
- Chave de API do Google Gemini

## 🛠️ Instalação Local

```bash
# Clonar repositório
git clone https://github.com/seu-usuario/farmacia-magistral.git
cd farmacia-magistral

# Criar ambiente virtual
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp .env.example .env
# Editar .env e adicionar GOOGLE_API_KEY

# Executar
streamlit run src/app.py
```

## ☁️ Deploy no Streamlit Cloud

1. **Fork este repositório** no GitHub
2. Acesse [streamlit.io/cloud](https://streamlit.io/cloud)
3. Clique em **"New app"**
4. Conecte seu repositório GitHub
5. Configure:
   - **Main file path:** `src/app.py`
   - **Python version:** 3.11
6. Em **"Advanced settings" > "Secrets"**, adicione:
   ```toml
   GOOGLE_API_KEY = "sua_chave_aqui"
   ```
7. Clique em **"Deploy"**

## 🔐 Variáveis de Ambiente

| Variável | Descrição | Obrigatório |
|----------|-----------|-------------|
| GOOGLE_API_KEY | Chave da API Google Gemini | ✅ |
| LLM_PROVIDER | Provider do LLM (gemini) | ❌ |
| GEMINI_MODEL | Modelo Gemini (gemini-2.0-flash) | ❌ |
| TOP_K_RESULTS | Número de resultados por busca | ❌ |

## 📁 Estrutura do Projeto

```
farmacia-magistral/
├── src/
│   ├── app.py           # Interface Streamlit
│   ├── core_ai.py       # Motor RAG + LLM
│   ├── ingestor.py      # Extração de PDFs
│   └── precificacao.py  # Sistema de preços
├── data/
│   ├── vectorstore/     # Base de dados vetorial
│   ├── raw/             # PDFs da Farmacopeia
│   └── monografias_backup.json
├── .streamlit/
│   └── config.toml      # Configuração Streamlit
├── requirements.txt
└── README.md
```

## ⚠️ Aviso Legal

Este sistema é uma ferramenta de **AUXÍLIO** para farmacêuticos habilitados.

- Todas as recomendações **DEVEM** ser validadas por profissional responsável  
- **NÃO substitui** avaliação clínica ou diagnóstico médico
- Baseado na **Farmacopeia Brasileira 6ª Edição**
- Uso restrito a ambiente profissional regulamentado

## 📄 Licença

Este projeto é para uso educacional e profissional.