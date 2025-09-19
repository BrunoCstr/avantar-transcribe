# 🚀 Deploy no Easypanel (Hostinger VPS)

## Pré-requisitos no Windows

### 1. Instalar Git
```bash
# Baixar e instalar Git for Windows
https://git-scm.com/download/win
```

### 2. Preparar o projeto
```bash
# No terminal do Windows (PowerShell ou CMD)
cd D:\AVA-IA

# Adicionar arquivos ao git (se ainda não estiver)
git init
git add .
git commit -m "Initial commit - Whisper Transcription API"

# Criar repositório no GitHub/GitLab
# Depois fazer push:
git remote add origin https://github.com/seu-usuario/whisper-api.git
git push -u origin main
```

## Deploy no Easypanel

### 1. Acessar o Easypanel
1. Entre na sua VPS Hostinger
2. Acesse o Easypanel (geralmente em `https://seu-ip:3000`)
3. Faça login com suas credenciais

### 2. Criar Nova Aplicação

#### Passo 1: Adicionar Serviço
1. Clique em **"Add Service"**
2. Escolha **"App"**
3. Selecione **"From Source Code"**

#### Passo 2: Configurar Source
```yaml
# Repository URL
https://github.com/seu-usuario/whisper-api.git

# Branch
main

# Build Path
./

# Auto Deploy
✅ Habilitado
```

#### Passo 3: Configurações da Aplicação
```yaml
# App Name
whisper-transcription

# Domain
whisper.seu-dominio.com
# OU usar o domínio gratuito do Easypanel

# Port
8000

# Build Command (deixar vazio - usaremos Dockerfile)

# Start Command (deixar vazio - usaremos Dockerfile)
```

### 3. Configurar Dockerfile Otimizado para Easypanel

Vou atualizar o Dockerfile para funcionar perfeitamente no Easypanel:

```dockerfile
# Dockerfile otimizado para Easypanel
FROM python:3.11-slim

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Criar diretório da aplicação
WORKDIR /app

# Copiar arquivos de dependências primeiro (para cache do Docker)
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Criar diretório de cache
RUN mkdir -p cache logs

# Dar permissões necessárias
RUN chmod -R 755 /app

# Expor porta
EXPOSE 8000

# Variáveis de ambiente para produção
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Comando de inicialização
CMD ["python", "avantar-transcribe/transcribe.py"]
```

### 4. Configurações de Environment Variables

No Easypanel, adicione essas variáveis de ambiente:

```env
# Performance
MAX_FILE_SIZE_MB=100
CACHE_SIZE_LIMIT=1000
LOG_LEVEL=INFO

# Modelos Whisper
LOAD_MODELS=tiny,base,small

# Configurações do FastAPI
HOST=0.0.0.0
PORT=8000
```

### 5. Configurar Volume para Cache

1. No Easypanel, vá em **"Volumes"**
2. Adicione um volume:
```yaml
# Volume Name
whisper-cache

# Mount Path
/app/cache

# Size
5GB
```

### 6. Configurações de Recursos

No Easypanel, configure os recursos:

```yaml
# Memory Limit
4GB

# CPU Limit
2 cores

# Storage
10GB (para modelos + cache)
```

## Configuração Completa do Projeto

### 1. Preparar arquivos no Windows

No seu diretório `D:\AVA-IA`, certifique-se de ter estes arquivos:

```
D:\AVA-IA\
├── avantar-transcribe/
│   └── transcribe.py
├── requirements.txt
├── Dockerfile
├── config.env
├── README.md
└── .gitignore
```

### 2. Criar arquivo .gitignore

```gitignore
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
venv/
env/
ENV/

# Cache e logs
cache/
logs/
*.log

# OS
.DS_Store
Thumbs.db

# IDEs
.vscode/
.idea/
*.swp
*.swo

# Temporários
temp/
tmp/
*.tmp
```

### 3. Fazer Push para o GitHub

No PowerShell do Windows:

