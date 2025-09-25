# 📚 Documentação da API Avantar Transcribe - Versão Otimizada

## 🎯 Visão Geral

A API Avantar Transcribe Otimizada é uma versão especializada para VPS com recursos limitados (2 vCPU, 8GB RAM). Ela oferece transcrição de áudio/vídeo, OCR de imagens e processamento de documentos com otimizações de memória e CPU.

## 🚀 Endpoints Principais

### 1. **Health Check**
Verifica o status da API e recursos do sistema.

```bash
GET /health
```

**Resposta:**
```json
{
  "status": "healthy",
  "resources": {
    "cpu_percent": 2.0,
    "memory_percent": 29.7,
    "memory_available_mb": 5585,
    "memory_used_mb": 1961
  },
  "cache_size": 0,
  "max_file_size_mb": 25,
  "ocr_available": true,
  "max_concurrent_requests": 2
}
```

### 2. **Transcrição Simples** ⭐ (Recomendado)
Endpoint otimizado para transcrições rápidas (WhatsApp, áudios curtos).

```bash
POST /transcribe-simple
```

**Parâmetros:**
- `file`: Arquivo de áudio/vídeo (máximo 25MB)

**Exemplo com cURL:**
```bash
curl -X POST \
  -F "file=@audio.ogg" \
  https://seu-dominio.com/transcribe-simple
```

**Resposta:**
```json
{
  "text": "Olá, este é um teste de transcrição de áudio."
}
```

### 3. **Transcrição Completa**
Endpoint com mais opções e informações detalhadas.

```bash
POST /transcribe
```

**Parâmetros:**
- `file`: Arquivo de áudio/vídeo (máximo 25MB)
- `language`: Código do idioma (padrão: "pt")
- `use_cache`: Usar cache (padrão: true)

**Exemplo com cURL:**
```bash
curl -X POST \
  -F "file=@video.mp4" \
  -F "language=pt" \
  -F "use_cache=true" \
  https://seu-dominio.com/transcribe
```

**Resposta:**
```json
{
  "text": "Transcrição completa do áudio...",
  "language": "pt",
  "segments": [
    {
      "id": 0,
      "start": 0.0,
      "end": 5.2,
      "text": "Primeiro segmento"
    }
  ],
  "filename": "video.mp4",
  "model_used": "tiny",
  "duration": 5.2,
  "cached": false,
  "resources_used": {
    "cpu_percent": 15.0,
    "memory_percent": 35.0
  }
}
```

### 4. **OCR de Imagens**
Extrai texto de imagens usando Tesseract.

```bash
POST /ocr/image
```

**Parâmetros:**
- `file`: Arquivo de imagem (JPG, PNG, etc.)

**Exemplo com cURL:**
```bash
curl -X POST \
  -F "file=@imagem.jpg" \
  https://seu-dominio.com/ocr/image
```

**Resposta:**
```json
{
  "text": "Texto extraído da imagem",
  "method": "Tesseract (optimized)",
  "confidence": 0.8,
  "filename": "imagem.jpg",
  "file_size": 1024000,
  "cached": false
}
```

## 🛠️ Gerenciamento de Cache

### Limpar Cache
```bash
GET /cache/clear
```

**Resposta:**
```json
{
  "message": "Cache limpo. 15 itens removidos."
}
```

### Estatísticas do Cache
```bash
GET /cache/stats
```

**Resposta:**
```json
{
  "cache_size": 5,
  "max_cache_size": 50,
  "resources": {
    "cpu_percent": 10.0,
    "memory_percent": 30.0
  },
  "memory_usage_mb": 2.5
}
```

## 📋 Formatos Suportados

### Áudio
- MP3, WAV, M4A, OGG, WEBM, FLAC

### Vídeo
- MP4, AVI, MOV, MKV

### Imagens
- JPG, JPEG, PNG, BMP, TIFF, WEBP, GIF

## ⚡ Otimizações Automáticas

### Seleção de Modelo
A API escolhe automaticamente o modelo baseado em:

