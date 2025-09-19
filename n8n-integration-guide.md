# 🔗 Guia de Integração com n8n

## Configuração Básica no n8n

### 1. Criar Workflow de Transcrição

#### Nó 1: Webhook (Trigger)
```json
{
  "httpMethod": "POST",
  "path": "transcribe-audio",
  "responseMode": "responseNode",
  "options": {}
}
```

#### Nó 2: HTTP Request (Whisper API)
```json
{
  "url": "https://seu-dominio.com/transcribe-whatsapp",
  "method": "POST",
  "sendBody": true,
  "bodyContentType": "multipart-form-data",
  "bodyParameters": {
    "parameters": [
      {
        "name": "file",
        "value": "={{ $binary.data }}"
      }
    ]
  }
}
```

#### Nó 3: Respond to Webhook
```json
{
  "respondWith": "json",
  "responseBody": "={{ $json }}"
}
```

## Workflows Específicos

### 1. Workflow para WhatsApp Business API

```json
{
  "name": "WhatsApp Audio Transcription",
  "nodes": [
    {
      "parameters": {
        "httpMethod": "POST",
        "path": "whatsapp-webhook",
        "responseMode": "responseNode"
      },
      "name": "WhatsApp Webhook",
      "type": "n8n-nodes-base.webhook",
      "position": [240, 300]
    },
    {
      "parameters": {
        "conditions": {
          "string": [
            {
              "value1": "={{ $json.entry[0].changes[0].value.messages[0].type }}",
              "value2": "audio"
            }
          ]
        }
      },
      "name": "Check if Audio",
      "type": "n8n-nodes-base.if",
      "position": [460, 300]
    },
    {
      "parameters": {
        "url": "={{ $json.entry[0].changes[0].value.messages[0].audio.id }}",
        "authentication": "genericCredentialType",
        "genericAuthType": "httpHeaderAuth",
        "headers": {
          "Authorization": "Bearer SEU_TOKEN_WHATSAPP"
        }
      },
      "name": "Download Audio from WhatsApp",
      "type": "n8n-nodes-base.httpRequest",
      "position": [680, 200]
    },
    {
      "parameters": {
        "url": "https://seu-dominio.com/transcribe-whatsapp",
        "method": "POST",
        "sendBody": true,
        "bodyContentType": "multipart-form-data",
        "bodyParameters": {
          "parameters": [
            {
              "name": "file",
              "value": "={{ $binary.data }}"
            }
          ]
        }
      },
      "name": "Transcribe Audio",
      "type": "n8n-nodes-base.httpRequest",
      "position": [900, 200]
    },
    {
      "parameters": {
        "url": "https://graph.facebook.com/v17.0/SEU_PHONE_NUMBER_ID/messages",
        "method": "POST",
        "sendBody": true,
        "bodyContentType": "json",
        "jsonBody": "={\n  \"messaging_product\": \"whatsapp\",\n  \"to\": \"{{ $('WhatsApp Webhook').item.json.entry[0].changes[0].value.messages[0].from }}\",\n  \"text\": {\n    \"body\": \"Transcrição: {{ $json.text }}\"\n  }\n}",
        "headers": {
          "Authorization": "Bearer SEU_TOKEN_WHATSAPP",
          "Content-Type": "application/json"
        }
      },
      "name": "Send Transcription Back",
      "type": "n8n-nodes-base.httpRequest",
      "position": [1120, 200]
    },
    {
      "parameters": {
        "respondWith": "text",
        "responseBody": "OK"
      },
      "name": "Respond to Webhook",
      "type": "n8n-nodes-base.respondToWebhook",
      "position": [1340, 300]
    }
  ],
  "connections": {
    "WhatsApp Webhook": {
      "main": [
        [
          {
            "node": "Check if Audio",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Check if Audio": {
      "main": [
        [
          {
            "node": "Download Audio from WhatsApp",
            "type": "main",
            "index": 0
          }
        ],
        [
          {
            "node": "Respond to Webhook",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Download Audio from WhatsApp": {
      "main": [
        [
          {
            "node": "Transcribe Audio",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Transcribe Audio": {
      "main": [
        [
          {
            "node": "Send Transcription Back",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Send Transcription Back": {
      "main": [
        [
          {
            "node": "Respond to Webhook",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  }
}
```

### 2. Workflow para Processar Vídeos de Diretório

