# 📊 Guia de Integração - Processamento de Planilhas para RAG

## 🎯 Visão Geral

Este guia mostra como processar planilhas com múltiplas abas e enviar os dados para o RAG no n8n de forma estruturada e otimizada.

## 🚀 Endpoints Disponíveis

### 1. `/extract-spreadsheet` - Processar Planilha

Extrai e estrutura dados de planilhas com múltiplas abas.

**Parâmetros:**
- `file`: Arquivo da planilha (xlsx, xls, csv)
- `format`: Formato de saída
  - `"markdown"` - Formato completo e detalhado
  - `"markdown-compact"` - Formato compacto em tabelas (recomendado para RAG)
  - `"json"` - Formato JSON estruturado
- `include_metadata`: true/false (incluir informações extras)

**Exemplo cURL:**
```bash
curl -X POST "https://seu-dominio.com/extract-spreadsheet" \
  -F "file=@planilha.xlsx" \
  -F "format=markdown-compact" \
  -F "include_metadata=true"
```

**Resposta:**
```json
{
  "status": "success",
  "file_type": "XLSX",
  "text": "# DADOS DA PLANILHA\n\n## Clientes\n...",
  "sheets": ["Clientes", "Produtos", "Vendas"],
  "total_sheets": 3,
  "total_rows": 150
}
```

### 2. `/extract-and-send-to-n8n` - Processar e Enviar Direto

Processa a planilha e envia automaticamente para o webhook do n8n.

**Parâmetros:**
- `file`: Arquivo da planilha
- `n8n_webhook_url`: URL do webhook do n8n
- `format`: Formato de saída
- `include_metadata`: true/false

**Exemplo cURL:**
```bash
curl -X POST "https://seu-dominio.com/extract-and-send-to-n8n" \
  -F "file=@planilha.xlsx" \
  -F "n8n_webhook_url=https://seu-n8n.com/webhook/planilha-rag" \
  -F "format=markdown-compact"
```

### 3. `/analyze-spreadsheet` - Analisar Estrutura

Analisa a planilha sem processar todos os dados (útil para preview).

**Exemplo cURL:**
```bash
curl -X POST "https://seu-dominio.com/analyze-spreadsheet" \
  -F "file=@planilha.xlsx"
```

## 📋 Workflow no n8n

### Workflow 1: Processar Planilha e Inserir no Vector Store

```json
{
  "name": "Planilha para RAG",
  "nodes": [
    {
      "parameters": {
        "httpMethod": "POST",
        "path": "planilha-upload",
        "responseMode": "responseNode",
        "options": {}
      },
      "name": "Webhook - Receber Planilha",
      "type": "n8n-nodes-base.webhook",
      "position": [240, 300]
    },
    {
      "parameters": {
        "url": "https://seu-dominio.com/extract-spreadsheet",
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
              "name": "format",
              "value": "markdown-compact"
            }
          ]
        }
      },
      "name": "Processar Planilha",
      "type": "n8n-nodes-base.httpRequest",
      "position": [460, 300]
    },
    {
      "parameters": {
        "jsCode": "// Dividir texto em chunks para o RAG\nconst text = $input.first().json.text;\nconst chunkSize = 2000;\nconst chunks = [];\n\nfor (let i = 0; i < text.length; i += chunkSize) {\n  chunks.push({\n    text: text.slice(i, i + chunkSize),\n    chunk_index: chunks.length,\n    source: $input.first().json.filename || 'planilha',\n    timestamp: new Date().toISOString()\n  });\n}\n\nreturn chunks.map(chunk => ({ json: chunk }));"
      },
      "name": "Dividir em Chunks",
      "type": "n8n-nodes-base.code",
      "position": [680, 300]
    },
    {
      "parameters": {
        "mode": "insert",
        "text": "={{ $json.text }}",
        "metadata": {
          "source": "={{ $json.source }}",
          "chunk_index": "={{ $json.chunk_index }}",
          "timestamp": "={{ $json.timestamp }}"
        }
      },
      "name": "Inserir no Vector Store",
      "type": "@n8n/n8n-nodes-langchain.vectorStoreSupabase",
      "position": [900, 300]
    },
    {
      "parameters": {
        "respondWith": "json",
        "responseBody": "={{ { \"status\": \"success\", \"chunks_inserted\": $items().length } }}"
      },
      "name": "Responder",
      "type": "n8n-nodes-base.respondToWebhook",
      "position": [1120, 300]
    }
  ],
  "connections": {
    "Webhook - Receber Planilha": {
      "main": [[{"node": "Processar Planilha", "type": "main", "index": 0}]]
    },
    "Processar Planilha": {
      "main": [[{"node": "Dividir em Chunks", "type": "main", "index": 0}]]
    },
    "Dividir em Chunks": {
      "main": [[{"node": "Inserir no Vector Store", "type": "main", "index": 0}]]
    },
    "Inserir no Vector Store": {
      "main": [[{"node": "Responder", "type": "main", "index": 0}]]
    }
  }
}
```

