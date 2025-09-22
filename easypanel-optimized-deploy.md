# Guia de Deploy no EasyPanel — Versão Otimizada

Este guia descreve como implantar a versão otimizada do Avantar Transcribe no EasyPanel usando o `Dockerfile.optimized`.

## Pré-requisitos
- Repositório com estes arquivos no root:
  - `Dockerfile.optimized`
  - `docker-compose-optimized.yml` (opcional)
  - `requirements_optimized.txt`
  - `src/transcribe_optimized.py`
- EasyPanel instalado no seu servidor com Docker.
- Porta 8000 liberada no firewall (ou configure um domínio via EasyPanel).

## Passo a passo no EasyPanel

### 1) Criar Aplicação
- Acesse o EasyPanel → Apps → New App
- Tipo: Dockerfile (Build from source)
- Repositório: conecte seu Git (ou use Upload se preferir)
- Branch: `main`
- Build Context: `/` (raiz do repo)
- Dockerfile Path: `Dockerfile.optimized`

### 2) Variáveis de Ambiente
Adicione as seguintes variáveis:
- `PYTHONUNBUFFERED=1`
- `OMP_NUM_THREADS=2`
- `MKL_NUM_THREADS=2`
- `TOKENIZERS_PARALLELISM=false`

Opcional (para limitar tamanho de upload, se desejar alterar o padrão do código):
- `MAX_FILE_SIZE_MB=25`

### 3) Recursos (Limits e Requests)
Defina limites conservadores para VPS 2 vCPU / 8GB RAM:
- CPU limit: 2.0
- CPU request: 1.0
- Memory limit: 6G
- Memory request: 2G

No EasyPanel, ajuste em Resources/Scaling (ou equivalente no provider):
- Instâncias (replicas): 1

### 4) Porta e Health Check
- Expose/Service Port: `8000`
- Health Check:
  - Path: `/health`
  - Interval: 30s
  - Timeout: 10s
  - Retries: 3
  - Start Period: 40s

### 5) Volume Persistente (Cache)
Crie e anexe um volume para o cache de transcrições:
- Volume Name: `avantar-cache`
- Mount Path: `/app/cache`

Isso reduz reprocessamento e uso de CPU em chamadas repetidas.

### 6) Deploy
- Clique em Deploy/Build
- Aguarde o build (instala pacotes, baixa modelos na primeira execução)
- Ao finalizar, verifique os Logs para confirmar: "Avantar Transcribe API - Versão Otimizada" e status healthy no `/health`

## Testes Pós-Deploy

### Testar Health
```bash
curl -f http://SEU_DOMINIO_OU_IP:8000/health
```

### Testar Transcrição Simples (WhatsApp/áudio curto)
```bash
curl -X POST \
  -F "file=@caminho/para/audio.ogg" \
  http://SEU_DOMINIO_OU_IP:8000/transcribe-simple
```

### Testar Transcrição Completa
```bash
curl -X POST \
  -F "file=@caminho/para/audio.mp3" \
  -F "language=pt" \
  http://SEU_DOMINIO_OU_IP:8000/transcribe
```

## Boas Práticas de Uso (VPS 2 vCPU / 8GB)
- Envie arquivos até 25MB (padrão do app). Para maiores, converta para mono 16kHz e compacte.
- Evite requisições simultâneas: a API já limita, mas organize seu cliente para fila.
- Prefira o endpoint `/transcribe-simple` quando só precisar do texto.
- Reaproveite resultados: o cache está habilitado por padrão.

## Observabilidade e Manutenção
- Logs: verifique no EasyPanel → Logs do app
- Saúde: `GET /health` (retorna uso de CPU/RAM e tamanho do cache)
- Cache:
  - Limpar: `GET /cache/clear`
  - Estatísticas: `GET /cache/stats`

## Dicas de Performance
- O app seleciona o modelo baseado em recursos/arquivo; em VPS modesta ele usará `tiny`.
- Conversão via FFmpeg usa `-threads 1` para evitar picos de CPU.
- Para mais throughput, aumente vCPU e RAM e eleve `workers`/recursos.

## Solução de Problemas
- Build muito lento ou falha de memória: aumente Memory limit temporariamente para 8G.
- Health reporta "overloaded": reduza concorrência do cliente ou aguarde.
- 413 (Payload Too Large): compacte o áudio/vídeo ou ajuste `MAX_FILE_SIZE` no código.
- Sem saída de áudio: confirme que o container tem `ffmpeg` (já incluso no Dockerfile).

## Atualizações
- Edite o código e faça git push → no EasyPanel, clique em Redeploy.
- Mudanças em dependências exigem rebuild completo.

## Segurança
- Se expor publicamente, configure domínio/HTTPS pelo EasyPanel.
- Aplique rate limiting no proxy (Nginx/Traefik) se tiver alto tráfego.

---
Se precisar, posso conectar o app a um domínio e configurar HTTPS/Proxy no EasyPanel com as melhores práticas para produção.
