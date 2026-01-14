# 📱 GUIA DETALHADO: WhatsApp Business API + Render (GRÁTIS)

## PARTE 1: META DEVELOPERS (20 minutos)

### Passo 1.1: Acessar Meta Developers

1. Abra o navegador
2. Acesse: **https://developers.facebook.com**
3. Clique no botão **"Começar"** ou **"Get Started"** (canto superior direito)
4. Faça login com sua conta do Facebook
   - Se não tiver, crie uma conta

### Passo 1.2: Verificar Conta de Desenvolvedor

1. Após login, você verá uma tela de boas-vindas
2. Aceite os termos de uso
3. Verifique seu email (Meta envia um código)
4. Pronto! Você é um desenvolvedor Meta

### Passo 1.3: Criar um App

1. No painel principal, clique em **"Meus Apps"** (menu superior)
2. Clique no botão verde **"Criar App"**
3. Na tela de seleção:
   - **Tipo de app:** Selecione **"Negócios"** (Business)
   - Clique **"Avançar"**
4. Preencha os detalhes:
   - **Nome do app:** `Farmacia Magistral Bot`
   - **Email de contato:** seu email
   - **Conta comercial:** Selecione ou crie uma
5. Clique **"Criar App"**
6. ⚠️ Pode pedir para confirmar senha

### Passo 1.4: Adicionar WhatsApp ao App

1. Na página do seu app, role até **"Adicionar produtos ao seu app"**
2. Encontre o card **"WhatsApp"**
3. Clique no botão **"Configurar"**
4. Pronto! WhatsApp foi adicionado

### Passo 1.5: Obter Credenciais

1. No menu lateral esquerdo, clique em **WhatsApp > Configuração da API**
2. Você verá a seção **"Acesso à API"**

#### Token de Acesso Temporário:
- Procure **"Token de acesso temporário"**
- Clique em **"Gerar token"** ou copie o existente
- **⚠️ IMPORTANTE:** Este token expira em 24 horas
- **Guarde esse token!** Você vai precisar

#### Phone Number ID:
- Na mesma página, seção **"De"**
- Você verá um número de teste (ex: +1 555 XXX XXXX)
- Abaixo dele, há o **"ID do número de telefone"**
- **Copie esse ID!** (parece: 123456789012345)

### Passo 1.6: Adicionar Número de Teste

1. Na seção **"Para"**, clique em **"Gerenciar lista de números de telefone"**
2. Clique em **"Adicionar número de telefone"**
3. Digite SEU número de WhatsApp (com código do país: +55...)
4. Você receberá um código no WhatsApp
5. Digite o código para verificar
6. Pronto! Seu número está autorizado para testes

---

## PARTE 2: DEPLOY NO KOYEB (GRÁTIS, SEM CARTÃO) (15 minutos)

### Passo 2.1: Criar Conta no Koyeb

1. Acesse: **https://app.koyeb.com**
2. Clique em **"Sign up"**
3. Escolha **"Continue with GitHub"** (mais fácil)
4. Autorize o Koyeb no GitHub
5. ✅ Pronto! Conta criada (não pede cartão!)

### Passo 2.2: Criar Novo App

1. No dashboard, clique em **"Create App"**
2. Selecione **"GitHub"** como fonte
3. Clique em **"Connect GitHub"** se ainda não conectou
4. Encontre seu repositório **"ia-farmacia"**
5. Clique em **"Import"**

### Passo 2.3: Configurar o Build

Na página de configuração:

| Campo | Valor |
|-------|-------|
| **Builder** | `Dockerfile` ou `Buildpack` |
| **Branch** | `main` |
| **Build command** | `pip install -r requirements-whatsapp.txt` |
| **Run command** | `gunicorn src.whatsapp_bot:app --bind 0.0.0.0:8000` |
| **Port** | `8000` |

### Passo 2.4: Adicionar Variáveis de Ambiente

1. Role até **"Environment variables"**
2. Clique em **"Add variable"** para cada uma:

| Variable | Value |
|----------|-------|
| `GOOGLE_API_KEY` | Sua chave do Gemini |
| `WHATSAPP_ACCESS_TOKEN` | Token copiado do Meta |
| `WHATSAPP_PHONE_NUMBER_ID` | ID do número copiado |
| `WHATSAPP_VERIFY_TOKEN` | `farmacia_token_123` |
| `VECTORSTORE_PATH` | `data/vectorstore` |
| `PORT` | `8000` |

### Passo 2.5: Escolher Plano e Deploy

1. Em **"Instance"**, selecione **"Free"** (nano)
2. Dê um nome ao app: `farmacia-whatsapp`
3. Clique em **"Deploy"**
4. Aguarde o deploy (5-10 minutos)
5. Quando ficar verde, está pronto!
6. **COPIE A URL** (ex: `https://farmacia-whatsapp-XXXXX.koyeb.app`)

---

## PARTE 3: CONFIGURAR WEBHOOK NO META (5 minutos)

### Passo 3.1: Acessar Configuração do Webhook

1. Volte para **developers.facebook.com**
2. Acesse seu app
3. No menu lateral, vá em **WhatsApp > Configuração**
4. Role até a seção **"Webhook"**

### Passo 3.2: Configurar URL do Webhook

1. Clique em **"Editar"** no card do Webhook
2. Preencha:
   - **URL de callback:** `https://farmacia-whatsapp-bot.onrender.com/webhook`
     (substitua pela SUA URL do Render)
   - **Token de verificação:** `farmacia_token_123`
3. Clique em **"Verificar e salvar"**
4. Se tudo estiver certo, aparecerá ✅

### Passo 3.3: Inscrever-se nos Eventos

1. Após verificar, você verá a lista de **"Campos de webhook"**
2. Encontre o campo **"messages"**
3. Clique em **"Inscrever-se"** ou no toggle para ativar
4. Pronto!

---

## PARTE 4: TESTAR! 🎉

### Passo 4.1: Enviar Mensagem de Teste

1. No Meta Developers, vá em **WhatsApp > Configuração da API**
2. Seção **"Enviar mensagens"**
3. Selecione seu número em **"Para"**
4. Clique em **"Enviar mensagem"**
5. Você receberá uma mensagem de teste no WhatsApp

### Passo 4.2: Testar o Bot

1. Abra seu WhatsApp
2. Responda à mensagem de teste
3. Escreva: **"Olá"**
4. O bot deve responder com a mensagem de boas-vindas!
5. Teste com sintomas: **"Estou com dor de cabeça e febre"**

---

## ✅ PRONTO!

Seu bot está funcionando! Agora:
- Clientes enviam mensagem para o número do WhatsApp
- O bot responde com fórmulas manipuladas + preço
- 100% automático!

---

## 🔧 PROBLEMAS COMUNS

| Problema | Solução |
|----------|---------|
| Webhook não verifica | Verifique se a URL termina com `/webhook` |
| Bot não responde | Veja os logs no Render (tab "Logs") |
| Token expirado | Gere um novo token no Meta |
| Erro de CPU | O Render gratuito pode demorar para acordar |

---

## 🔐 SEGURANÇA (Importante!)

1. **Nunca compartilhe** seu Access Token
2. Para produção, gere um **token permanente**:
   - Meta Business > Configurações > Usuários do sistema
   - Crie um usuário e gere token permanente
