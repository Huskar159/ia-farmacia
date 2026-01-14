"""
Servidor Webhook para WhatsApp Business API.
Recebe mensagens do WhatsApp e responde com recomendações farmacêuticas.
"""

import os
import json
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configurações do WhatsApp
VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "farmacia_token_123")
ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")

# Importar o sistema de IA
import sys
sys.path.insert(0, os.path.dirname(__file__))
from core_ai import AssistenteFarmaceutico
from precificacao import calcular_preco

# Inicializar assistente (lazy loading)
assistente = None

def get_assistente():
    """Inicializa o assistente farmacêutico (lazy loading)."""
    global assistente
    if assistente is None:
        vectorstore_path = os.getenv("VECTORSTORE_PATH", "data/vectorstore")
        assistente = AssistenteFarmaceutico(vectorstore_path)
    return assistente


@app.route("/", methods=["GET"])
def home():
    """Rota principal - verificação de saúde."""
    return jsonify({
        "status": "online",
        "service": "Farmácia Magistral WhatsApp Bot",
        "version": "1.0.0"
    })


@app.route("/webhook", methods=["GET"])
def verify_webhook():
    """
    Verificação do webhook pelo Meta.
    O Meta envia um GET para verificar se o webhook está ativo.
    """
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    
    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("✅ Webhook verificado com sucesso!")
        return challenge, 200
    else:
        print("❌ Falha na verificação do webhook")
        return "Forbidden", 403


@app.route("/webhook", methods=["POST"])
def receive_message():
    """
    Recebe mensagens do WhatsApp.
    Processa e responde com recomendação farmacêutica.
    """
    data = request.get_json()
    
    print(f"📩 Mensagem recebida: {json.dumps(data, indent=2)}")
    
    try:
        # Extrair informações da mensagem
        entry = data.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])
        
        if not messages:
            return jsonify({"status": "no_message"}), 200
        
        message = messages[0]
        sender_phone = message.get("from")
        message_type = message.get("type")
        
        # Processar apenas mensagens de texto
        if message_type == "text":
            text = message.get("text", {}).get("body", "")
            print(f"📝 Texto: {text} | De: {sender_phone}")
            
            # Processar mensagem e gerar resposta
            resposta = processar_mensagem(text)
            
            # Enviar resposta
            enviar_mensagem(sender_phone, resposta)
        
        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        print(f"❌ Erro ao processar mensagem: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


def processar_mensagem(texto: str) -> str:
    """
    Processa a mensagem do usuário e gera resposta.
    Detecta se é uma saudação ou sintomas.
    """
    texto_lower = texto.lower().strip()
    
    # Saudações
    saudacoes = ["oi", "olá", "ola", "bom dia", "boa tarde", "boa noite", "hello", "hi", "e aí", "eae"]
    
    if any(s in texto_lower for s in saudacoes) and len(texto_lower) < 30:
        return """👋 Olá! Bem-vindo à *Farmácia Magistral*!

Sou o assistente virtual e posso ajudar você a encontrar o medicamento manipulado ideal para seus sintomas.

💬 *Como funciona:*
Descreva seus sintomas e eu vou recomendar uma fórmula personalizada baseada na Farmacopeia Brasileira.

📝 *Exemplo:*
_"Estou com dor de cabeça e febre há 2 dias"_

Como posso ajudar você hoje?"""

    # Mensagens muito curtas
    if len(texto_lower) < 5:
        return "Por favor, descreva seus sintomas com mais detalhes para que eu possa ajudar você. 🙏"
    
    # Processar sintomas
    try:
        assistente = get_assistente()
        resultado = assistente.gerar_recomendacao(texto)
        
        return formatar_resposta_whatsapp(resultado, texto)
        
    except Exception as e:
        print(f"❌ Erro ao processar sintomas: {e}")
        return "Desculpe, ocorreu um erro ao processar sua solicitação. Por favor, tente novamente. 🙏"


def formatar_resposta_whatsapp(resultado: dict, sintomas: str) -> str:
    """
    Formata o resultado da IA para mensagem do WhatsApp.
    """
    # Se houver erro
    if "erro" in resultado:
        return f"""⚠️ *Não encontrei um medicamento específico*

{resultado.get('explicacao', 'Não foi possível encontrar medicamentos adequados para esses sintomas.')}

💡 *Sugestões:*
• Tente descrever os sintomas de forma diferente
• Consulte um profissional de saúde

_Baseado na Farmacopeia Brasileira 6ª Edição_"""

    # Formatar fórmula
    formula = resultado.get("formula", {})
    nome = formula.get("nome_sugerido", "Fórmula Personalizada")
    forma = formula.get("forma_farmaceutica", "Cápsula").capitalize()
    quantidade = formula.get("quantidade_total", "30 unidades")
    
    # Insumos
    insumos_texto = ""
    for insumo in formula.get("insumos", []):
        insumos_texto += f"• *{insumo.get('nome', 'N/A')}* - {insumo.get('dose', 'N/A')}\n"
    
    # Posologia
    posologia = resultado.get("posologia", "Conforme orientação médica")
    
    # Calcular preço
    try:
        preco = calcular_preco(formula)
        preco_texto = f"💰 *Preço:* R$ {preco['preco_final']:.2f}"
    except:
        preco_texto = "💰 *Preço:* Consulte a farmácia"
    
    # Alertas
    alertas = resultado.get("alertas_seguranca", [])
    alertas_texto = ""
    if alertas:
        alertas_texto = "\n⚠️ *Alertas:*\n" + "\n".join([f"• {a}" for a in alertas[:3]])
    
    return f"""💊 *{nome}*

🩺 *Seus sintomas:* {sintomas}

📋 *Fórmula Recomendada:*
{insumos_texto}
📦 *Forma:* {forma}
📊 *Quantidade:* {quantidade}

💊 *Posologia:*
{posologia}

{preco_texto}
{alertas_texto}

✅ *Deseja fazer o pedido?*
Responda com *SIM* para confirmar.

_⚠️ Este sistema é uma ferramenta de auxílio. Consulte um farmacêutico antes de usar._
_📚 Baseado na Farmacopeia Brasileira 6ª Ed._"""


def enviar_mensagem(telefone: str, texto: str):
    """
    Envia mensagem para o WhatsApp do cliente.
    """
    if not ACCESS_TOKEN or not PHONE_NUMBER_ID:
        print("⚠️ Credenciais do WhatsApp não configuradas!")
        return False
    
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": telefone,
        "type": "text",
        "text": {"body": texto}
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            print(f"✅ Mensagem enviada para {telefone}")
            return True
        else:
            print(f"❌ Erro ao enviar mensagem: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao enviar mensagem: {e}")
        return False


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"🚀 Servidor iniciando na porta {port}...")
    app.run(host="0.0.0.0", port=port, debug=True)