```powershell
# Navegar para o diretório
cd D:\AVA-IA

# Inicializar git (se não feito)
git init

# Adicionar arquivos
git add .
git commit -m "Deploy: Whisper API otimizada para Easypanel"

# Conectar ao repositório remoto
git remote add origin https://github.com/SEU-USUARIO/whisper-transcription-api.git
git branch -M main
git push -u origin main
```

## Deploy Passo a Passo no Easypanel

### 1. Acessar o Easypanel

1. **Acesse sua VPS Hostinger** pelo painel de controle
2. **Entre no Easypanel**: `https://SEU-IP-VPS:3000`
   - O IP da sua VPS você encontra no painel da Hostinger
   - Exemplo: se seu IP é `123.45.67.89`, acesse `https://123.45.67.89:3000`
3. **Faça login** com as credenciais que você criou quando instalou o Easypanel

### 2. Criar o Projeto

#### Passo 1: New Project
1. Clique em **"Create Project"**
2. Nome do projeto: `whisper-transcription`
3. Clique em **"Create"**

#### Passo 2: Add Service
1. Dentro do projeto, clique **"Add Service"**
2. Escolha **"App"**
3. Selecione **"From Source Code"**

#### Passo 3: Configurar Source Code
Na tela **"Create App"**, você verá um formulário. Preencha:

**Source:**
- **Type**: `Git Repository` (já selecionado)
- **Repository URL**: `https://github.com/SEU-USUARIO/whisper-transcription-api.git`
- **Branch**: `main`
- **Auto Deploy**: ✅ (marque a caixa para deploy automático)

#### Passo 4: App Configuration
**App Settings:**
- **App Name**: `whisper-api`
- **Build Method**: Selecione `Dockerfile` no dropdown
- **Port**: `8000`
- **Domain**: Deixe o padrão (será algo como `whisper-api-abc123.easypanel.host`)

**Depois clique em "Create App" no final da página.**

---

## ⚠️ PROBLEMAS COMUNS NO PASSO 3

### Problema 1: "Não encontro as abas Environment/Resources/Mounts"

**Solução:**
1. Certifique-se de que a app foi criada com sucesso
2. Você deve estar **DENTRO** da página da app (não na lista de apps)
3. As abas ficam no **topo da página**, logo abaixo do nome da app
4. Se não aparecem, recarregue a página (F5)

### Problema 2: "Não consigo adicionar Environment Variables"

**Solução:**
1. Na aba Environment, procure por **"Environment Variables"** (pode estar mais abaixo)
2. Se não tem botão "+ Add Variable", procure por "Edit" ou "Configure"
3. Algumas versões do Easypanel mostram um formulário direto em vez de botão

### Problema 3: "Não encontro a aba Mounts/Volumes"

**Solução:**
1. A aba pode se chamar **"Mounts"**, **"Volumes"** ou **"Storage"**
2. Se não existe, procure na aba **"Resources"** por uma seção de volumes
3. Em algumas versões, volumes são configurados junto com resources

### Problema 4: "Build falha ou app não inicia"

**Solução:**
1. Verifique se o repositório GitHub está público ou se você deu acesso
2. Confirme se todos os arquivos estão no repositório (Dockerfile, requirements.txt)
3. Veja os logs na aba **"Logs"** para identificar o erro específico

---

### 3. Configurar Environment Variables

**IMPORTANTE**: Após criar a app, você precisa configurar as variáveis de ambiente.

**Localização das abas no Easypanel:**
```
[Overview] [Environment] [Resources] [Mounts] [Domains] [Logs] [Settings]
    ↑           ↑            ↑         ↑
  Atual    Vamos aqui    Depois    Depois
```

**Passo a passo:**
1. **Certifique-se** de que está na página da sua app (mostra "whisper-api" no topo)
2. **Clique na aba "Environment"** (segunda aba da esquerda)
3. **Role a página para baixo** até encontrar **"Environment Variables"**
4. **Clique em "+ Add Variable"** ou botão similar

**Se não encontrar as abas:**
- Verifique se está na página certa (deve mostrar o nome da app no topo)
- Recarregue a página (Ctrl+F5)
- As abas podem estar em um menu "hamburger" (≡) em telas pequenas

**Adicione essas variáveis uma por uma:**

