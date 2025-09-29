# Script de teste para processamento de planilhas
# Execute: .\test-spreadsheet.ps1

$ErrorActionPreference = "Continue"

# Configurações
$url = "http://localhost:8000"
$testFile = "D:\teste-planilha.xlsx"

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Teste de Processamento de Planilhas" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Verificar se o serviço está rodando
Write-Host "[1/5] Verificando serviço..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$url/health" -Method Get
    Write-Host "✓ Serviço está rodando" -ForegroundColor Green
    Write-Host "  Service: $($health.service)" -ForegroundColor Gray
} catch {
    Write-Host "✗ Serviço não está rodando. Inicie o servidor primeiro." -ForegroundColor Red
    Write-Host "  Execute: uvicorn src.transcribe_spreadsheet:app --reload" -ForegroundColor Gray
    exit 1
}

Write-Host ""

# Criar arquivo de teste se não existir
if (-not (Test-Path $testFile)) {
    Write-Host "Arquivo de teste não encontrado. Especifique o caminho do arquivo:" -ForegroundColor Yellow
    $testFile = Read-Host "Caminho completo do arquivo .xlsx"
    
    if (-not (Test-Path $testFile)) {
        Write-Host "✗ Arquivo não encontrado: $testFile" -ForegroundColor Red
        exit 1
    }
}

Write-Host "[2/5] Analisando estrutura da planilha..." -ForegroundColor Yellow
try {
    $formData = @{
        file = Get-Item -Path $testFile
    }
    
    $analysis = Invoke-RestMethod -Uri "$url/analyze-spreadsheet" -Method Post -Form $formData
    
    if ($analysis.status -eq "success") {
        Write-Host "✓ Análise concluída" -ForegroundColor Green
        Write-Host "  Arquivo: $($analysis.analysis.filename)" -ForegroundColor Gray
        Write-Host "  Tipo: $($analysis.analysis.file_type)" -ForegroundColor Gray
        Write-Host "  Total de abas: $($analysis.analysis.total_sheets)" -ForegroundColor Gray
        
        foreach ($sheet in $analysis.analysis.sheets_info) {
            Write-Host "    - Aba '$($sheet.name)': $($sheet.total_rows) linhas, $($sheet.total_columns) colunas" -ForegroundColor Gray
        }
    } else {
        Write-Host "✗ Erro na análise: $($analysis.error)" -ForegroundColor Red
    }
} catch {
    Write-Host "✗ Erro ao analisar: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Teste 3: Extração formato markdown
Write-Host "[3/5] Testando extração formato Markdown..." -ForegroundColor Yellow
try {
    $formData = @{
        file = Get-Item -Path $testFile
        format = "markdown"
        include_metadata = "true"
    }
    
    $extract = Invoke-RestMethod -Uri "$url/extract-spreadsheet" -Method Post -Form $formData
    
    if ($extract.status -eq "success") {
        Write-Host "✓ Extração markdown concluída" -ForegroundColor Green
        Write-Host "  Total de abas: $($extract.total_sheets)" -ForegroundColor Gray
        Write-Host "  Total de linhas: $($extract.total_rows)" -ForegroundColor Gray
        Write-Host "  Tamanho do texto: $($extract.text.Length) caracteres" -ForegroundColor Gray
        
        # Salvar resultado
        $outputFile = "output_markdown.txt"
        $extract.text | Out-File -FilePath $outputFile -Encoding UTF8
        Write-Host "  Salvo em: $outputFile" -ForegroundColor Gray
    } else {
        Write-Host "✗ Erro na extração: $($extract.error)" -ForegroundColor Red
    }
} catch {
    Write-Host "✗ Erro ao extrair: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Teste 4: Extração formato markdown compact
Write-Host "[4/5] Testando extração formato Markdown Compact (RAG)..." -ForegroundColor Yellow
try {
    $formData = @{
        file = Get-Item -Path $testFile
        format = "markdown-compact"
        include_metadata = "true"
    }
    
    $extract = Invoke-RestMethod -Uri "$url/extract-spreadsheet" -Method Post -Form $formData
    
    if ($extract.status -eq "success") {
        Write-Host "✓ Extração markdown compact concluída" -ForegroundColor Green
        Write-Host "  Tamanho do texto: $($extract.text.Length) caracteres" -ForegroundColor Gray
        
        # Salvar resultado
        $outputFile = "output_markdown_compact.txt"
        $extract.text | Out-File -FilePath $outputFile -Encoding UTF8
        Write-Host "  Salvo em: $outputFile" -ForegroundColor Gray
    } else {
        Write-Host "✗ Erro na extração: $($extract.error)" -ForegroundColor Red
    }
} catch {
    Write-Host "✗ Erro ao extrair: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Teste 5: Extração formato otimizado para n8n
Write-Host "[5/5] Testando extração otimizada para n8n..." -ForegroundColor Yellow
try {
    $formData = @{
        file = Get-Item -Path $testFile
    }
    
    $extract = Invoke-RestMethod -Uri "$url/extract-for-n8n" -Method Post -Form $formData
    
    if ($extract.status -eq "success") {
        Write-Host "✓ Extração para n8n concluída" -ForegroundColor Green
        Write-Host "  Total de abas: $($extract.total_sheets)" -ForegroundColor Gray
        Write-Host "  Total de linhas: $($extract.total_rows)" -ForegroundColor Gray
        
        # Mostrar estrutura de cada aba
        foreach ($sheet in $extract.sheets) {
            Write-Host "  - Aba '$($sheet.sheet_name)': $($sheet.metadata.total_rows) linhas, $($sheet.metadata.total_columns) colunas" -ForegroundColor Gray
        }
        
        # Salvar resultado
        $outputFile = "output_n8n.json"
        $extract | ConvertTo-Json -Depth 10 | Out-File -FilePath $outputFile -Encoding UTF8
        Write-Host "  Salvo em: $outputFile" -ForegroundColor Gray
    } else {
        Write-Host "✗ Erro na extração: $($extract.error)" -ForegroundColor Red
    }
} catch {
    Write-Host "✗ Erro ao extrair: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Testes concluídos!" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Arquivos gerados:" -ForegroundColor Yellow
Write-Host "  - output_markdown.txt" -ForegroundColor Gray
Write-Host "  - output_markdown_compact.txt" -ForegroundColor Gray
Write-Host "  - output_n8n.json (FORMATO RECOMENDADO PARA N8N)" -ForegroundColor Cyan
Write-Host ""
Write-Host "Para processar no n8n, use o endpoint:" -ForegroundColor Yellow
Write-Host '  POST /extract-for-n8n' -ForegroundColor Cyan
Write-Host ""
Write-Host "Exemplo:" -ForegroundColor Yellow
Write-Host '  curl -X POST "http://localhost:8000/extract-for-n8n" -F "file=@sua-planilha.xlsx"' -ForegroundColor Gray
Write-Host ""
Write-Host "Ou envie direto para o n8n:" -ForegroundColor Yellow
Write-Host '  curl -X POST "http://localhost:8000/extract-and-send-to-n8n" \' -ForegroundColor Gray
Write-Host '    -F "file=@sua-planilha.xlsx" \' -ForegroundColor Gray
Write-Host '    -F "n8n_webhook_url=https://seu-n8n.com/webhook/planilha"' -ForegroundColor Gray
Write-Host ""
Write-Host "Veja FORMATO-N8N.md para exemplos de processamento no n8n!" -ForegroundColor Cyan
