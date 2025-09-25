from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import whisper
import tempfile
import os
import uvicorn
from typing import Optional, List
import logging
import asyncio
import aiofiles
from pathlib import Path
import subprocess
import shutil
from datetime import datetime
import hashlib
import json
import gc
import psutil
import threading
from concurrent.futures import ThreadPoolExecutor
import time

# OCR e processamento de documentos (opcional)
try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Avantar Transcribe API - Otimizada",
    description="API otimizada para VPS com recursos limitados",
    version="2.0.0-optimized"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurações otimizadas para VPS
CACHE_DIR = Path("./cache")
CACHE_DIR.mkdir(exist_ok=True)

MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB (reduzido)
CHUNK_SIZE = 512 * 1024  # 512KB chunks
MAX_CONCURRENT_REQUESTS = 2  # Limitar concorrência
MAX_CACHE_SIZE = 50  # Máximo 50 itens no cache

# Cache de resultados com limpeza automática
transcription_cache = {}
cache_access_times = {}

# Pool de threads para processamento
executor = ThreadPoolExecutor(max_workers=2)

# Modelo Whisper único (carregado sob demanda)
whisper_model = None
model_lock = threading.Lock()

def get_system_resources():
    """Monitora recursos do sistema"""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    return {
        "cpu_percent": cpu_percent,
        "memory_percent": memory.percent,
        "memory_available_mb": memory.available // (1024 * 1024),
        "memory_used_mb": memory.used // (1024 * 1024)
    }

def cleanup_cache():
    """Limpa cache baseado em LRU e tamanho"""
    global transcription_cache, cache_access_times
    
    if len(transcription_cache) <= MAX_CACHE_SIZE:
        return
    
    # Ordenar por tempo de acesso
    sorted_items = sorted(cache_access_times.items(), key=lambda x: x[1])
    
    # Remover itens mais antigos
    items_to_remove = len(transcription_cache) - MAX_CACHE_SIZE + 5
    for cache_key, _ in sorted_items[:items_to_remove]:
        if cache_key in transcription_cache:
            del transcription_cache[cache_key]
        if cache_key in cache_access_times:
            del cache_access_times[cache_key]
    
    # Forçar garbage collection
    gc.collect()
    logger.info(f"Cache limpo. Itens restantes: {len(transcription_cache)}")

def load_whisper_model(model_name: str = "tiny"):
    """Carrega modelo Whisper sob demanda"""
    global whisper_model
    
    with model_lock:
        if whisper_model is None:
            logger.info(f"Carregando modelo Whisper: {model_name}")
            try:
                whisper_model = whisper.load_model(model_name)
                logger.info("Modelo carregado com sucesso!")
            except Exception as e:
                logger.error(f"Erro ao carregar modelo: {e}")
                raise HTTPException(status_code=500, detail="Erro ao carregar modelo Whisper")
        
        return whisper_model

def get_file_hash(content: bytes) -> str:
    """Gera hash do arquivo para cache"""
    return hashlib.md5(content).hexdigest()

def choose_optimal_model(file_size: int) -> str:
    """Escolhe modelo baseado no tamanho e recursos disponíveis"""
    resources = get_system_resources()
    
    # Se memória baixa, usar tiny sempre
    if resources["memory_available_mb"] < 2000:
        return "tiny"
    
    # Se arquivo pequeno, usar tiny
    if file_size < 5 * 1024 * 1024:  # < 5MB
        return "tiny"
    
    # Se CPU baixo, usar tiny
    if resources["cpu_percent"] > 80:
        return "tiny"
    
    # Caso contrário, usar base
    return "base"

async def convert_video_to_audio(video_path: str) -> str:
    """Converte vídeo para áudio usando ffmpeg otimizado"""
    audio_path = video_path.rsplit('.', 1)[0] + '_audio.wav'
    
    # Comando otimizado para VPS
    cmd = [
        'ffmpeg', '-i', video_path,
        '-vn',  # Sem vídeo
        '-acodec', 'pcm_s16le',
        '-ar', '16000',  # Sample rate otimizado
        '-ac', '1',  # Mono
        '-threads', '1',  # Limitar threads
        '-y',
        audio_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=300)
        return audio_path
    except subprocess.TimeoutExpired:
        logger.error("Timeout na conversão de vídeo")
        raise HTTPException(status_code=408, detail="Timeout na conversão")
    except subprocess.CalledProcessError as e:
        logger.error(f"Erro na conversão: {e.stderr}")
        raise HTTPException(status_code=500, detail="Erro na conversão do vídeo")

