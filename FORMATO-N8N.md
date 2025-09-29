# 📊 Formato de Saída para n8n

## 🎯 Endpoint Otimizado

Use o endpoint `/extract-for-n8n` para obter os dados no formato ideal para processamento no n8n.

```bash
curl -X POST "http://localhost:8000/extract-for-n8n" \
  -F "file=@sua-planilha.xlsx"
```

## 📦 Estrutura do Retorno

### Resposta Completa

```json
{
  "status": "success",
  "filename": "planilha-exemplo.xlsx",
  "file_type": "XLSX",
  "total_sheets": 3,
  "total_rows": 180,
  "sheets": [
    {
      "sheet_name": "Produtos",
      "metadata": {
        "total_rows": 10,
        "total_columns": 6,
        "columns": ["ID", "Nome", "Categoria", "Preço", "Estoque", "Fornecedor"],
        "source_file": "planilha-exemplo.xlsx",
        "file_type": "XLSX",
        "processed_at": "2025-09-29T10:30:00.123456"
      },
      "data": [
        {
          "ID": "001",
          "Nome": "Mouse Gamer RGB",
          "Categoria": "Informática",
          "Preço": "89.9",
          "Estoque": "45",
          "Fornecedor": "Fornecedor A"
        },
        {
          "ID": "002",
          "Nome": "Teclado Mecânico",
          "Categoria": "Informática",
          "Preço": "299.9",
          "Estoque": "23",
          "Fornecedor": "Fornecedor A"
        }
      ]
    },
    {
      "sheet_name": "Clientes",
      "metadata": {
        "total_rows": 10,
        "total_columns": 7,
        "columns": ["ID", "Nome", "Email", "Telefone", "Cidade", "Estado", "Data Cadastro"],
        "source_file": "planilha-exemplo.xlsx",
        "file_type": "XLSX",
        "processed_at": "2025-09-29T10:30:00.123456"
      },
      "data": [
        {
          "ID": "CLI001",
          "Nome": "João Silva",
          "Email": "joao.silva@example.com",
          "Telefone": "(11) 99999-9999",
          "Cidade": "São Paulo",
          "Estado": "SP",
          "Data Cadastro": "2024-10-15"
        }
      ]
    }
  ]
}
```

## 🔄 Processamento no n8n

### Workflow Simples

```json
{
  "name": "Processar Planilha no RAG",
  "nodes": [
    {
      "parameters": {
        "httpMethod": "POST",
        "path": "upload-planilha"
      },
      "name": "Webhook - Receber Planilha",
      "type": "n8n-nodes-base.webhook",
      "position": [240, 300]
    },
    {
      "parameters": {
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
      },
      "name": "Extrair Dados da Planilha",
      "type": "n8n-nodes-base.httpRequest",
      "position": [460, 300]
    },
    {
      "parameters": {
        "fieldToSplitOut": "sheets",
        "options": {}
      },
      "name": "Split - Por Aba",
      "type": "n8n-nodes-base.splitOut",
      "position": [680, 300]
    },
    {
      "parameters": {
        "fieldToSplitOut": "data",
        "options": {}
      },
      "name": "Split - Por Linha",
      "type": "n8n-nodes-base.splitOut",
      "position": [900, 300]
    },
    {
      "parameters": {
        "jsCode": "// Preparar texto para vetorização\nconst row = $input.first().json;\nconst metadata = $('Split - Por Aba').item.json.metadata;\nconst sheetName = $('Split - Por Aba').item.json.sheet_name;\n\n// Criar texto descritivo\nlet texto = `Aba: ${sheetName}\\n\\n`;\n\nfor (const [key, value] of Object.entries(row)) {\n  if (value && value.toString().trim()) {\n    texto += `${key}: ${value}\\n`;\n  }\n}\n\nreturn [{\n  json: {\n    texto: texto,\n    sheet_name: sheetName,\n    metadata: metadata,\n    raw_data: row\n  }\n}];"
      },
      "name": "Formatar para RAG",
      "type": "n8n-nodes-base.code",
      "position": [1120, 300]
    },
    {
      "parameters": {
        "mode": "insert",
        "text": "={{ $json.texto }}",
        "metadata": {
          "sheet_name": "={{ $json.sheet_name }}",
          "source_file": "={{ $json.metadata.source_file }}",
          "columns": "={{ $json.metadata.columns.join(', ') }}"
        }
      },
      "name": "Inserir no Vector Store",
      "type": "@n8n/n8n-nodes-langchain.vectorStoreSupabase",
      "position": [1340, 300]
    }
  ]
}
```

## 💡 Exemplos de Uso no n8n

### 1. Processar Cada Aba Separadamente

```javascript
// Nó Code - Após Split por Aba
const sheet = $input.first().json;

// Acessar metadados da aba
const sheetName = sheet.sheet_name;
const totalRows = sheet.metadata.total_rows;
const columns = sheet.metadata.columns;

// Processar todos os dados da aba
const allRows = sheet.data;

// Exemplo: Criar um único texto com todos os dados da aba
let textoCompleto = `# ${sheetName}\n\n`;

allRows.forEach((row, idx) => {
  textoCompleto += `## Registro ${idx + 1}\n`;
  for (const [key, value] of Object.entries(row)) {
    if (value) {
      textoCompleto += `- ${key}: ${value}\n`;
    }
  }
  textoCompleto += '\n';
});

return [{
  json: {
    sheet_name: sheetName,
    texto: textoCompleto,
    metadata: sheet.metadata
  }
}];
```

### 2. Filtrar e Processar Linhas Específicas

```javascript
// Nó Code - Filtrar dados antes de vetorizar
const sheets = $input.first().json.sheets;

