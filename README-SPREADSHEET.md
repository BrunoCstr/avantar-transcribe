# 📊 Avantar Transcribe - Processador de Planilhas para RAG

## 🎯 Visão Geral

Serviço especializado para processar planilhas com múltiplas abas e preparar os dados para inserção em sistemas RAG (Retrieval-Augmented Generation). Integra perfeitamente com n8n e suporta diversos formatos de saída.

## ✨ Funcionalidades

- ✅ **Múltiplos Formatos**: XLSX, XLS, CSV
- ✅ **Múltiplas Abas**: Processa todas as abas automaticamente
- ✅ **Formatos de Saída**: Markdown, Markdown Compact, JSON
- ✅ **Integração Direta com n8n**: Endpoint dedicado
- ✅ **Análise Prévia**: Visualize a estrutura antes de processar
- ✅ **Otimizado para RAG**: Formatação ideal para embeddings

## 🚀 Início Rápido

### Instalação Local

```bash
# Instalar dependências
pip install -r requirements_spreadsheet.txt

# Iniciar servidor
uvicorn src.transcribe_spreadsheet:app --reload --port 8000
```

### Docker

```bash
# Build
docker build -f Dockerfile.spreadsheet -t avantar-spreadsheet .

# Run
docker run -p 8000:8000 avantar-spreadsheet
```

### Docker Compose

```yaml
# Adicionar ao seu docker-compose.yml
spreadsheet-processor:
  build:
    context: .
    dockerfile: Dockerfile.spreadsheet
  ports:
    - "8003:8000"
  restart: unless-stopped
```

## 📚 Uso Básico

### 1. Analisar Estrutura da Planilha

```bash
curl -X POST "http://localhost:8000/analyze-spreadsheet" \
  -F "file=@minha-planilha.xlsx"
```

**Resposta:**
```json
{
  "status": "success",
  "analysis": {
    "filename": "minha-planilha.xlsx",
    "file_type": "XLSX",
    "total_sheets": 3,
    "sheets_info": [
      {
        "name": "Clientes",
        "total_rows": 150,
        "total_columns": 5,
        "columns": ["Nome", "Email", "Telefone", "Cidade", "Estado"],
        "sample_rows": [...]
      }
    ]
  }
}
```

### 2. Extrair Dados (Formato Markdown Compact - Recomendado para RAG)

```bash
curl -X POST "http://localhost:8000/extract-spreadsheet" \
  -F "file=@minha-planilha.xlsx" \
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
  "total_rows": 450
}
```

### 3. Enviar Diretamente para n8n

```bash
curl -X POST "http://localhost:8000/extract-and-send-to-n8n" \
  -F "file=@minha-planilha.xlsx" \
  -F "n8n_webhook_url=https://seu-n8n.com/webhook/planilha-rag" \
  -F "format=markdown-compact"
```

## 🎨 Formatos de Saída

### Markdown (Detalhado)
Ideal para: Documentação, visualização humana

```markdown
# DADOS DA PLANILHA

## ABA: Produtos
Total de registros: 50

### Registro 1
- **Nome**: Produto A
- **Preço**: 99.90
- **Categoria**: Eletrônicos
```

### Markdown Compact (Recomendado para RAG) ⭐
Ideal para: RAG, economia de tokens, tabelas

```markdown
# DADOS DA PLANILHA

## Produtos
*50 registros*

| Nome | Preço | Categoria |
|---|---|---|
| Produto A | 99.90 | Eletrônicos |
| Produto B | 149.90 | Informática |
```

### JSON
Ideal para: Integração programática, APIs

```json
{
  "processed_at": "2025-09-29T10:30:00",
  "total_sheets": 2,
  "sheets": {
    "Produtos": {
      "headers": ["Nome", "Preço", "Categoria"],
      "rows": [...],
      "total_rows": 50
    }
  }
}
```

## 🔌 Integração com n8n

### Workflow Básico

1. **Criar Webhook no n8n**
   - Tipo: POST
   - Path: `planilha-rag`

2. **Adicionar Nó HTTP Request**
   - URL: `https://seu-servico.com/extract-and-send-to-n8n`
   - Method: POST
   - Body: multipart-form-data
   - Parâmetros:
     - `file`: arquivo da planilha
     - `n8n_webhook_url`: URL do webhook RAG
     - `format`: `markdown-compact`

3. **Processar no Vector Store**
   - Dividir texto em chunks
   - Gerar embeddings
   - Inserir no Supabase/Pinecone

### Exemplo Completo

Veja o arquivo `n8n-spreadsheet-guide.md` para workflows completos e casos de uso avançados.

## 📊 Exemplos de Uso

### Caso 1: Base de Conhecimento de Produtos

```python
import requests

# Enviar planilha de produtos
with open('produtos.xlsx', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/extract-spreadsheet',
        files={'file': f},
        data={
            'format': 'markdown-compact',
            'include_metadata': True
        }
    )

data = response.json()
print(f"Processados {data['total_rows']} produtos de {data['total_sheets']} categorias")
print(f"Texto pronto para RAG: {len(data['text'])} caracteres")
```