```json
{
  "name": "Batch Video Transcription",
  "nodes": [
    {
      "parameters": {
        "rule": {
          "interval": [
            {
              "field": "hours",
              "hoursInterval": 1
            }
          ]
        }
      },
      "name": "Schedule Trigger",
      "type": "n8n-nodes-base.scheduleTrigger",
      "position": [240, 300]
    },
    {
      "parameters": {
        "command": "find /path/to/videos -name '*.mp4' -o -name '*.avi' -o -name '*.mov'"
      },
      "name": "Find Video Files",
      "type": "n8n-nodes-base.executeCommand",
      "position": [460, 300]
    },
    {
      "parameters": {
        "fieldName": "videos",
        "include": "onlyIncluded",
        "fields": "stdout"
      },
      "name": "Split Video List",
      "type": "n8n-nodes-base.splitInBatches",
      "position": [680, 300]
    },
    {
      "parameters": {
        "filePath": "={{ $json.stdout.split('\\n')[$index] }}",
        "options": {}
      },
      "name": "Read Video File",
      "type": "n8n-nodes-base.readBinaryFile",
      "position": [900, 300]
    },
    {
      "parameters": {
        "url": "https://seu-dominio.com/transcribe-video",
        "method": "POST",
        "sendBody": true,
        "bodyContentType": "multipart-form-data",
        "bodyParameters": {
          "parameters": [
            {
              "name": "file",
              "value": "={{ $binary.data }}"
            },
            {
              "name": "language",
              "value": "pt"
            }
          ]
        }
      },
      "name": "Transcribe Video",
      "type": "n8n-nodes-base.httpRequest",
      "position": [1120, 300]
    },
    {
      "parameters": {
        "filePath": "={{ $('Read Video File').item.json.filePath.replace(/\\.[^/.]+$/, '_transcript.txt') }}",
        "fileContent": "={{ $json.text }}"
      },
      "name": "Save Transcript",
      "type": "n8n-nodes-base.writeBinaryFile",
      "position": [1340, 300]
    }
  ]
}
```

### 3. Workflow com Google Drive

```json
{
  "name": "Google Drive Audio Transcription",
  "nodes": [
    {
      "parameters": {
        "folderId": "SEU_FOLDER_ID",
        "event": "fileCreated",
        "options": {}
      },
      "name": "Google Drive Trigger",
      "type": "n8n-nodes-base.googleDriveTrigger",
      "position": [240, 300]
    },
    {
      "parameters": {
        "conditions": {
          "string": [
            {
              "value1": "={{ $json.mimeType }}",
              "operation": "contains",
              "value2": "audio/"
            }
          ]
        }
      },
      "name": "Check if Audio File",
      "type": "n8n-nodes-base.if",
      "position": [460, 300]
    },
    {
      "parameters": {
        "fileId": "={{ $json.id }}",
        "options": {}
      },
      "name": "Download from Drive",
      "type": "n8n-nodes-base.googleDrive",
      "position": [680, 200]
    },
    {
      "parameters": {
        "url": "https://seu-dominio.com/transcribe",
        "method": "POST",
        "sendBody": true,
        "bodyContentType": "multipart-form-data",
        "bodyParameters": {
          "parameters": [
            {
              "name": "file",
              "value": "={{ $binary.data }}"
            },
            {
              "name": "language",
              "value": "pt"
            }
          ]
        }
      },
      "name": "Transcribe Audio",
      "type": "n8n-nodes-base.httpRequest",
      "position": [900, 200]
    },
    {
      "parameters": {
        "operation": "upload",
        "fileContent": "={{ $json.text }}",
        "name": "={{ $('Download from Drive').item.json.name.replace(/\\.[^/.]+$/, '_transcript.txt') }}",
        "parents": {
          "folderId": "SEU_FOLDER_ID"
        }
      },
      "name": "Upload Transcript to Drive",
      "type": "n8n-nodes-base.googleDrive",
      "position": [1120, 200]
    }
  ]
}
```

## Configurações Avançadas

### 1. Tratamento de Erros

```javascript
// Código para nó Function - Tratamento de Erro
const items = $input.all();

for (const item of items) {
  try {
    // Verificar se a transcrição foi bem-sucedida
    if (!item.json.text || item.json.text.trim() === '') {
      throw new Error('Transcrição vazia');
    }
    
    // Adicionar metadados
    item.json.transcription_date = new Date().toISOString();
    item.json.status = 'success';
    
  } catch (error) {
    item.json.status = 'error';
    item.json.error_message = error.message;
    item.json.transcription_date = new Date().toISOString();
  }
}

return items;
```

### 2. Cache e Otimização

```javascript
// Código para nó Function - Verificar Cache
const items = $input.all();
const results = [];

for (const item of items) {
  const filename = item.json.filename;
  const fileHash = item.json.file_hash || 'unknown';
  
  // Verificar se já foi processado (usando banco de dados ou arquivo)
  const cacheKey = `${filename}_${fileHash}`;
  
  // Simular verificação de cache
  const cached = $workflow.getStaticData('global')[cacheKey];
  
  if (cached) {
    item.json = {
      ...item.json,
      ...cached,
      cached: true
    };
  } else {
    // Marcar para processamento
    item.json.needs_processing = true;
  }
  
  results.push(item);
}

return results;
```

