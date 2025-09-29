#!/bin/bash
# Script de teste para processamento de planilhas
# Execute: ./test-spreadsheet.sh

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
GRAY='\033[0;90m'
NC='\033[0m' # No Color

# Configurações
URL="http://localhost:8000"
TEST_FILE="planilha-exemplo.xlsx"

echo -e "${CYAN}=====================================${NC}"
echo -e "${CYAN}Teste de Processamento de Planilhas${NC}"
echo -e "${CYAN}=====================================${NC}"
echo ""

# Verificar se o serviço está rodando
echo -e "${YELLOW}[1/5] Verificando serviço...${NC}"
if curl -s "${URL}/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Serviço está rodando${NC}"
    SERVICE_INFO=$(curl -s "${URL}/health")
    echo -e "${GRAY}  Service: $(echo $SERVICE_INFO | jq -r '.service')${NC}"
else
    echo -e "${RED}✗ Serviço não está rodando. Inicie o servidor primeiro.${NC}"
    echo -e "${GRAY}  Execute: uvicorn src.transcribe_spreadsheet:app --reload${NC}"
    exit 1
fi

echo ""

# Verificar arquivo de teste
if [ ! -f "$TEST_FILE" ]; then
    echo -e "${YELLOW}Arquivo de teste não encontrado. Criando...${NC}"
    python3 create-sample-spreadsheet.py
    echo ""
fi

# Teste 2: Análise da planilha
echo -e "${YELLOW}[2/5] Analisando estrutura da planilha...${NC}"
RESPONSE=$(curl -s -X POST "${URL}/analyze-spreadsheet" -F "file=@${TEST_FILE}")
STATUS=$(echo $RESPONSE | jq -r '.status')

if [ "$STATUS" = "success" ]; then
    echo -e "${GREEN}✓ Análise concluída${NC}"
    echo -e "${GRAY}  Arquivo: $(echo $RESPONSE | jq -r '.analysis.filename')${NC}"
    echo -e "${GRAY}  Tipo: $(echo $RESPONSE | jq -r '.analysis.file_type')${NC}"
    echo -e "${GRAY}  Total de abas: $(echo $RESPONSE | jq -r '.analysis.total_sheets')${NC}"
    
    # Listar abas
    echo "$RESPONSE" | jq -r '.analysis.sheets_info[] | "    - Aba \"\(.name)\": \(.total_rows) linhas, \(.total_columns) colunas"' | while read line; do
        echo -e "${GRAY}${line}${NC}"
    done
else
    echo -e "${RED}✗ Erro na análise: $(echo $RESPONSE | jq -r '.error')${NC}"
fi

echo ""

# Teste 3: Extração formato markdown
echo -e "${YELLOW}[3/5] Testando extração formato Markdown...${NC}"
RESPONSE=$(curl -s -X POST "${URL}/extract-spreadsheet" \
    -F "file=@${TEST_FILE}" \
    -F "format=markdown" \
    -F "include_metadata=true")

STATUS=$(echo $RESPONSE | jq -r '.status')

if [ "$STATUS" = "success" ]; then
    echo -e "${GREEN}✓ Extração markdown concluída${NC}"
    echo -e "${GRAY}  Total de abas: $(echo $RESPONSE | jq -r '.total_sheets')${NC}"
    echo -e "${GRAY}  Total de linhas: $(echo $RESPONSE | jq -r '.total_rows')${NC}"
    TEXT_LENGTH=$(echo $RESPONSE | jq -r '.text' | wc -c)
    echo -e "${GRAY}  Tamanho do texto: ${TEXT_LENGTH} caracteres${NC}"
    
    # Salvar resultado
    echo $RESPONSE | jq -r '.text' > output_markdown.txt
    echo -e "${GRAY}  Salvo em: output_markdown.txt${NC}"
else
    echo -e "${RED}✗ Erro na extração: $(echo $RESPONSE | jq -r '.error')${NC}"
fi

echo ""

# Teste 4: Extração formato markdown compact
echo -e "${YELLOW}[4/5] Testando extração formato Markdown Compact (RAG)...${NC}"
RESPONSE=$(curl -s -X POST "${URL}/extract-spreadsheet" \
    -F "file=@${TEST_FILE}" \
    -F "format=markdown-compact" \
    -F "include_metadata=true")

STATUS=$(echo $RESPONSE | jq -r '.status')

if [ "$STATUS" = "success" ]; then
    echo -e "${GREEN}✓ Extração markdown compact concluída${NC}"
    TEXT_LENGTH=$(echo $RESPONSE | jq -r '.text' | wc -c)
    echo -e "${GRAY}  Tamanho do texto: ${TEXT_LENGTH} caracteres${NC}"
    
    # Salvar resultado
    echo $RESPONSE | jq -r '.text' > output_markdown_compact.txt
    echo -e "${GRAY}  Salvo em: output_markdown_compact.txt${NC}"
else
    echo -e "${RED}✗ Erro na extração: $(echo $RESPONSE | jq -r '.error')${NC}"
fi

echo ""

# Teste 5: Extração formato JSON
echo -e "${YELLOW}[5/5] Testando extração formato JSON...${NC}"
RESPONSE=$(curl -s -X POST "${URL}/extract-spreadsheet" \
    -F "file=@${TEST_FILE}" \
    -F "format=json" \
    -F "include_metadata=true")

STATUS=$(echo $RESPONSE | jq -r '.status')

if [ "$STATUS" = "success" ]; then
    echo -e "${GREEN}✓ Extração JSON concluída${NC}"
    
    # Salvar resultado
    echo $RESPONSE | jq '.data' > output_json.json
    echo -e "${GRAY}  Salvo em: output_json.json${NC}"
else
    echo -e "${RED}✗ Erro na extração: $(echo $RESPONSE | jq -r '.error')${NC}"
fi

echo ""
echo -e "${CYAN}=====================================${NC}"
echo -e "${CYAN}Testes concluídos!${NC}"
echo -e "${CYAN}=====================================${NC}"
echo ""
echo -e "${YELLOW}Arquivos gerados:${NC}"
echo -e "${GRAY}  - output_markdown.txt${NC}"
echo -e "${GRAY}  - output_markdown_compact.txt${NC}"
echo -e "${GRAY}  - output_json.json${NC}"
echo ""
echo -e "${YELLOW}Para testar envio ao n8n, use:${NC}"
echo -e "${GRAY}  curl -X POST \"http://localhost:8000/extract-and-send-to-n8n\" \\${NC}"
echo -e "${GRAY}    -F \"file=@${TEST_FILE}\" \\${NC}"
echo -e "${GRAY}    -F \"n8n_webhook_url=https://seu-n8n.com/webhook/test\"${NC}"
