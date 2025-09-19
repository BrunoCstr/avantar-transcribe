# Teste da API no Easypanel
# SUBSTITUA a URL pela sua URL real do Easypanel

$apiUrl = "https://avantar-tools-avantar-transcribe.dhyhg5.easypanel.host/"  # <- MUDE AQUI!

Write-Host "Testando Health Check..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$apiUrl/health" -Method Get
    Write-Host "API esta funcionando!" -ForegroundColor Green
    Write-Host "Status: $($health.status)"
    Write-Host "Modelos: $($health.models_loaded -join ', ')"
    Write-Host "Cache: $($health.cache_size) arquivos"
    Write-Host "Limite: $($health.max_file_size_mb)MB"
} catch {
    Write-Host "Erro no Health Check:" -ForegroundColor Red
    Write-Host $_.Exception.Message
    exit 1
}

Write-Host ""
Write-Host "Testando Transcricao..." -ForegroundColor Yellow

# Procurar por arquivos de audio na pasta atual
$audioFiles = Get-ChildItem -Path . -Include "*.ogg", "*.mp3", "*.wav", "*.m4a" -Recurse | Select-Object -First 1

if ($audioFiles) {
    $audioFile = $audioFiles[0]
    Write-Host "Usando arquivo: $($audioFile.Name)" -ForegroundColor Cyan
    
    try {
        # Criar form data para upload
        $form = @{
            file = Get-Item -Path $audioFile.FullName
        }
        
        Write-Host "Enviando para transcricao..." -ForegroundColor Yellow
        $result = Invoke-RestMethod -Uri "$apiUrl/transcribe-whatsapp" -Method Post -Form $form
        
        Write-Host "Transcricao concluida!" -ForegroundColor Green
        Write-Host "Texto: $($result.text)"
        Write-Host "Tempo: $($result.processing_time_seconds)s"
        Write-Host "Modelo: $($result.model_used)"
        
    } catch {
        Write-Host "Erro na transcricao:" -ForegroundColor Red
        Write-Host $_.Exception.Message
    }
} else {
    Write-Host "Nenhum arquivo de audio encontrado para teste" -ForegroundColor Yellow
    Write-Host "Coloque um arquivo .ogg, .mp3, .wav ou .m4a nesta pasta para testar"
}

Write-Host ""
Write-Host "Para acessar a documentacao completa:" -ForegroundColor Cyan
Write-Host "$apiUrl/docs"