def preprocess_audio(audio_path: str) -> str:
    """Otimiza áudio para transcrição"""
    output_path = audio_path.rsplit('.', 1)[0] + '_processed.wav'
    
    cmd = [
        'ffmpeg', '-i', audio_path,
        '-ar', '16000',
        '-ac', '1',
        '-filter:a', 'volume=1.5,highpass=f=200,lowpass=f=3000',
        '-threads', '1',
        '-y',
        output_path
    ]
    
    try:
        subprocess.run(cmd, capture_output=True, check=True, timeout=120)
        return output_path
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        logger.warning("Falha no pré-processamento, usando arquivo original")
        return audio_path

def extract_text_from_image_simple(image_path: str) -> dict:
    """OCR simples usando apenas Tesseract (se disponível)"""
    if not OCR_AVAILABLE:
        return {
            "text": "OCR não disponível nesta versão otimizada",
            "method": "Not available",
            "confidence": 0
        }
    
    try:
        image = Image.open(image_path)
        # Redimensionar se muito grande
        if image.size[0] > 2000 or image.size[1] > 2000:
            image.thumbnail((2000, 2000), Image.Resampling.LANCZOS)
        
        text = pytesseract.image_to_string(image, lang='por+eng')
        
        return {
            "text": text.strip(),
            "method": "Tesseract (optimized)",
            "confidence": 0.8
        }
    except Exception as e:
        logger.error(f"Erro no OCR: {e}")
        return {
            "text": f"Erro no OCR: {str(e)}",
            "method": "Error",
            "confidence": 0
        }

# Middleware para limitar concorrência
@app.middleware("http")
async def limit_concurrency(request, call_next):
    # Verificar recursos do sistema
    resources = get_system_resources()
    
    if resources["cpu_percent"] > 90 or resources["memory_percent"] > 90:
        return JSONResponse(
            status_code=503,
            content={"error": "Servidor sobrecarregado. Tente novamente em alguns segundos."}
        )
    
    response = await call_next(request)
    return response

@app.get("/")
async def root():
    return {"message": "Avantar Transcribe API - Versão Otimizada"}

@app.get("/health")
async def health_check():
    resources = get_system_resources()
    
    return {
        "status": "healthy" if resources["cpu_percent"] < 90 and resources["memory_percent"] < 90 else "overloaded",
        "resources": resources,
        "cache_size": len(transcription_cache),
        "max_file_size_mb": MAX_FILE_SIZE // (1024 * 1024),
        "ocr_available": OCR_AVAILABLE,
        "max_concurrent_requests": MAX_CONCURRENT_REQUESTS
    }

@app.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: Optional[str] = "pt",
    use_cache: bool = True
):
    """
    Transcreve arquivo de áudio/vídeo - Versão Otimizada
    """
    
    # Verificar tamanho do arquivo
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Arquivo muito grande. Máximo: {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    # Verificar cache
    file_hash = get_file_hash(content)
    cache_key = f"{file_hash}_{language}"
    
    if use_cache and cache_key in transcription_cache:
        cache_access_times[cache_key] = time.time()
        logger.info(f"Resultado encontrado no cache para {file.filename}")
        return transcription_cache[cache_key]
    
    # Verificar tipo de arquivo
    allowed_types = {
        'audio/mpeg', 'audio/wav', 'audio/mp4', 'audio/m4a', 
        'audio/ogg', 'audio/webm', 'audio/flac',
        'video/mp4', 'video/avi', 'video/mov', 'video/mkv'
    }
    
    if file.content_type not in allowed_types:
        ext = file.filename.split('.')[-1].lower() if file.filename else ""
        if ext not in ['mp3', 'wav', 'm4a', 'ogg', 'webm', 'flac', 'mp4', 'avi', 'mov', 'mkv']:
            raise HTTPException(
                status_code=400, 
                detail=f"Tipo de arquivo não suportado: {file.content_type}"
            )
    
    temp_files = []
    try:
        # Criar arquivo temporário
        suffix = f".{file.filename.split('.')[-1]}" if file.filename else ".tmp"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
            temp_files.append(temp_file_path)
        
        logger.info(f"Processando: {file.filename} ({len(content)} bytes)")
        
        # Processar vídeo se necessário
        is_video = any(ext in file.content_type for ext in ['video/', '.mp4', '.avi', '.mov', '.mkv'])
        if is_video:
            logger.info("Convertendo vídeo para áudio...")
            audio_path = await convert_video_to_audio(temp_file_path)
            temp_files.append(audio_path)
            temp_file_path = audio_path
        
        # Otimizar áudio
        processed_path = preprocess_audio(temp_file_path)
        if processed_path != temp_file_path:
            temp_files.append(processed_path)
            temp_file_path = processed_path
        
        # Escolher modelo otimizado
        model_name = choose_optimal_model(len(content))
        model = load_whisper_model(model_name)
        
        logger.info(f"Usando modelo: {model_name}")
        
        # Transcrever com configurações otimizadas
        transcribe_options = {
            "fp16": False,
            "temperature": 0.0,
            "no_speech_threshold": 0.6,
            "logprob_threshold": -1.0,
            "compression_ratio_threshold": 2.4
        }
        
        if language and language != "auto":
            transcribe_options["language"] = language
        
        # Processar em thread separada para não bloquear
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            executor, 
            lambda: model.transcribe(temp_file_path, **transcribe_options)
        )
        
        # Preparar resposta
        response = {
            "text": result["text"].strip(),
            "language": result["language"],
            "segments": result["segments"],
            "filename": file.filename,
            "model_used": model_name,
            "duration": result.get("segments", [])[-1]["end"] if result.get("segments") else 0,
            "cached": False,
            "resources_used": get_system_resources()
        }
        
        # Salvar no cache com limpeza automática
        if use_cache:
            cleanup_cache()  # Limpar antes de adicionar
            transcription_cache[cache_key] = response.copy()
            transcription_cache[cache_key]["cached"] = True
            cache_access_times[cache_key] = time.time()
        
        logger.info("Transcrição concluída com sucesso")
        return response
        
    except Exception as e:
        logger.error(f"Erro na transcrição: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro na transcrição: {str(e)}")
    
    finally:
        # Limpar arquivos temporários
        for temp_path in temp_files:
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            except Exception as e:
                logger.warning(f"Erro ao limpar arquivo {temp_path}: {e}")