### Workflow 2: Processar Planilhas do Google Drive Automaticamente

```json
{
  "name": "Google Drive Planilha Auto-RAG",
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
              "value2": "spreadsheet"
            }
          ]
        }
      },
      "name": "Verificar se é Planilha",
      "type": "n8n-nodes-base.if",
      "position": [460, 300]
    },
    {
      "parameters": {
        "fileId": "={{ $json.id }}",
        "options": {
          "googleFileConversion": {
            "conversion": {
              "doConversion": true,
              "conversionFormat": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            }
          }
        }
      },
      "name": "Download do Drive",
      "type": "n8n-nodes-base.googleDrive",
      "position": [680, 200]
    },
    {
      "parameters": {
        "url": "https://seu-dominio.com/extract-and-send-to-n8n",
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
              "name": "n8n_webhook_url",
              "value": "https://seu-n8n.com/webhook/inserir-rag"
            },
            {
              "name": "format",
              "value": "markdown-compact"
            }
          ]
        }
      },
      "name": "Processar e Enviar para RAG",
      "type": "n8n-nodes-base.httpRequest",
      "position": [900, 200]
    },
    {
      "parameters": {
        "operation": "upload",
        "fileContent": "={{ $json.text }}",
        "name": "={{ $('Download do Drive').item.json.name + '_processado.txt' }}",
        "parents": {
          "folderId": "SEU_FOLDER_ID"
        }
      },
      "name": "Salvar Texto Processado",
      "type": "n8n-nodes-base.googleDrive",
      "position": [1120, 200]
    }
  ]
}
```

### Workflow 3: Processar Planilha com Análise Prévia

```json
{
  "name": "Planilha com Preview",
  "nodes": [
    {
      "parameters": {
        "httpMethod": "POST",
        "path": "planilha-preview",
        "responseMode": "responseNode"
      },
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "position": [240, 300]
    },
    {
      "parameters": {
        "url": "https://seu-dominio.com/analyze-spreadsheet",
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
      "name": "Analisar Estrutura",
      "type": "n8n-nodes-base.httpRequest",
      "position": [460, 300]
    },
    {
      "parameters": {
        "conditions": {
          "number": [
            {
              "value1": "={{ $json.analysis.total_sheets }}",
              "operation": "largerEqual",
              "value2": 1
            }
          ]
        }
      },
      "name": "Verificar se tem Dados",
      "type": "n8n-nodes-base.if",
      "position": [680, 300]
    },
    {
      "parameters": {
        "url": "https://seu-dominio.com/extract-spreadsheet",
        "method": "POST",
        "sendBody": true,
        "bodyContentType": "multipart-form-data",
        "bodyParameters": {
          "parameters": [
            {
              "name": "file",
              "value": "={{ $('Webhook').item.binary.data }}"
            },
            {
              "name": "format",
              "value": "markdown-compact"
            }
          ]
        }
      },
      "name": "Processar Completo",
      "type": "n8n-nodes-base.httpRequest",
      "position": [900, 200]
    }
  ]
}
```

## 🎯 Casos de Uso

### 1. Planilha de Produtos para E-commerce

```javascript
// Nó Function - Processar dados de produtos
const data = $input.first().json;

// Extrair informações específicas
const produtos = data.sheets.Produtos.rows.map(row => ({
  nome: row['Nome do Produto'],
  preco: parseFloat(row['Preço']),
  categoria: row['Categoria'],
  descricao: row['Descrição'],
  estoque: parseInt(row['Estoque'])
}));

// Criar texto otimizado para RAG
const textoRAG = produtos.map(p => 
  `Produto: ${p.nome}
   Categoria: ${p.categoria}
   Preço: R$ ${p.preco.toFixed(2)}
   Descrição: ${p.descricao}
   Estoque: ${p.estoque} unidades`
).join('\n\n---\n\n');

return [{ json: { texto: textoRAG, produtos } }];
```

