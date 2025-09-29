# 🔧 Teste com Google Drive - CSV

## 🎯 Problema Identificado

Quando você baixa um arquivo CSV do Google Drive, o n8n pode não preservar a extensão `.csv` no nome do arquivo, mas o `content_type` será `text/csv`.

## ✅ Solução Implementada

O script agora detecta o tipo de arquivo por:
1. **MIME Type** (content_type) - prioridade máxima
2. **Conteúdo do arquivo** (primeiros bytes)
3. **Extensão do arquivo** - fallback

## 🧪 Como Testar

### 1. Teste de Debug

Use o endpoint `/debug-file` para ver exatamente o que está sendo recebido:

```bash
# No n8n, adicione um nó HTTP Request após o Download File
# URL: https://seu-servico.com/debug-file
# Method: POST
# Body: multipart-form-data
# Parâmetros:
#   - file: {{ $binary.data }}
```

### 2. Exemplo de Resposta do Debug

```json
{
  "status": "success",
  "file_info": {
    "filename": "GUIA COMERCIAL",  // ← Sem extensão
    "content_type": "text/csv",    // ← MIME type correto
    "size_bytes": 719,
    "detected_type": "CSV",        // ← Agora detecta corretamente
    "csv_processing": "success",
    "csv_sheets": ["Planilha"]
  }
}
```

### 3. Teste Completo

```bash
# Teste direto com curl
curl -X POST "http://localhost:8000/debug-file" \
  -F "file=@seu-arquivo.csv"
```

## 🔄 Workflow no n8n

### Nó 1: Google Drive Download
- Configure normalmente
- O arquivo será baixado sem extensão

### Nó 2: HTTP Request (Debug)
```json
{
  "url": "https://seu-servico.com/debug-file",
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

### Nó 3: HTTP Request (Processar)
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

## 🎯 Resultado Esperado

Agora o script deve:
1. ✅ Detectar CSV pelo `content_type: text/csv`
2. ✅ Processar o arquivo corretamente
3. ✅ Retornar dados estruturados para o RAG

## 🐛 Se Ainda Der Erro

### Verificar Logs

```bash
# Ver logs do serviço
docker logs avantar-spreadsheet

# Ou se rodando local
# Os logs aparecerão no terminal
```

### Informações de Debug

O endpoint `/debug-file` mostrará:
- Nome do arquivo recebido
- Content-Type recebido
- Primeiros bytes do arquivo
- Tipo detectado
- Se o processamento funcionou

## 📝 Exemplo de Uso Completo

```javascript
// Nó Code no n8n - Após receber dados do extract-for-n8n
const response = $input.first().json;

if (response.status === 'success') {
  console.log(`Arquivo processado: ${response.filename}`);
  console.log(`Tipo: ${response.file_type}`);
  console.log(`Total de abas: ${response.total_sheets}`);
  
  // Processar cada aba
  response.sheets.forEach(sheet => {
    console.log(`Aba: ${sheet.sheet_name}`);
    console.log(`Linhas: ${sheet.metadata.total_rows}`);
    console.log(`Colunas: ${sheet.metadata.columns.join(', ')}`);
    
    // Aqui você pode fazer o chunking e vetorização
    // como preferir no n8n
  });
} else {
  console.error('Erro:', response.error);
}
```

## 🚀 Próximos Passos

1. **Teste o debug** primeiro para confirmar que está detectando corretamente
2. **Use o endpoint `/extract-for-n8n`** para processar
3. **Configure seu RAG** no n8n com os dados estruturados

---

**Nota**: O problema era que o script só verificava a extensão do arquivo. Agora ele verifica o MIME type primeiro, que é mais confiável para arquivos baixados do Google Drive.
