#!/usr/bin/env python3
"""
Script de teste para a API de transcrição de PDF e vídeo
"""

import requests
import json
import os

# Configuração
BASE_URL = "http://localhost:8080"

def test_health():
    """Testa o endpoint de saúde"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print("🏥 Teste de Health:")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Erro no teste de health: {e}")
        return False

def test_transcribe_auto():
    """Testa o endpoint de transcrição automática"""
    try:
        # Criar um arquivo de teste simples (simulando upload)
        test_file = "teste.txt"
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("Este é um arquivo de teste para verificar se a API está funcionando.")
        
        with open(test_file, "rb") as f:
            files = {"file": ("teste.txt", f, "text/plain")}
            response = requests.post(f"{BASE_URL}/transcribe-auto", files=files)
        
        # Limpar arquivo de teste
        os.remove(test_file)
        
        print("\n🎯 Teste de Transcribe Auto:")
        print(f"Status: {response.status_code}")
        if response.status_code == 400:
            print("✅ Resposta esperada - arquivo não suportado")
            return True
        else:
            print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste de transcribe-auto: {e}")
        return False

def test_endpoints():
    """Testa se todos os endpoints estão disponíveis"""
    endpoints = [
        "/health",
        "/test", 
        "/extract",
        "/extract-structured",
        "/transcribe-video",
        "/transcribe-audio",
        "/transcribe-auto"
    ]
    
    print("\n📋 Endpoints disponíveis:")
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}")
            status = "✅" if response.status_code in [200, 405] else "❌"
            print(f"{status} {endpoint} - Status: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint} - Erro: {e}")

def main():
    """Função principal de teste"""
    print("🚀 Iniciando testes da API PDF and Video Transcription...")
    print(f"🌐 URL base: {BASE_URL}")
    
    # Teste de conectividade
    if not test_health():
        print("\n❌ API não está respondendo. Verifique se o servidor está rodando.")
        return
    
    # Teste de endpoints
    test_endpoints()
    
    # Teste de funcionalidade
    test_transcribe_auto()
    
    print("\n✅ Testes concluídos!")
    print("\n📝 Para testar com arquivos reais:")
    print("   - PDFs: POST /extract")
    print("   - Imagens: POST /extract") 
    print("   - Vídeos: POST /transcribe-video")
    print("   - Áudios: POST /transcribe-audio")
    print("   - Auto-detecção: POST /transcribe-auto")

if __name__ == "__main__":
    main()