### 2. Base de Conhecimento de FAQ

```javascript
// Nó Function - Processar FAQ
const data = $input.first().json;
const faq = data.sheets.FAQ.rows;

// Formatar para RAG (formato pergunta-resposta)
const textoRAG = faq.map((item, idx) => 
  `FAQ ${idx + 1}:
   Pergunta: ${item['Pergunta']}
   Resposta: ${item['Resposta']}
   Categoria: ${item['Categoria'] || 'Geral'}
   Tags: ${item['Tags'] || ''}`
).join('\n\n---\n\n');

return [{ json: { texto: textoRAG, total_faqs: faq.length } }];
```

### 3. Processar Planilha de Vendas com Análise

```javascript
// Nó Function - Análise e estruturação
const sheets = $input.first().json.data.sheets;

let resultado = {
  resumo: [],
  dados_completos: []
};

// Processar cada aba
for (const [nome, dados] of Object.entries(sheets)) {
  // Criar resumo estatístico
  const resumo = {
    aba: nome,
    total_registros: dados.total_rows,
    colunas: dados.headers
  };
  
  // Se for aba de vendas, calcular totais
  if (nome.toLowerCase().includes('venda')) {
    const total = dados.rows.reduce((sum, row) => {
      const valor = parseFloat(row['Valor'] || row['Total'] || 0);
      return sum + valor;
    }, 0);
    resumo.total_vendas = total;
  }
  
  resultado.resumo.push(resumo);
  resultado.dados_completos.push({
    aba: nome,
    dados: dados.rows
  });
}

return [{ json: resultado }];
```

## 📊 Formatos de Saída

### Markdown (Detalhado)
```markdown
# DADOS DA PLANILHA

Data de processamento: 2025-09-29 10:30:00
Total de abas: 2

## ABA: Clientes
Total de registros: 50
Colunas: Nome, Email, Telefone, Cidade

### Registro 1
- **Nome**: João Silva
- **Email**: joao@example.com
- **Telefone**: (11) 99999-9999
- **Cidade**: São Paulo
```

### Markdown Compact (Recomendado para RAG)
```markdown
# DADOS DA PLANILHA

## Clientes
*50 registros*

| Nome | Email | Telefone | Cidade |
|---|---|---|---|
| João Silva | joao@example.com | (11) 99999-9999 | São Paulo |
| Maria Santos | maria@example.com | (21) 88888-8888 | Rio de Janeiro |
```

### JSON
```json
{
  "processed_at": "2025-09-29T10:30:00",
  "total_sheets": 2,
  "sheets": {
    "Clientes": {
      "headers": ["Nome", "Email", "Telefone", "Cidade"],
      "rows": [
        {
          "Nome": "João Silva",
          "Email": "joao@example.com",
          "Telefone": "(11) 99999-9999",
          "Cidade": "São Paulo"
        }
      ],
      "total_rows": 50
    }
  }
}
```

## 🔧 Boas Práticas

### 1. Chunking para RAG

Para planilhas grandes, divida os dados em chunks:

```javascript
// Nó Function - Chunking inteligente
const CHUNK_SIZE = 2000; // caracteres
const text = $input.first().json.text;
const sheets = $input.first().json.sheets;

const chunks = [];
let currentChunk = '';
let chunkMeta = {
  sheets_included: []
};

// Dividir por aba para manter contexto
for (const sheetName of sheets) {
  const sheetText = extractSheetText(text, sheetName);
  
  if (currentChunk.length + sheetText.length > CHUNK_SIZE) {
    // Salvar chunk atual
    chunks.push({
      text: currentChunk,
      metadata: { ...chunkMeta }
    });
    
    // Iniciar novo chunk
    currentChunk = sheetText;
    chunkMeta = { sheets_included: [sheetName] };
  } else {
    currentChunk += '\n\n' + sheetText;
    chunkMeta.sheets_included.push(sheetName);
  }
}

// Adicionar último chunk
if (currentChunk) {
  chunks.push({
    text: currentChunk,
    metadata: chunkMeta
  });
}

return chunks.map(c => ({ json: c }));
```

