# 📊 Solução Completa - Processamento de Planilhas para RAG

## ✅ Problema Resolvido

**Problema**: Arquivos CSV baixados do Google Drive não eram detectados corretamente porque o n8n não preserva a extensão `.csv` no nome do arquivo.

**Solução**: Implementada detecção inteligente de tipo de arquivo usando:
1. **MIME Type** (content_type) - prioridade máxima
2. **Conteúdo do arquivo** (primeiros bytes)
3. **Extensão do arquivo** - fallback

## 🎯 Endpoints Criados

### 1. `/extract-for-n8n` ⭐ (Recomendado)
**Uso**: Processar planilha e retornar dados estruturados para n8n

```bash
curl -X POST "http://localhost:8000/extract-for-n8n" \
  -F "file=@sua-planilha.xlsx"
```

**Retorna**:
```json
{
  "status": "success",
  "filename": "planilha.xlsx",
  "file_type": "XLSX",
  "total_sheets": 3,
  "total_rows": 150,
  "sheets": [
    {
      "sheet_name": "Produtos",
      "metadata": {
        "total_rows": 50,
        "total_columns": 6,
        "columns": ["ID", "Nome", "Categoria", "Preço", "Estoque", "Fornecedor"],
        "source_file": "planilha.xlsx",
        "file_type": "XLSX",
        "processed_at": "2025-09-29T10:30:00"
      },
      "data": [
        {
          "ID": "001",
          "Nome": "Mouse Gamer",
          "Categoria": "Informática",
          "Preço": "89.90",
          "Estoque": "45",
          "Fornecedor": "Fornecedor A"
        }
      ]
    }
  ]
}
```

### 2. `/extract-and-send-to-n8n`
**Uso**: Processar e enviar diretamente para webhook do n8n

```bash
curl -X POST "http://localhost:8000/extract-and-send-to-n8n" \
  -F "file=@sua-planilha.xlsx" \
  -F "n8n_webhook_url=https://seu-n8n.com/webhook/planilha"
```

### 3. `/debug-file` 🔧
**Uso**: Debug de arquivos para diagnosticar problemas

```bash
curl -X POST "http://localhost:8000/debug-file" \
  -F "file=@seu-arquivo.csv"
```

## 🔄 Workflow no n8n

### Passo 1: Download do Google Drive
- Configure o nó "Google Drive" normalmente
- O arquivo será baixado (pode não ter extensão)

### Passo 2: Processar Planilha
```json
{
  "url": "https://seu-servico.com/extract-for-n8n",
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

### Passo 3: Split por Aba
- Use "Split Out" no campo `sheets`
- Cada item será uma aba da planilha

### Passo 4: Processar Dados
```javascript
// Nó Code - Processar cada aba
const sheet = $input.first().json;

// Acessar metadados
const sheetName = sheet.sheet_name;
const totalRows = sheet.metadata.total_rows;
const columns = sheet.metadata.columns;

// Processar dados da aba
const allRows = sheet.data;

// Criar texto para RAG
let texto = `# ${sheetName}\n\n`;
allRows.forEach((row, idx) => {
  texto += `## Registro ${idx + 1}\n`;
  for (const [key, value] of Object.entries(row)) {
    if (value) {
      texto += `- ${key}: ${value}\n`;
    }
  }
  texto += '\n';
});

return [{
  json: {
    texto: texto,
    sheet_name: sheetName,
    metadata: sheet.metadata
  }
}];
```

### Passo 5: Vetorizar (seu processo)
- Use seu sistema de embeddings
- Insira no vector store
- Configure metadados como preferir

## 📁 Arquivos Criados

1. **`src/transcribe_spreadsheet.py`** - Serviço principal
2. **`Dockerfile.spreadsheet`** - Container Docker
3. **`requirements_spreadsheet.txt`** - Dependências
4. **`docker-compose-spreadsheet.yml`** - Orquestração
5. **`nginx-spreadsheet.conf`** - Load balancer
6. **`FORMATO-N8N.md`** - Guia de uso no n8n
7. **`TESTE-GOOGLE-DRIVE.md`** - Solução do problema CSV
8. **`test-spreadsheet.ps1`** - Script de teste Windows
9. **`test-spreadsheet.sh`** - Script de teste Linux/Mac

## 🚀 Como Usar

### 1. Instalação Local
```bash
pip install -r requirements_spreadsheet.txt
uvicorn src.transcribe_spreadsheet:app --reload --port 8000
```

### 2. Docker
```bash
docker build -f Dockerfile.spreadsheet -t avantar-spreadsheet .
docker run -p 8000:8000 avantar-spreadsheet
```

### 3. Docker Compose
```bash
docker-compose -f docker-compose-spreadsheet.yml up -d
```

## 🎯 Vantagens da Solução

✅ **Detecção Inteligente**: Funciona com qualquer fonte (Google Drive, upload direto, etc)
✅ **Dados Estruturados**: Cada aba é um objeto com metadados completos
✅ **Flexibilidade Total**: Você decide como chunking e vetorizar no n8n
✅ **Sem Perda de Dados**: Todos os dados são preservados
✅ **Metadados Ricos**: Informações sobre origem, colunas, timestamps
✅ **Compatibilidade**: XLSX, XLS, CSV

## 🔧 Troubleshooting

### Problema: "Formato não suportado"
**Solução**: Use `/debug-file` para ver o que está sendo recebido

### Problema: "Erro ao processar CSV"
**Solução**: Verifique encoding do arquivo (UTF-8, Latin-1)

### Problema: "Timeout no n8n"
**Solução**: Para planilhas muito grandes, processe por partes

## 📊 Exemplo de Dados Retornados

Para um CSV com dados de produtos:

```json
{
  "sheets": [
    {
      "sheet_name": "Planilha",
      "metadata": {
        "total_rows": 10,
        "total_columns": 5,
        "columns": ["Produto", "Preço", "Categoria", "Estoque", "Fornecedor"],
        "source_file": "GUIA COMERCIAL",
        "file_type": "CSV",
        "processed_at": "2025-09-29T10:30:00"
      },
      "data": [
        {
          "Produto": "Mouse Gamer",
          "Preço": "89.90",
          "Categoria": "Informática",
          "Estoque": "45",
          "Fornecedor": "Fornecedor A"
        }
      ]
    }
  ]
}
```

## 🎉 Resultado Final

Agora você tem:
- ✅ Script que detecta CSV do Google Drive corretamente
- ✅ Dados estruturados prontos para n8n
- ✅ Controle total sobre chunking e vetorização
- ✅ Metadados completos para cada aba
- ✅ Flexibilidade para processar como preferir

**Próximo passo**: Configure seu workflow no n8n usando o endpoint `/extract-for-n8n` e processe os dados como preferir!