| Key | Value |
|-----|-------|
| `MAX_FILE_SIZE_MB` | `100` |
| `CACHE_SIZE_LIMIT` | `1000` |
| `LOG_LEVEL` | `INFO` |
| `LOAD_MODELS` | `tiny,base,small` |
| `HOST` | `0.0.0.0` |
| `PORT` | `8000` |
| `CACHE_ENABLED` | `true` |
| `CACHE_TTL` | `3600` |
| `MAX_WORKERS` | `2` |
| `TIMEOUT_SECONDS` | `300` |

**Para cada variável:**
1. Clique **"+ Add Variable"**
2. Digite o **Key** (nome da variável)
3. Digite o **Value** (valor)
4. Clique **"Add"**

### 4. Configurar Resources

**Agora vamos configurar CPU e memória:**

1. **Clique na aba "Resources"** (terceira aba)
2. **Procure por campos** para configurar recursos:

**Layout típico da página Resources:**
```
Memory Limit: [____] MB
CPU Limit: [____] millicores  
Storage Size: [____] GB
```

**Memory:**
- Procure por **"Memory Limit"**
- Digite: `4096` (isso significa 4096MB = 4GB)

**CPU:**
- Procure por **"CPU Limit"** 
- Digite: `2000` (isso significa 2000m = 2 cores)

**Storage:**
- Procure por **"Storage Size"**
- Digite: `10` (isso significa 10GB)

**Depois clique em "Save" ou "Update" para salvar as configurações.**

### 5. Configurar Volumes (Importante!)

**O cache é essencial para performance!**

**Localizando a configuração de volumes:**
1. **Clique na aba "Mounts"** (quarta aba)
   - Se não existir, procure na aba "Resources" por uma seção de volumes
   - Algumas versões chamam de "Storage" ou "Volumes"

2. **Procure por:**
   - Seção **"Volumes"** 
   - Seção **"Persistent Storage"**
   - Botão **"+ Add Volume"** ou **"Create Volume"**

**Se não encontrar volumes:**
- Algumas versões do Easypanel não têm volumes separados
- Neste caso, pule esta etapa (o cache ficará em memória)

**Configure o volume:**
- **Volume Name**: `whisper-cache`
- **Mount Path**: `/app/cache`
- **Size**: `5` (GB)

4. Clique **"Add"** ou **"Create"** para criar o volume
5. **Importante**: Certifique-se de que o volume está "attached" à sua app

### 6. Deploy

**Agora vamos fazer o deploy!**

1. **Volte para a aba "Overview"** da sua app (primeira aba)
2. Procure por um botão **"Deploy"** ou **"Redeploy"** (geralmente no canto superior direito)
3. Clique em **"Deploy"**
4. **Aguarde o build** - pode demorar 5-10 minutos na primeira vez

**Durante o deploy:**
- Clique na aba **"Logs"** para acompanhar o progresso
- Você verá mensagens como:
  - `Building Docker image...`
  - `Installing dependencies...`
  - `Starting application...`

**Sinais de sucesso:**
- Status muda para **"Running"** (bolinha verde)
- Nos logs aparece: `"Modelos carregados com sucesso!"`

---

## ✅ CHECKLIST - Verificar Configurações

Antes de fazer o deploy, confirme que configurou tudo:

### ✅ App Criada
- [ ] App "whisper-api" foi criada com sucesso
- [ ] Repository GitHub está conectado
- [ ] Build Method está como "Dockerfile"
- [ ] Port está configurada como 8000

### ✅ Environment Variables (10 variáveis)
- [ ] `MAX_FILE_SIZE_MB` = `100`
- [ ] `CACHE_SIZE_LIMIT` = `1000`
- [ ] `LOG_LEVEL` = `INFO`
- [ ] `LOAD_MODELS` = `tiny,base,small`
- [ ] `HOST` = `0.0.0.0`
- [ ] `PORT` = `8000`
- [ ] `CACHE_ENABLED` = `true`
- [ ] `CACHE_TTL` = `3600`
- [ ] `MAX_WORKERS` = `2`
- [ ] `TIMEOUT_SECONDS` = `300`