### 2. Validação de Dados

```javascript
// Nó Function - Validar planilha antes de processar
const analysis = $input.first().json.analysis;

// Verificações
const errors = [];
const warnings = [];

// Verificar se tem abas
if (analysis.total_sheets === 0) {
  errors.push('Planilha não contém abas');
}

// Verificar tamanho
const totalRows = analysis.sheets_info.reduce((sum, s) => sum + s.total_rows, 0);
if (totalRows > 10000) {
  warnings.push(`Planilha muito grande (${totalRows} linhas). Considere dividir.`);
}

// Verificar colunas vazias
for (const sheet of analysis.sheets_info) {
  const emptyCols = sheet.columns.filter(c => !c || c.startsWith('Coluna_'));
  if (emptyCols.length > 0) {
    warnings.push(`Aba "${sheet.name}" tem ${emptyCols.length} colunas sem nome`);
  }
}

if (errors.length > 0) {
  throw new Error(`Erros na validação: ${errors.join(', ')}`);
}

return [{ 
  json: { 
    valid: true, 
    warnings,
    analysis 
  } 
}];
```

### 3. Metadados Enriquecidos

```javascript
// Nó Function - Adicionar metadados ricos
const data = $input.first().json;

const enriched = {
  ...data,
  metadata: {
    processed_at: new Date().toISOString(),
    source: 'spreadsheet',
    filename: data.filename || 'unknown',
    sheets_count: data.total_sheets,
    total_rows: data.total_rows,
    format: 'structured_data',
    language: 'pt-BR',
    version: '1.0'
  }
};

return [{ json: enriched }];
```

## 🚀 Scripts de Teste

### Teste Local (PowerShell)

```powershell
# test-spreadsheet.ps1

$url = "http://localhost:8000"
$file = "D:\planilha-teste.xlsx"

# Teste 1: Análise da planilha
Write-Host "Testando análise da planilha..." -ForegroundColor Cyan
$response = curl.exe -X POST "$url/analyze-spreadsheet" `
  -F "file=@$file"

Write-Host $response

# Teste 2: Extração markdown compact
Write-Host "`nTestando extração markdown compact..." -ForegroundColor Cyan
$response = curl.exe -X POST "$url/extract-spreadsheet" `
  -F "file=@$file" `
  -F "format=markdown-compact"

Write-Host $response

# Teste 3: Extração JSON
Write-Host "`nTestando extração JSON..." -ForegroundColor Cyan
$response = curl.exe -X POST "$url/extract-spreadsheet" `
  -F "file=@$file" `
  -F "format=json"

Write-Host $response
```

### Teste com n8n

```bash
#!/bin/bash
# test-with-n8n.sh

API_URL="https://seu-dominio.com"
N8N_WEBHOOK="https://seu-n8n.com/webhook/test-planilha"
FILE="planilha-teste.xlsx"

echo "Enviando planilha para n8n..."
curl -X POST "$API_URL/extract-and-send-to-n8n" \
  -F "file=@$FILE" \
  -F "n8n_webhook_url=$N8N_WEBHOOK" \
  -F "format=markdown-compact" \
  | jq '.'
```

## 🎯 Dicas para RAG

1. **Use formato markdown-compact** para economizar tokens
2. **Divida planilhas grandes** em chunks de ~2000 caracteres
3. **Mantenha metadados** sobre a aba de origem
4. **Normalize dados** antes de enviar (datas, números, etc)
5. **Crie índices** para busca eficiente no vector store
6. **Use embeddings** específicos para dados tabulares se disponível

## 📈 Monitoramento

```javascript
// Nó Function - Log de processamento
const startTime = Date.now();

// ... processamento ...

const endTime = Date.now();
const duration = endTime - startTime;

// Enviar para sistema de logs
$http.post('https://seu-sistema-logs.com/api/logs', {
  json: {
    type: 'spreadsheet_processing',
    filename: $json.filename,
    sheets: $json.total_sheets,
    rows: $json.total_rows,
    duration_ms: duration,
    format: $json.format,
    timestamp: new Date().toISOString()
  }
});
```

---

**Versão**: 1.0.0  
**Última atualização**: Setembro 2025
