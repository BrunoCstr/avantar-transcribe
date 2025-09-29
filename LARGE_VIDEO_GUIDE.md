# 🎥 Guia para Vídeos Grandes - API de Transcrição

## 📊 **Limites Atualizados**

✅ **Limite aumentado de 100MB para 200MB** nos endpoints padrão
✅ **Novo endpoint para vídeos grandes**: até **500MB**
✅ **Otimizações específicas** para sua VPS de 8GB RAM

## 🚀 **Endpoints Disponíveis**

### 1. **Endpoint Padrão** (até 200MB)
```bash
POST /transcribe-video
```
- **Limite**: 200MB
- **Otimizado para**: Vídeos médios
- **Uso recomendado**: Arquivos de até 200MB

### 2. **Endpoint para Vídeos Grandes** (até 500MB) ⭐ **NOVO**
```bash
POST /transcribe-large-video
```
- **Limite**: 500MB
- **Otimizado para**: Arquivos grandes como o seu de 106MB
- **Uso recomendado**: Arquivos de 100MB+

## 🔧 **Otimizações Implementadas**

### **Para sua VPS de 8GB RAM:**
- ✅ **Modelo Whisper Tiny**: Usa apenas ~1-2GB RAM
- ✅ **FFmpeg otimizado**: 2 threads, timeout de 10 minutos
- ✅ **Limpeza automática**: Remove arquivos temporários
- ✅ **Processamento eficiente**: Configurações otimizadas para arquivos grandes

### **Configurações Especiais para Arquivos Grandes:**
- `condition_on_previous_text: False` - Economiza memória
- `compression_ratio_threshold: 2.4` - Melhor qualidade
- `no_speech_threshold: 0.6` - Detecta silêncio melhor
- `threads: 2` - Usa apenas 2 cores CPU

## 📝 **Como Usar**

### **Para seu vídeo de 106MB:**

```bash
# Usar o endpoint otimizado para vídeos grandes
curl -X POST "https://sua-api.com/transcribe-large-video" \
  -F "file=@seu_video_106mb.mp4" \
  -F "language=pt"
```

### **Via n8n (seu caso):**
1. Mude a URL para: `/transcribe-large-video`
2. Mantenha os mesmos parâmetros
3. O arquivo de 106MB agora será aceito!

## ⚡ **Performance Esperada**

### **Para vídeo de 106MB:**
- **Tempo de conversão**: ~2-5 minutos (FFmpeg)
- **Tempo de transcrição**: ~5-15 minutos (Whisper)
- **Total estimado**: ~10-20 minutos
- **Uso de RAM**: Pico de ~3-4GB (dentro do limite de 8GB)

## 🎯 **Recomendações**

1. **Use `/transcribe-large-video`** para arquivos > 100MB
2. **Mantenha a VPS com pelo menos 1GB livre** durante o processamento
3. **Monitore os logs** para acompanhar o progresso
4. **Vídeos muito longos** (> 30 min) podem demorar mais

## 🔍 **Monitoramento**

### **Verificar status:**
```bash
GET /health
```

### **Resposta esperada:**
```json
{
  "ok": true,
  "services": {
    "video_transcription": true
  },
  "limits": {
    "max_file_size_mb": 200,
    "max_large_video_mb": 500
  }
}
```

## ⚠️ **Importante**

- **Seu vídeo de 106MB** agora será aceito pelo endpoint `/transcribe-large-video`
- **Mude a URL no n8n** de `/transcribe-video` para `/transcribe-large-video`
- **O processamento pode demorar** 10-20 minutos para arquivos grandes
- **Mantenha o timeout do n8n** em pelo menos 30 minutos

## 🎉 **Resultado**

Seu arquivo de 106MB agora será processado com sucesso! 🚀
