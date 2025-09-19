# 🎙️ Universal Transcription API

API universal para transcrição de áudio, OCR de imagens e extração de texto de documentos.

## ✨ Características

- 🎵 **Transcrição de áudio**: WhatsApp otimizado + vídeos grandes (Whisper)
- 🖼️ **OCR de imagens**: EasyOCR + Tesseract para extrair texto de imagens
- 📄 **Extração de PDFs**: Texto direto + OCR para PDFs escaneados
- 📝 **Documentos Office**: Word, Excel, PowerPoint (.docx, .xlsx, .pptx)
- 🤖 **Detecção automática**: Identifica o tipo de arquivo automaticamente
- ⚡ **Cache inteligente**: Evita reprocessamento desnecessário
- 🐳 **Docker ready**: Deploy fácil com Easypanel/Hostinger
- 🔗 **n8n integration**: Workflows prontos para automação

## 🛠️ Tecnologias

- **FastAPI**: Framework web moderno e rápido
- **OpenAI Whisper**: IA de transcrição de áudio/vídeo
- **EasyOCR**: OCR moderno com IA para imagens
- **Tesseract**: OCR tradicional e confiável
- **PyMuPDF + pdfplumber**: Extração de texto de PDFs
- **python-docx/openpyxl/python-pptx**: Documentos Office
- **FFmpeg**: Processamento de áudio/vídeo
- **Docker**: Containerização para deploy fácil

## 🚀 Deploy Rápido (Easypanel + Hostinger)

### 1. Preparar no Windows

```powershell
# Clonar o repositório
git clone https://github.com/SEU-USUARIO/whisper-transcription-api.git
cd whisper-transcription-api

# Fazer push para seu repositório
git remote set-url origin https://github.com/SEU-USUARIO/whisper-transcription-api.git
git push
```

### 2. Deploy no Easypanel

1. Acesse seu Easypanel: `https://SEU-IP-VPS:3000`
2. Create Project → Add Service → From Source Code
3. Configure:
   - **Repository**: `https://github.com/SEU-USUARIO/whisper-transcription-api.git`
   - **Build Method**: Dockerfile
   - **Port**: 8000
   - **Memory**: 4GB
   - **CPU**: 2 cores

4. Environment Variables:
```env
MAX_FILE_SIZE_MB=100
LOAD_MODELS=tiny,base,small
LOG_LEVEL=INFO
```

5. Deploy! 🚀

### 3. Testar

```powershell
# No Windows PowerShell
.\test-windows.ps1 -ApiUrl "https://whisper-api-SEU-PROJETO.easypanel.host"
```

## 📚 Documentação Completa

- **[🚀 Deploy Guide](easypanel-deploy-guide.md)** - Deploy completo no Easypanel
- **[🔗 n8n Integration](n8n-integration-guide.md)** - Workflows e automações

## 🎯 Endpoints Principais

### 🎵 Áudio e Vídeo
```bash
POST /transcribe-whatsapp    # Otimizado para WhatsApp
POST /transcribe-video       # Vídeos grandes
POST /transcribe-simple      # Resposta simples
POST /transcribe            # Resposta completa
```

### 🖼️ Imagens (OCR)
```bash
POST /ocr/image             # OCR de imagens
# Parâmetros: method=easyocr|tesseract
```

### 📄 PDFs
```bash
POST /extract/pdf           # Extração de PDFs
# Parâmetros: method=auto|direct|ocr
```

### 📝 Documentos Office
```bash
POST /extract/document      # Word, Excel, PowerPoint
# Suporta: .docx, .xlsx, .pptx
```

### 🤖 Detecção Automática
```bash
POST /extract/auto          # Detecta tipo automaticamente
# Suporta todos os formatos acima
```

## 💾 Cache e Performance

- ✅ Cache baseado em hash MD5
- ✅ Modelos otimizados por tamanho de arquivo
- ✅ Limpeza automática de arquivos temporários
- ✅ Processamento assíncrono

## 🔧 Desenvolvimento Local

```bash
# Instalar dependências
pip install -r requirements.txt

# Executar
python openai-whisper/transcribe.py

# Testar
curl http://localhost:8000/health
```

## 📊 Tecnologias por Tipo de Arquivo

| Tipo | Tecnologia | Formatos Suportados | Performance |
|------|------------|---------------------|-------------|
| **Áudio** | Whisper (tiny/base/small) | mp3, wav, ogg, m4a, flac | ⚡⚡⚡ |
| **Vídeo** | Whisper + FFmpeg | mp4, avi, mov, mkv | ⚡⚡ |
| **Imagem** | EasyOCR / Tesseract | jpg, png, bmp, tiff, webp | ⚡⚡ |
| **PDF** | pdfplumber + OCR | pdf (texto e escaneado) | ⚡ |
| **Office** | python-docx/openpyxl/pptx | docx, xlsx, pptx | ⚡⚡⚡ |

## 🔗 Integração n8n

### Exemplos para n8n:

**Áudio do WhatsApp:**
```javascript
{
  "url": "https://sua-api.easypanel.host/transcribe-whatsapp",
  "method": "POST",
  "bodyContentType": "multipart-form-data"
}
```

**OCR de Imagem:**
```javascript
{
  "url": "https://sua-api.easypanel.host/ocr/image",
  "method": "POST",
  "bodyContentType": "multipart-form-data"
}
```

**PDF:**
```javascript
{
  "url": "https://sua-api.easypanel.host/extract/pdf",
  "method": "POST",
  "bodyContentType": "multipart-form-data"
}
```

**Auto-detecção:**
```javascript
{
  "url": "https://sua-api.easypanel.host/extract/auto",
  "method": "POST",
  "bodyContentType": "multipart-form-data"
}
```

## 🐛 Troubleshooting

### Build falhou?
- Verifique se todos os arquivos estão no repositório
- Confirme se o Dockerfile está presente

### Aplicação lenta?
- Aumente a memória para 4GB+
- Use apenas modelos necessários
- Verifique se o volume de cache está configurado

### Erro de memória?
- Configure swap na VPS
- Reduza modelos carregados
- Monitore uso no Easypanel

## 📈 Custos Hostinger

| VPS | RAM | CPU | Status |
|-----|-----|-----|--------|
| VPS 1 | 2GB | 1 core | ⚠️ Funciona mas lento |
| VPS 2 | 4GB | 2 cores | ✅ **Recomendado** |
| VPS 3 | 8GB | 4 cores | 🚀 Ideal para alto volume |

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch: `git checkout -b feature/nova-funcionalidade`
3. Commit: `git commit -m 'Add: nova funcionalidade'`
4. Push: `git push origin feature/nova-funcionalidade`
5. Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

## 🎉 Feito com

- ❤️ e muito café ☕
- 🐍 Python
- 🤖 OpenAI Whisper
- 🚀 FastAPI
- 🐳 Docker
- ☁️ Easypanel