### 3. Webhook para Status de Processamento

```javascript
// Endpoint para verificar status de transcrição
// GET /transcription-status/:id

const express = require('express');
const app = express();

app.get('/transcription-status/:id', (req, res) => {
  const transcriptionId = req.params.id;
  
  // Verificar status no seu sistema
  const status = checkTranscriptionStatus(transcriptionId);
  
  res.json({
    id: transcriptionId,
    status: status.status, // 'processing', 'completed', 'error'
    progress: status.progress, // 0-100
    result: status.result || null,
    error: status.error || null
  });
});
```

## Exemplos de Uso

### 1. Curl para testar endpoints

```bash
# Transcrever áudio do WhatsApp
curl -X POST "https://seu-dominio.com/transcribe-whatsapp" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@audio_whatsapp.ogg"

# Transcrever vídeo
curl -X POST "https://seu-dominio.com/transcribe-video" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@video.mp4" \
     -F "language=pt"

# Verificar cache
curl "https://seu-dominio.com/cache/stats"
```

### 2. JavaScript para frontend

```javascript
// Função para upload e transcrição
async function transcribeAudio(file, isWhatsApp = false) {
  const formData = new FormData();
  formData.append('file', file);
  
  const endpoint = isWhatsApp ? '/transcribe-whatsapp' : '/transcribe';
  
  try {
    const response = await fetch(`https://seu-dominio.com${endpoint}`, {
      method: 'POST',
      body: formData
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const result = await response.json();
    return result;
    
  } catch (error) {
    console.error('Erro na transcrição:', error);
    throw error;
  }
}

// Uso
const audioFile = document.getElementById('audioInput').files[0];
transcribeAudio(audioFile, true)
  .then(result => {
    console.log('Transcrição:', result.text);
    console.log('Modelo usado:', result.model_used);
    console.log('Duração:', result.duration);
  })
  .catch(error => {
    console.error('Falha na transcrição:', error);
  });
```

### 3. Python para automação

```python
import requests
import os
from pathlib import Path

def transcribe_directory(directory_path, api_url):
    """Transcrever todos os áudios de um diretório"""
    
    audio_extensions = ['.mp3', '.wav', '.ogg', '.m4a', '.flac']
    results = []
    
    for file_path in Path(directory_path).rglob('*'):
        if file_path.suffix.lower() in audio_extensions:
            
            with open(file_path, 'rb') as audio_file:
                files = {'file': audio_file}
                
                # Detectar se é áudio do WhatsApp pelo nome
                is_whatsapp = 'whatsapp' in file_path.name.lower() or 'ptt' in file_path.name.lower()
                endpoint = '/transcribe-whatsapp' if is_whatsapp else '/transcribe'
                
                try:
                    response = requests.post(f"{api_url}{endpoint}", files=files)
                    response.raise_for_status()
                    
                    result = response.json()
                    result['file_path'] = str(file_path)
                    results.append(result)
                    
                    print(f"✅ {file_path.name}: {result['text'][:100]}...")
                    
                except requests.exceptions.RequestException as e:
                    print(f"❌ Erro ao processar {file_path.name}: {e}")
                    
    return results

# Uso
results = transcribe_directory('/path/to/audio/files', 'https://seu-dominio.com')

# Salvar resultados
import json
with open('transcriptions.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
```

## Monitoramento e Logs no n8n

### 1. Webhook para logs
```javascript
// Nó Function para logging
const logData = {
  timestamp: new Date().toISOString(),
  workflow_id: $workflow.id,
  execution_id: $execution.id,
  file_name: $json.filename,
  file_size: $json.file_size,
  model_used: $json.model_used,
  duration: $json.duration,
  cached: $json.cached,
  processing_time: Date.now() - $json.start_time
};

// Enviar para sistema de logs
$http.post('https://seu-sistema-logs.com/api/logs', {
  json: logData
});

return $input.all();
```

### 2. Alertas por email/Slack
```javascript
// Nó Function para alertas
const items = $input.all();

for (const item of items) {
  // Verificar se houve erro
  if (item.json.status === 'error') {
    // Enviar alerta
    const alertData = {
      type: 'error',
      message: `Falha na transcrição: ${item.json.filename}`,
      error: item.json.error_message,
      timestamp: new Date().toISOString()
    };
    
    // Configurar webhook do Slack ou email
    // ...
  }
  
  // Verificar tempo de processamento alto
  if (item.json.processing_time > 300000) { // 5 minutos
    // Alerta de performance
    // ...
  }
}

return items;
```

Este guia fornece uma base sólida para integrar seu serviço de transcrição com n8n, cobrindo desde casos simples até workflows complexos de automação!