### ✅ Resources
- [ ] Memory: `4096` MB
- [ ] CPU: `2000` millicores
- [ ] Storage: `10` GB

### ✅ Volume (Opcional)
- [ ] Volume criado: `whisper-cache`
- [ ] Mount path: `/app/cache`
- [ ] Size: `5` GB
- [ ] OU pulou esta etapa se não encontrou

**Se todos os itens estão marcados, pode fazer o deploy! 🚀**

---

## Verificar se Funcionou

### 1. Testar Health Check

```bash
# Substituir pela sua URL do Easypanel
curl https://whisper-api-SEU-PROJETO.easypanel.host/health
```

Resposta esperada:
```json
{
  "status": "healthy",
  "models_loaded": ["tiny", "base", "small"],
  "cache_size": 0,
  "max_file_size_mb": 100
}
```

### 2. Testar Transcrição

No Windows, usando PowerShell:

```powershell
# Testar com um áudio pequeno
$uri = "https://whisper-api-SEU-PROJETO.easypanel.host/transcribe-whatsapp"
$filePath = "D:\AVA-IA\audios\WhatsApp-Ptt-2025-09-19-at-12.25.16.ogg"

# Criar form data
$form = @{
    file = Get-Item -Path $filePath
}

# Fazer request
Invoke-RestMethod -Uri $uri -Method Post -Form $form
```

### 3. Verificar Logs

No Easypanel:
1. Vá na aba **"Logs"**
2. Verifique se não há erros
3. Deve mostrar: "Modelos carregados com sucesso!"

## Configurar Domínio Personalizado (Opcional)

### 1. No Easypanel

1. Vá em **"Domains"**
2. Clique **"Add Domain"**
3. Digite: `whisper.seu-dominio.com`
4. Ative SSL automático

### 2. No DNS (Hostinger)

1. Acesse o painel da Hostinger
2. Vá em **DNS Zone**
3. Adicione um registro A:
```
Type: A
Name: whisper
Points to: SEU-IP-VPS
TTL: 3600
```

## Monitoramento e Manutenção

### 1. Verificar Status

No Easypanel, você pode:
- Ver uso de CPU/Memória
- Verificar logs em tempo real
- Reiniciar o serviço se necessário

### 2. Atualizar o Código

No Windows:
```powershell
cd D:\AVA-IA

# Fazer suas alterações
# Depois:
git add .
git commit -m "Update: nova funcionalidade"
git push

# O Easypanel vai fazer auto-deploy!
```

### 3. Backup

O Easypanel faz backup automático, mas você pode:
1. Fazer backup manual na aba **"Backups"**
2. Baixar backups quando necessário

## Integração com n8n

Agora que sua API está rodando, você pode usar nos workflows do n8n:

```javascript
// URL da sua API no Easypanel
const apiUrl = "https://whisper-api-SEU-PROJETO.easypanel.host";

// Usar nos nós HTTP Request do n8n
{
  "url": "https://whisper-api-SEU-PROJETO.easypanel.host/transcribe-whatsapp",
  "method": "POST",
  "sendBody": true,
  "bodyContentType": "multipart-form-data"
}
```

## Troubleshooting

### 1. Build falhou
- Verifique se todos os arquivos estão no GitHub
- Confirme se o Dockerfile está correto
- Veja os logs de build no Easypanel

### 2. Aplicação não inicia
- Verifique as environment variables
- Confirme se a porta 8000 está configurada
- Veja os logs da aplicação

### 3. Erro de memória
- Aumente a memória para 4GB ou mais
- Considere usar apenas modelos "tiny" e "base"

### 4. Transcrição lenta
- Verifique se o volume de cache está funcionando
- Monitore uso de CPU
- Considere fazer upgrade da VPS

## Custos Estimados

Na Hostinger VPS:
- **VPS 1**: 2GB RAM, 1 CPU → Funciona mas lento
- **VPS 2**: 4GB RAM, 2 CPU → **Recomendado**
- **VPS 3**: 8GB RAM, 4 CPU → Ideal para alto volume

O Easypanel é gratuito e já está incluído! 🎉