@app.post("/transcribe-simple")
async def transcribe_simple(file: UploadFile = File(...)):
    """
    Versão simples - retorna apenas o texto
    """
    result = await transcribe_audio(file=file, language="pt", use_cache=True)
    return {"text": result["text"]}

@app.post("/ocr/image")
async def ocr_image(file: UploadFile = File(...)):
    """
    OCR de imagem - Versão Otimizada
    """
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Arquivo muito grande. Máximo: {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    # Verificar cache
    file_hash = get_file_hash(content)
    cache_key = f"ocr_{file_hash}"
    
    if cache_key in transcription_cache:
        cache_access_times[cache_key] = time.time()
        return transcription_cache[cache_key]
    
    temp_files = []
    try:
        suffix = f".{file.filename.split('.')[-1]}" if file.filename else ".jpg"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
            temp_files.append(temp_file_path)
        
        # Processar OCR
        result = extract_text_from_image_simple(temp_file_path)
        
        response = {
            **result,
            "filename": file.filename,
            "file_size": len(content),
            "cached": False
        }
        
        # Salvar no cache
        cleanup_cache()
        transcription_cache[cache_key] = response.copy()
        transcription_cache[cache_key]["cached"] = True
        cache_access_times[cache_key] = time.time()
        
        return response
        
    except Exception as e:
        logger.error(f"Erro no OCR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro no OCR: {str(e)}")
    
    finally:
        for temp_path in temp_files:
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            except Exception as e:
                logger.warning(f"Erro ao limpar arquivo {temp_path}: {e}")

@app.get("/cache/clear")
async def clear_cache():
    """Limpa o cache de transcrições"""
    global transcription_cache, cache_access_times
    cache_size = len(transcription_cache)
    transcription_cache.clear()
    cache_access_times.clear()
    gc.collect()
    return {"message": f"Cache limpo. {cache_size} itens removidos."}

@app.get("/cache/stats")
async def cache_stats():
    """Estatísticas do cache e sistema"""
    return {
        "cache_size": len(transcription_cache),
        "max_cache_size": MAX_CACHE_SIZE,
        "resources": get_system_resources(),
        "memory_usage_mb": sum(len(str(v)) for v in transcription_cache.values()) / (1024 * 1024)
    }

if __name__ == "__main__":
    print("🚀 Iniciando Avantar Transcribe API - Versão Otimizada...")
    print(f"💾 Memória disponível: {psutil.virtual_memory().available // (1024*1024)} MB")
    print(f"🖥️  CPU cores: {psutil.cpu_count()}")
    
    try:
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=8000,
            log_level="info",
            access_log=True,
            workers=1  # Apenas 1 worker para economizar memória
        )
    except Exception as e:
        print(f"❌ Erro na inicialização: {e}")
        import traceback
        traceback.print_exc()