const resultados = [];

sheets.forEach(sheet => {
  // Exemplo: Processar apenas a aba "Produtos"
  if (sheet.sheet_name === 'Produtos') {
    
    sheet.data.forEach(row => {
      // Filtrar apenas produtos em estoque
      if (parseInt(row.Estoque) > 0) {
        
        const texto = `
          Produto: ${row.Nome}
          Categoria: ${row.Categoria}
          Preço: R$ ${row.Preço}
          Estoque: ${row.Estoque} unidades
          Fornecedor: ${row.Fornecedor}
        `;
        
        resultados.push({
          json: {
            texto: texto.trim(),
            produto_id: row.ID,
            categoria: row.Categoria,
            sheet_name: sheet.sheet_name
          }
        });
      }
    });
  }
});

return resultados;
```

### 3. Criar Embeddings com Contexto da Aba

```javascript
// Nó Code - Adicionar contexto da aba ao texto
const sheet = $input.first().json;

const resultados = [];

sheet.data.forEach((row, idx) => {
  // Criar contexto rico
  const contexto = `
    Fonte: ${sheet.metadata.source_file}
    Aba: ${sheet.sheet_name}
    Registro ${idx + 1} de ${sheet.metadata.total_rows}
  `.trim();
  
  // Criar texto do registro
  let conteudo = '';
  for (const [key, value] of Object.entries(row)) {
    if (value && value.toString().trim()) {
      conteudo += `${key}: ${value}\n`;
    }
  }
  
  resultados.push({
    json: {
      texto: `${contexto}\n\n${conteudo}`,
      metadata: {
        sheet: sheet.sheet_name,
        row_index: idx,
        total_rows: sheet.metadata.total_rows,
        columns: sheet.metadata.columns
      }
    }
  });
});

return resultados;
```

### 4. Agrupar Dados por Categoria

```javascript
// Nó Code - Agrupar antes de vetorizar
const sheets = $input.first().json.sheets;

// Encontrar aba de produtos
const produtosSheet = sheets.find(s => s.sheet_name === 'Produtos');

if (!produtosSheet) {
  throw new Error('Aba Produtos não encontrada');
}

// Agrupar por categoria
const porCategoria = {};

produtosSheet.data.forEach(row => {
  const categoria = row.Categoria || 'Sem Categoria';
  
  if (!porCategoria[categoria]) {
    porCategoria[categoria] = [];
  }
  
  porCategoria[categoria].push(row);
});

// Criar um texto para cada categoria
const resultados = [];

for (const [categoria, produtos] of Object.entries(porCategoria)) {
  let texto = `# Categoria: ${categoria}\n\n`;
  texto += `Total de produtos: ${produtos.length}\n\n`;
  
  produtos.forEach(p => {
    texto += `## ${p.Nome}\n`;
    texto += `- Preço: R$ ${p.Preço}\n`;
    texto += `- Estoque: ${p.Estoque}\n`;
    texto += `- Fornecedor: ${p.Fornecedor}\n\n`;
  });
  
  resultados.push({
    json: {
      texto: texto,
      categoria: categoria,
      total_produtos: produtos.length,
      sheet_name: produtosSheet.sheet_name
    }
  });
}

return resultados;
```

## 🚀 Exemplo Completo de Teste

### 1. Enviar Planilha

```bash
curl -X POST "http://localhost:8000/extract-for-n8n" \
  -F "file=@planilha.xlsx" \
  | jq '.' > resultado.json
```

### 2. Ver Estrutura

```bash
# Ver total de abas
cat resultado.json | jq '.total_sheets'

# Listar nomes das abas
cat resultado.json | jq '.sheets[].sheet_name'

# Ver primeira aba completa
cat resultado.json | jq '.sheets[0]'

# Ver metadados de todas as abas
cat resultado.json | jq '.sheets[] | {name: .sheet_name, rows: .metadata.total_rows, columns: .metadata.columns}'

# Ver primeiros dados de cada aba
cat resultado.json | jq '.sheets[] | {sheet: .sheet_name, sample: .data[0]}'
```

## 📝 Vantagens desta Estrutura

✅ **Simples de processar no n8n**: Use `Split Out` para iterar sobre as abas
✅ **Metadados completos**: Cada aba tem suas informações estruturadas
✅ **Flexível**: Você decide como vetorizar (por linha, por aba, por categoria, etc)
✅ **Sem chunking prévio**: Você faz o chunking do jeito que precisar
✅ **Todos os dados disponíveis**: Nada é perdido ou resumido

## 🔧 Dicas

1. **Use Split Out** no n8n para iterar sobre `sheets` primeiro
2. **Depois Split Out novamente** sobre `data` se quiser processar linha por linha
3. **Acesse metadados** via `$('Split - Por Aba').item.json.metadata`
4. **Crie seu próprio formato de texto** para embedding
5. **Filtre dados** antes de vetorizar se necessário

## 📊 Envio Direto para n8n

Se preferir enviar diretamente:

```bash
curl -X POST "http://localhost:8000/extract-and-send-to-n8n" \
  -F "file=@planilha.xlsx" \
  -F "n8n_webhook_url=https://seu-n8n.com/webhook/processar-planilha"
```

O payload enviado será exatamente o mesmo formato do `/extract-for-n8n`.

---

**Nota**: Este formato foi otimizado para máxima flexibilidade no n8n. Você tem controle total sobre como processar e vetorizar os dados!