### Caso 2: FAQ Automático

```python
# Processar planilha de FAQ e enviar para RAG
response = requests.post(
    'http://localhost:8000/extract-and-send-to-n8n',
    files={'file': open('faq.xlsx', 'rb')},
    data={
        'n8n_webhook_url': 'https://seu-n8n.com/webhook/faq-rag',
        'format': 'markdown-compact'
    }
)

print(response.json())
```

### Caso 3: Catálogo de Serviços

```python
# Analisar antes de processar
response = requests.post(
    'http://localhost:8000/analyze-spreadsheet',
    files={'file': open('servicos.xlsx', 'rb')}
)

analysis = response.json()['analysis']

# Verificar se tem dados suficientes
if analysis['total_sheets'] > 0:
    # Processar
    response = requests.post(
        'http://localhost:8000/extract-spreadsheet',
        files={'file': open('servicos.xlsx', 'rb')},
        data={'format': 'json'}
    )
    
    data = response.json()['data']
    # Processar dados...
```

## 🎯 Boas Práticas para RAG

### 1. Use Markdown Compact
- Economia de até 60% em tokens
- Melhor para tabelas
- Mantém estrutura visual

### 2. Divida em Chunks
```python
def chunk_text(text, chunk_size=2000):
    """Divide texto em chunks para RAG"""
    chunks = []
    lines = text.split('\n')
    current_chunk = []
    current_size = 0
    
    for line in lines:
        line_size = len(line)
        if current_size + line_size > chunk_size and current_chunk:
            chunks.append('\n'.join(current_chunk))
            current_chunk = [line]
            current_size = line_size
        else:
            current_chunk.append(line)
            current_size += line_size
    
    if current_chunk:
        chunks.append('\n'.join(current_chunk))
    
    return chunks
```

### 3. Adicione Metadados
```python
# Enriquecer cada chunk com metadados
for i, chunk in enumerate(chunks):
    metadata = {
        'source': 'planilha',
        'filename': 'produtos.xlsx',
        'chunk_index': i,
        'total_chunks': len(chunks),
        'processed_at': datetime.now().isoformat()
    }
    # Inserir no vector store com metadados
```

### 4. Normalize Dados
```python
# Antes de processar, normalize
df = pd.read_excel('dados.xlsx')

# Remover espaços extras
df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

# Preencher valores vazios
df = df.fillna('')

# Salvar normalizado
df.to_excel('dados_normalizados.xlsx', index=False)
```

## 🔧 Configuração Avançada

### Variáveis de Ambiente

```bash
# .env
PORT=8000
MAX_FILE_SIZE_MB=50
LOG_LEVEL=INFO
```

### Customização de Formato

Você pode modificar as funções `format_for_rag` e `format_for_rag_compact` em `src/transcribe_spreadsheet.py` para adaptar o formato de saída às suas necessidades específicas.

## 📈 Performance

### Tempos Típicos

| Tamanho | Abas | Linhas | Tempo |
|---------|------|--------|-------|
| 1 MB    | 1    | 100    | 1-2s  |
| 5 MB    | 3    | 1,000  | 3-5s  |
| 10 MB   | 5    | 5,000  | 5-10s |
| 20 MB   | 10   | 10,000 | 10-20s|

### Otimizações

- Processamento em memória (sem arquivos temporários)
- Leitura lazy de planilhas grandes
- Suporte a streaming para arquivos muito grandes

## 🐛 Troubleshooting

### Erro: "Arquivo muito grande"
**Solução**: Reduza o tamanho da planilha ou aumente `MAX_FILE_SIZE_MB`

### Erro: "Formato não suportado"
**Solução**: Converta para XLSX antes de enviar

### Erro: "Erro ao ler planilha"
**Solução**: Verifique se o arquivo não está corrompido e tem abas válidas

### Timeout ao processar
**Solução**: Para planilhas muito grandes, processe por aba individualmente

## 📝 Teste

### Teste Rápido

```bash
# Windows
.\test-spreadsheet.ps1

# Linux/Mac
./test-spreadsheet.sh
```

### Teste Manual

```bash
# 1. Health check
curl http://localhost:8000/health

# 2. Analisar planilha
curl -X POST http://localhost:8000/analyze-spreadsheet \
  -F "file=@teste.xlsx"

# 3. Extrair dados
curl -X POST http://localhost:8000/extract-spreadsheet \
  -F "file=@teste.xlsx" \
  -F "format=markdown-compact"
```

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:
1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT.

## 🆘 Suporte

- 📖 Documentação completa: `n8n-spreadsheet-guide.md`
- 🐛 Issues: GitHub Issues
- 💬 Discussões: GitHub Discussions

---

**Versão**: 1.0.0  
**Última atualização**: Setembro 2025  
**Autor**: Avantar Team