1. **Tiny** (padrão para VPS):
   - Arquivos < 5MB
   - Memória disponível < 2GB
   - CPU > 80%

2. **Base** (quando recursos permitem):
   - Arquivos > 5MB
   - Memória disponível > 2GB
   - CPU < 80%

### Limitações de Recursos
- **CPU**: Máximo 90% (retorna 503 se exceder)
- **RAM**: Máximo 90% (retorna 503 se exceder)
- **Concorrência**: Máximo 2 requisições simultâneas
- **Cache**: Máximo 50 itens (limpeza automática LRU)

## 🔧 Exemplos Práticos

### 1. Transcrição de Áudio do WhatsApp
```bash
# Arquivo pequeno (otimizado)
curl -X POST \
  -F "file=@whatsapp_audio.ogg" \
  https://seu-dominio.com/transcribe-simple
```

### 2. Transcrição de Vídeo
```bash
# Vídeo será convertido para áudio automaticamente
curl -X POST \
  -F "file=@video.mp4" \
  -F "language=pt" \
  https://seu-dominio.com/transcribe
```

### 3. OCR de Documento Escaneado
```bash
# Extrair texto de imagem
curl -X POST \
  -F "file=@documento.jpg" \
  https://seu-dominio.com/ocr/image
```

### 4. Monitoramento de Saúde
```bash
# Verificar status da API
curl https://seu-dominio.com/health
```

## 🚨 Códigos de Erro

| Código | Descrição | Solução |
|--------|------------|---------|
| 400 | Tipo de arquivo não suportado | Use formatos suportados |
| 413 | Arquivo muito grande | Reduza para < 25MB |
| 408 | Timeout na conversão | Arquivo muito longo |
| 500 | Erro interno | Verifique logs |
| 503 | Servidor sobrecarregado | Aguarde e tente novamente |

## 📊 Monitoramento

### Recursos do Sistema
```bash
curl https://seu-dominio.com/health | jq '.resources'
```

### Estatísticas de Cache
```bash
curl https://seu-dominio.com/cache/stats | jq '.cache_size'
```

## 🎯 Casos de Uso Recomendados

### 1. **WhatsApp Business**
- Use `/transcribe-simple` para áudios curtos
- Cache habilitado para respostas rápidas
- Modelo "tiny" automático

### 2. **Processamento em Lote**
- Faça requisições sequenciais (não simultâneas)
- Monitore `/health` antes de cada lote
- Use cache para arquivos repetidos

### 3. **Integração com N8N/Zapier**
- Endpoint `/transcribe-simple` para automação
- Timeout de 5 minutos para arquivos grandes
- Retry em caso de erro 503

## 🔒 Segurança

### Rate Limiting
- Máximo 2 requisições simultâneas
- Bloqueio automático se CPU/RAM > 90%

### Validação de Arquivos
- Verificação de tipo MIME
- Limite de tamanho (25MB)
- Limpeza automática de arquivos temporários

## 📈 Performance

### Tempos Típicos (VPS 2 vCPU/8GB)
- **Áudio 1MB**: 10-30 segundos
- **Vídeo 10MB**: 30-60 segundos
- **Imagem OCR**: 5-15 segundos

### Otimizações
- Cache LRU automático
- Processamento assíncrono
- Limpeza de memória automática
- Threads limitadas para FFmpeg

## 🛠️ Troubleshooting

### Problema: "Service not reachable"
**Solução**: Verifique configuração de porta no EasyPanel

### Problema: "Servidor sobrecarregado"
**Solução**: Aguarde 30 segundos e tente novamente

### Problema: "Arquivo muito grande"
**Solução**: Comprima o arquivo ou use conversão de áudio

### Problema: Timeout
**Solução**: Reduza duração do áudio ou use arquivos menores

## 📞 Suporte

Para problemas técnicos:
1. Verifique `/health` primeiro
2. Consulte logs do EasyPanel
3. Teste com arquivos menores
4. Monitore recursos do sistema

---

**Versão**: 2.0.0-optimized  
**Compatibilidade**: VPS 2 vCPU, 8GB RAM  
**Última atualização**: Setembro 2025
