# 📱 Guia: Configurar WhatsApp Business API (GRÁTIS)

## Passo 1: Criar Conta Meta for Developers

1. Acesse: **https://developers.facebook.com**
2. Clique em **"Get Started"** ou **"Começar"**
3. Faça login com sua conta Facebook
4. Complete o registro como desenvolvedor

---

## Passo 2: Criar App

1. No painel, clique em **"Criar App"**
2. Selecione **"Negócios"** como tipo
3. Dê um nome: `Farmacia Magistral Bot`
4. Clique em **Criar App**

---

## Passo 3: Adicionar WhatsApp

1. No seu app, vá em **"Adicionar Produtos"**
2. Encontre **"WhatsApp"** e clique em **"Configurar"**
3. Siga o fluxo de configuração

---

## Passo 4: Obter Credenciais

### Token de Acesso (temporário):
1. Vá em **WhatsApp > Configuração da API**
2. Copie o **Token de Acesso Temporário**
3. ⚠️ Este token expira em 24h (depois faremos permanente)

### Phone Number ID:
1. Na mesma página, veja **"De"**
2. Copie o **ID do Número de Telefone**

---

## Passo 5: Deploy no Render (GRÁTIS)

1. Acesse: **https://render.com**
2. Faça login com GitHub
3. Clique em **New > Web Service**
4. Conecte seu repositório
5. Configure:
   - **Name:** `farmacia-whatsapp-bot`
   - **Environment:** `Python`
   - **Build Command:** `pip install -r requirements-whatsapp.txt`
   - **Start Command:** `gunicorn src.whatsapp_bot:app`
6. Adicione **Environment Variables:**
   - `GOOGLE_API_KEY` = sua chave Gemini
   - `WHATSAPP_ACCESS_TOKEN` = token do Meta
   - `WHATSAPP_PHONE_NUMBER_ID` = ID do número
   - `WHATSAPP_VERIFY_TOKEN` = `farmacia_token_123`
7. Clique **Create Web Service**
8. Copie a URL gerada (ex: `https://farmacia-whatsapp-bot.onrender.com`)

---

## Passo 6: Configurar Webhook no Meta

1. Volte ao Meta Developers
2. Vá em **WhatsApp > Configuração**
3. Em **Webhook**, clique em **Editar**
4. **URL de Callback:** `https://SUA-URL.onrender.com/webhook`
5. **Token de Verificação:** `farmacia_token_123`
6. Clique em **Verificar e Salvar**
7. **Inscreva-se** no campo `messages`

---

## Passo 7: Testar!

1. No Meta Developers, vá em **WhatsApp > Enviar e Receber**
2. Adicione seu número de telefone para teste
3. Envie uma mensagem para o número de teste do WhatsApp
4. Você receberá a resposta do bot!

---

## 🎉 Pronto!

Agora você tem um bot WhatsApp funcional que:
- Recebe mensagens dos clientes
- Analisa sintomas com IA
- Responde com fórmulas manipuladas + preço

## 🔧 Problemas Comuns

| Problema | Solução |
|----------|---------|
| Token expirado | Gere um token permanente nas configurações |
| Webhook não verifica | Verifique se o token é `farmacia_token_123` |
| Bot não responde | Verifique os logs no Render |
