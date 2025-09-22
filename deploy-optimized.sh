#!/bin/bash

# Script de deploy otimizado para VPS
echo "🚀 Deploy do Avantar Transcribe - Versão Otimizada"

# Verificar recursos do sistema
echo "📊 Verificando recursos do sistema..."
echo "CPU cores: $(nproc)"
echo "Memória total: $(free -h | grep '^Mem:' | awk '{print $2}')"
echo "Memória disponível: $(free -h | grep '^Mem:' | awk '{print $7}')"
echo "Espaço em disco: $(df -h / | tail -1 | awk '{print $4}')"

# Parar containers existentes
echo "🛑 Parando containers existentes..."
docker-compose -f docker-compose-optimized.yml down

# Limpar cache e imagens antigas
echo "🧹 Limpando cache..."
docker system prune -f
docker image prune -f

# Construir nova imagem otimizada
echo "🔨 Construindo imagem otimizada..."
docker-compose -f docker-compose-optimized.yml build --no-cache

# Iniciar serviço
echo "▶️  Iniciando serviço otimizado..."
docker-compose -f docker-compose-optimized.yml up -d

# Aguardar inicialização
echo "⏳ Aguardando inicialização..."
sleep 30

# Verificar status
echo "🔍 Verificando status..."
docker-compose -f docker-compose-optimized.yml ps

# Testar endpoint
echo "🧪 Testando endpoint..."
curl -f http://localhost:8000/health || echo "❌ Serviço não está respondendo"

echo "✅ Deploy concluído!"
echo "🌐 API disponível em: http://localhost:8000"
echo "📊 Monitoramento: http://localhost:8000/health"
