# Script de teste para Windows PowerShell
# Para testar a Universal Transcription API no Easypanel

param(
    [Parameter(Mandatory=$true)]
    [string]$ApiUrl,
    
    [Parameter(Mandatory=$false)]
    [string]$AudioFile = "audios\WhatsApp-Ptt-2025-09-19-at-12.25.16.ogg",
    
    [Parameter(Mandatory=$false)]
    [string]$ImageFile = "images\test-image.jpg",
    
    [Parameter(Mandatory=$false)]
    [string]$PdfFile = "documents\test-document.pdf",
    
    [Parameter(Mandatory=$false)]
    [string]$WordFile = "documents\test-document.docx"
)

Write-Host "🚀 Testando Universal Transcription API no Easypanel" -ForegroundColor Green
Write-Host "URL: $ApiUrl" -ForegroundColor Cyan

# Função para testar endpoint
function Test-Endpoint {
    param($Url, $Name)
    
    try {
        Write-Host "🔍 Testando $Name..." -ForegroundColor Yellow
        $response = Invoke-RestMethod -Uri $Url -Method Get -TimeoutSec 30
        Write-Host "✅ $Name: OK" -ForegroundColor Green
        return $response
    }
    catch {
        Write-Host "❌ $Name: ERRO - $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

# Função para testar transcrição
function Test-Transcription {
    param($Url, $FilePath, $Name)
    
    if (-not (Test-Path $FilePath)) {
        Write-Host "⚠️  Arquivo não encontrado: $FilePath" -ForegroundColor Yellow
        return
    }
    
    try {
        Write-Host "🎵 Testando $Name..." -ForegroundColor Yellow
        
        $form = @{
            file = Get-Item -Path $FilePath
        }
        
        $startTime = Get-Date
        $response = Invoke-RestMethod -Uri $Url -Method Post -Form $form -TimeoutSec 120
        $endTime = Get-Date
        $duration = ($endTime - $startTime).TotalSeconds
        
        Write-Host "✅ $Name: Sucesso!" -ForegroundColor Green
        Write-Host "   Texto: $($response.text.Substring(0, [Math]::Min(100, $response.text.Length)))..." -ForegroundColor White
        Write-Host "   Modelo: $($response.model_used)" -ForegroundColor White
        Write-Host "   Tempo: $([Math]::Round($duration, 2))s" -ForegroundColor White
        Write-Host "   Cache: $($response.cached)" -ForegroundColor White
        
        return $response
    }
    catch {
        Write-Host "❌ $Name: ERRO - $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

# 1. Testar Health Check
Write-Host "`n=== HEALTH CHECK ===" -ForegroundColor Magenta
$health = Test-Endpoint "$ApiUrl/health" "Health Check"

if ($health) {
    Write-Host "📊 Status: $($health.status)" -ForegroundColor Cyan
    Write-Host "📊 Whisper disponível: $($health.services.whisper.available)" -ForegroundColor Cyan
    Write-Host "📊 Modelos Whisper: $($health.services.whisper.models -join ', ')" -ForegroundColor Cyan
    Write-Host "📊 EasyOCR: $($health.services.ocr.easyocr)" -ForegroundColor Cyan
    Write-Host "📊 Tesseract: $($health.services.ocr.tesseract)" -ForegroundColor Cyan
    Write-Host "📊 Processamento de documentos: $($health.services.document_processing)" -ForegroundColor Cyan
    Write-Host "📊 Tamanho máximo: $($health.max_file_size_mb)MB" -ForegroundColor Cyan
    Write-Host "📊 Cache: $($health.cache_size) itens" -ForegroundColor Cyan
}

# 2. Testar endpoint básico
Write-Host "`n=== ENDPOINT BÁSICO ===" -ForegroundColor Magenta
Test-Endpoint "$ApiUrl/" "Root Endpoint"

# 3. Testar transcrições (se arquivo existir)
Write-Host "`n=== TRANSCRIÇÕES ===" -ForegroundColor Magenta

if (Test-Path $AudioFile) {
    # Testar WhatsApp
    Test-Transcription "$ApiUrl/transcribe-whatsapp" $AudioFile "WhatsApp Transcription"
    
    # Testar simples
    Test-Transcription "$ApiUrl/transcribe-simple" $AudioFile "Simple Transcription"
    
    # Testar completo
    Test-Transcription "$ApiUrl/transcribe" $AudioFile "Full Transcription"
} else {
    Write-Host "⚠️  Nenhum arquivo de áudio encontrado para teste" -ForegroundColor Yellow
    Write-Host "   Coloque um arquivo em: $AudioFile" -ForegroundColor Yellow
}

# 4. Testar OCR de imagens
Write-Host "`n=== OCR DE IMAGENS ===" -ForegroundColor Magenta

if (Test-Path $ImageFile) {
    Test-Transcription "$ApiUrl/ocr/image" $ImageFile "OCR EasyOCR"
    Test-Transcription "$ApiUrl/ocr/image?method=tesseract" $ImageFile "OCR Tesseract"
} else {
    Write-Host "⚠️  Nenhuma imagem encontrada para teste" -ForegroundColor Yellow
    Write-Host "   Coloque uma imagem em: $ImageFile" -ForegroundColor Yellow
}

# 5. Testar extração de PDF
Write-Host "`n=== EXTRAÇÃO DE PDF ===" -ForegroundColor Magenta

if (Test-Path $PdfFile) {
    Test-Transcription "$ApiUrl/extract/pdf" $PdfFile "PDF Auto"
    Test-Transcription "$ApiUrl/extract/pdf?method=direct" $PdfFile "PDF Direto"
} else {
    Write-Host "⚠️  Nenhum PDF encontrado para teste" -ForegroundColor Yellow
    Write-Host "   Coloque um PDF em: $PdfFile" -ForegroundColor Yellow
}

# 6. Testar documentos Office
Write-Host "`n=== DOCUMENTOS OFFICE ===" -ForegroundColor Magenta

if (Test-Path $WordFile) {
    Test-Transcription "$ApiUrl/extract/document" $WordFile "Documento Word"
} else {
    Write-Host "⚠️  Nenhum documento encontrado para teste" -ForegroundColor Yellow
    Write-Host "   Coloque um .docx em: $WordFile" -ForegroundColor Yellow
}

# 7. Testar detecção automática
Write-Host "`n=== DETECÇÃO AUTOMÁTICA ===" -ForegroundColor Magenta

if (Test-Path $AudioFile) {
    Test-Transcription "$ApiUrl/extract/auto" $AudioFile "Auto-detecção (Áudio)"
}

if (Test-Path $ImageFile) {
    Test-Transcription "$ApiUrl/extract/auto" $ImageFile "Auto-detecção (Imagem)"
}

# 8. Testar cache stats
Write-Host "`n=== CACHE STATS ===" -ForegroundColor Magenta
$cacheStats = Test-Endpoint "$ApiUrl/cache/stats" "Cache Stats"

if ($cacheStats) {
    Write-Host "📊 Itens no cache: $($cacheStats.cache_size)" -ForegroundColor Cyan
    Write-Host "📊 Memória usada: $([Math]::Round($cacheStats.memory_usage_mb, 2))MB" -ForegroundColor Cyan
}

Write-Host "`n🎉 Testes concluídos!" -ForegroundColor Green
Write-Host "📖 Endpoints disponíveis:" -ForegroundColor Cyan
Write-Host "   🎵 Áudio: $ApiUrl/transcribe-whatsapp" -ForegroundColor White
Write-Host "   🎥 Vídeo: $ApiUrl/transcribe-video" -ForegroundColor White
Write-Host "   🖼️  Imagem: $ApiUrl/ocr/image" -ForegroundColor White
Write-Host "   📄 PDF: $ApiUrl/extract/pdf" -ForegroundColor White
Write-Host "   📝 Documento: $ApiUrl/extract/document" -ForegroundColor White
Write-Host "   🤖 Auto: $ApiUrl/extract/auto" -ForegroundColor White
