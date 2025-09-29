from fastapi import FastAPI, UploadFile, File, HTTPException
import io
import re
from pypdf import PdfReader
import logging
from PIL import Image
import pytesseract
import whisper
import tempfile
import os
import subprocess
from typing import Optional
import aiofiles

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="PDF and Video Transcription API",
    description="API para extração de texto de PDFs, OCR de imagens e transcrição de vídeos",
    version="2.0.0"
)

# Carregar modelo Whisper Tiny (otimizado para VPS)
logger.info("Carregando modelo Whisper Tiny...")
try:
    whisper_model = whisper.load_model("tiny")
    logger.info("Modelo Whisper carregado com sucesso!")
except Exception as e:
    logger.error(f"Erro ao carregar modelo Whisper: {e}")
    whisper_model = None

@app.get("/health")
def health(): 
    return {
        "ok": True,
        "services": {
            "pdf_extraction": True,
            "ocr": True,
            "video_transcription": whisper_model is not None
        }
    }

@app.get("/test")
def test():
    """Endpoint de teste para verificar funcionamento"""
    return {
        "status": "ok",
        "message": "Serviço funcionando",
        "version": "2.0.0"
    }

@app.post("/debug-file")
async def debug_file(file: UploadFile = File(...)):
    """Endpoint para debug de arquivos - mostra informações detalhadas"""
    try:
        data = await file.read()
        
        # Informações básicas
        info = {
            "filename": file.filename,
            "content_type": file.content_type,
            "size_bytes": len(data),
            "first_20_bytes": data[:20].hex() if len(data) >= 20 else data.hex(),
            "first_20_chars": data[:20].decode('utf-8', errors='ignore') if len(data) >= 20 else data.decode('utf-8', errors='ignore'),
            "is_pdf_header": data.startswith(b'%PDF'),
            "is_pdf_header_lower": data.startswith(b'%pdf'),
        }
        
        # Tentar identificar o tipo de arquivo
        if data.startswith(b'%PDF'):
            info["file_type"] = "PDF (header padrão)"
        elif data.startswith(b'%pdf'):
            info["file_type"] = "PDF (header minúsculo)"
        elif data.startswith(b'\x25PDF'):
            info["file_type"] = "PDF (header codificado)"
        elif data.startswith(b'PK'):
            info["file_type"] = "Possivelmente ZIP/Office"
        elif data.startswith(b'\x89PNG'):
            info["file_type"] = "PNG"
        elif data.startswith(b'\xff\xd8\xff'):
            info["file_type"] = "JPEG"
        else:
            info["file_type"] = "Desconhecido"
        
        # Tentar carregar como PDF
        try:
            reader = PdfReader(io.BytesIO(data))
            info["pdf_pages"] = len(reader.pages)
            info["pdf_loaded"] = True
        except Exception as e:
            info["pdf_loaded"] = False
            info["pdf_error"] = str(e)
        
        return {
            "status": "success",
            "file_info": info
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

def detect_file_type(data):
    """Detecta o tipo de arquivo baseado nos primeiros bytes"""
    if data.startswith(b'%PDF'):
        return "PDF"
    elif data.startswith(b'\xff\xd8\xff'):
        return "JPEG"
    elif data.startswith(b'\x89PNG'):
        return "PNG"
    elif data.startswith(b'PK'):
        return "ZIP/Office"
    elif data.startswith(b'GIF'):
        return "GIF"
    elif data.startswith(b'BM'):
        return "BMP"
    else:
        return "Desconhecido"

def remove_ocr_artifacts(text):
    """Remove lixo de OCR e layout"""
    if not text:
        return ""
    
    # Normalizar quebras de linha
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # Remover espaços duplos e múltiplos
    text = re.sub(r' +', ' ', text)
    
    # Remover quebras de linha múltiplas (mais de 2 seguidas)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remover linhas muito curtas que são provavelmente lixo de OCR
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        
        # Remover linhas vazias
        if not line:
            continue
            
        # Remover linhas com apenas caracteres especiais ou números
        if re.match(r'^[^\w\s]*$', line) or re.match(r'^\d+$', line):
            continue
            
        # Remover linhas muito curtas (menos de 3 caracteres)
        if len(line) < 3:
            continue
            
        cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)

def normalize_text(text):
    """Normaliza o texto corrigindo erros comuns"""
    if not text:
        return ""
    
    # Correções específicas
    corrections = {
        'VIdros': 'Vidros',
        'vIdros': 'vidros',
        'VIDROS': 'Vidros',
        'Para-brisa': 'Para-brisa',
        'para-brisa': 'Para-brisa',
        'PARA-BRISA': 'Para-brisa',
        'Lanternas': 'Lanternas',
        'lanternas': 'Lanternas',
        'LANTERNAS': 'Lanternas',
        'Faróis': 'Faróis',
        'faróis': 'Faróis',
        'FARÓIS': 'Faróis',
        'Retrovisores': 'Retrovisores',
        'retrovisores': 'Retrovisores',
        'RETROVISORES': 'Retrovisores',
        'Pequenos Reparos': 'Pequenos Reparos',
        'pequenos reparos': 'Pequenos Reparos',
        'PEQUENOS REPAROS': 'Pequenos Reparos',
    }
    
    for wrong, correct in corrections.items():
        text = text.replace(wrong, correct)
    
    return text

def clean_text(text):
    """Remove cabeçalhos, rodapés e limpa o texto"""
    if not text:
        return ""
    
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        
        # Pular linhas vazias
        if not line:
            continue
            
        # Ignorar linhas muito curtas que podem ser cabeçalhos/rodapés
        if len(line) < 3:
            continue
            
        # Ignorar linhas que parecem ser cabeçalhos (muito curtas e em maiúsculas)
        if len(line) < 20 and line.isupper():
            continue
            
        # Ignorar linhas que parecem ser números de página
        if re.match(r'^\d+$', line):
            continue
            
        # Ignorar linhas que parecem ser rodapés (contêm palavras comuns de rodapé)
        footer_keywords = ['página', 'page', 'www.', 'http', 'email', 'tel:', 'telefone']
        if any(keyword in line.lower() for keyword in footer_keywords):
            continue
            
        cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)

def structure_as_markdown(text):
    """Estrutura o texto em Markdown"""
    if not text:
        return ""
    
    lines = text.split('\n')
    markdown_lines = []
    
    # Padrões para identificar títulos e seções
    title_patterns = [
        r'novos? serviços? nos? planos?',
        r'planos? de (vidros?|proteção)',
        r'cobertura.*planos?'
    ]
    
    section_patterns = [
        r'^(auto|carlos?)$',
        r'^(moto|motocicletas?)$',
        r'^(pequenos? reparos?)$',
        r'^(proteção pneu e roda)$',
        r'^(teto solar|panorâmico)$'
    ]
    
    service_patterns = [
        r'para-brisa',
        r'vidro traseiro',
        r'vidros? laterais?',
        r'película',
        r'lanternas?',
        r'faróis?',
        r'retrovisores?',
        r'logomarca'
    ]
    
    current_section = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        line_lower = line.lower()
        
        # Verificar se é um título principal
        is_main_title = any(re.search(pattern, line_lower) for pattern in title_patterns)
        if is_main_title:
            markdown_lines.append(f"# {line}")
            continue
            
        # Verificar se é uma seção
        is_section = any(re.search(pattern, line_lower) for pattern in section_patterns)
        if is_section:
            current_section = line
            markdown_lines.append(f"## {line}")
            continue
            
        # Verificar se é um serviço
        is_service = any(re.search(pattern, line_lower) for pattern in service_patterns)
        if is_service:
            markdown_lines.append(f"- {line}")
            continue
            
        # Verificar se contém informações de planos (✓, X, etc.)
        if any(char in line for char in ['✓', '×', 'X', 'v', 'x']):
            # Pode ser uma linha de plano
            markdown_lines.append(f"  - {line}")
            continue
            
        # Linha normal
        if current_section:
            markdown_lines.append(f"  - {line}")
        else:
            markdown_lines.append(line)
    
    return '\n'.join(markdown_lines)

def create_service_table(text):
    """Cria uma tabela de serviços vs planos se possível"""
    lines = text.split('\n')
    
    # Encontrar serviços e planos
    services = []
    plans = []
    
    for line in lines:
        line = line.strip().lower()
        
        # Identificar serviços
        if any(service in line for service in ['para-brisa', 'vidro', 'lanterna', 'farol', 'retrovisor']):
            if line not in services:
                services.append(line)
        
        # Identificar planos (números ou nomes)
        if re.match(r'plano \d+', line) or re.match(r'\d+', line):
            if line not in plans:
                plans.append(line)
    
    if not services or not plans:
        return ""
    
    # Criar tabela markdown
    table_lines = ["\n## Tabela de Cobertura\n"]
    table_lines.append("| Serviço | " + " | ".join(plans) + " |")
    table_lines.append("|" + "---|" * (len(plans) + 1))
    
    for service in services:
        row = f"| {service} | " + " | ".join(["✓" for _ in plans]) + " |"
        table_lines.append(row)
    
    return '\n'.join(table_lines)

@app.post("/extract")
async def extract(file: UploadFile = File(...)):
    try:
        logger.info(f"Iniciando processamento do arquivo: {file.filename}")
        
        # Ler dados do arquivo
        data = await file.read()
        logger.info(f"Arquivo lido com sucesso. Tamanho: {len(data)} bytes")
        
        if len(data) == 0:
            return {
                "text": "",
                "error": "Arquivo vazio",
                "status": "error"
            }
        
        # Detectar tipo de arquivo
        file_type = detect_file_type(data)
        logger.info(f"Tipo de arquivo detectado: {file_type}")
        
        if file_type == "JPEG" or file_type == "PNG":
            # Processar como imagem usando OCR
            logger.info("Processando como imagem com OCR...")
            try:
                image = Image.open(io.BytesIO(data))
                text = pytesseract.image_to_string(image, lang='por')
                text = clean_text(text)
                
                if not text.strip():
                    return {
                        "text": "",
                        "error": "Nenhum texto foi extraído da imagem",
                        "status": "error"
                    }
                
                # Processar o texto extraído
                processed_text = remove_ocr_artifacts(text)
                processed_text = normalize_text(processed_text)
                markdown_text = structure_as_markdown(processed_text)
                
                return {
                    "text": markdown_text,
                    "raw_text": text,
                    "pages_processed": 1,
                    "status": "success",
                    "format": "markdown",
                    "file_type": file_type
                }
                
            except Exception as ocr_error:
                logger.error(f"Erro no OCR: {ocr_error}")
                return {
                    "text": "",
                    "error": f"Erro ao processar imagem: {str(ocr_error)}",
                    "status": "error"
                }
        
        elif file_type != "PDF":
            return {
                "text": "",
                "error": f"Tipo de arquivo não suportado: {file_type}. Use PDF ou imagens (JPEG/PNG)",
                "status": "error"
            }
        
        # Processar como PDF
        try:
            reader = PdfReader(io.BytesIO(data))
            logger.info(f"PDF carregado com sucesso. Páginas: {len(reader.pages)}")
        except Exception as pdf_error:
            logger.error(f"Erro ao carregar PDF: {pdf_error}")
            return {
                "text": "",
                "error": f"Erro ao carregar PDF: {str(pdf_error)}",
                "status": "error"
            }
        
        all_text = []
        
        for page_num, page in enumerate(reader.pages, 1):
            try:
                logger.info(f"Processando página {page_num}")
                
                # Extrair texto direto do PDF
                page_text = page.extract_text() or ""
                page_text = clean_text(page_text)
                
                if page_text.strip():
                    all_text.append(page_text)
                    logger.info(f"Página {page_num} processada com sucesso. Texto: {len(page_text)} caracteres")
                else:
                    logger.warning(f"Página {page_num} não contém texto extraível")
                    
            except Exception as page_error:
                logger.error(f"Erro ao processar página {page_num}: {page_error}")
                continue
        
        if not all_text:
            return {
                "text": "",
                "error": "Nenhum texto foi extraído do PDF",
                "status": "error"
            }
        
        # Combinar todo o texto
        raw_text = "\n\n".join(all_text).strip()
        logger.info(f"Texto combinado: {len(raw_text)} caracteres")
        
        # Processar o texto final
        processed_text = raw_text
        
        # 1. Remover lixo de OCR e layout
        processed_text = remove_ocr_artifacts(processed_text)
        
        # 2. Normalizar texto
        processed_text = normalize_text(processed_text)
        
        # 3. Estruturar em Markdown
        markdown_text = structure_as_markdown(processed_text)
        
        # 4. Criar tabela de serviços (se aplicável)
        service_table = create_service_table(markdown_text)
        
        # 5. Combinar markdown com tabela
        final_markdown = markdown_text
        if service_table:
            final_markdown += service_table
        
        logger.info("Processamento concluído com sucesso")
        
        return {
            "text": final_markdown,
            "raw_text": raw_text,
            "pages_processed": len(reader.pages),
            "status": "success",
            "format": "markdown"
        }
        
    except Exception as e:
        logger.error(f"Erro geral ao processar PDF: {e}", exc_info=True)
        return {
            "text": "",
            "error": f"Erro interno: {str(e)}",
            "status": "error"
        }

@app.post("/extract-structured")
async def extract_structured(file: UploadFile = File(...)):
    """Endpoint que retorna texto estruturado em JSON"""
    try:
        data = await file.read()
        reader = PdfReader(io.BytesIO(data))
        
        all_text = []
        
        for page_num, page in enumerate(reader.pages, 1):
            logger.info(f"Processando página {page_num}")
            
            # Extrair texto direto do PDF
            page_text = page.extract_text() or ""
            page_text = clean_text(page_text)
            
            if page_text.strip():
                all_text.append(page_text)
        
        # Processar texto
        raw_text = "\n\n".join(all_text).strip()
        processed_text = remove_ocr_artifacts(raw_text)
        processed_text = normalize_text(processed_text)
        
        # Extrair informações estruturadas
        lines = processed_text.split('\n')
        
        # Identificar seções e serviços
        sections = {}
        current_section = None
        services = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            line_lower = line.lower()
            
            # Verificar seções
            if any(re.search(pattern, line_lower) for pattern in [
                r'^(auto|carlos?)$', r'^(moto|motocicletas?)$', 
                r'^(pequenos? reparos?)$', r'^(proteção pneu e roda)$'
            ]):
                current_section = line
                sections[current_section] = []
                continue
            
            # Verificar serviços
            if any(service in line_lower for service in [
                'para-brisa', 'vidro', 'lanterna', 'farol', 'retrovisor', 'película'
            ]):
                if current_section:
                    sections[current_section].append(line)
                services.append(line)
        
        return {
            "markdown": structure_as_markdown(processed_text),
            "sections": sections,
            "services": services,
            "raw_text": raw_text,
            "pages_processed": len(reader.pages),
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Erro ao processar PDF: {e}")
        return {
            "error": str(e),
            "status": "error"
        }

# ========== FUNÇÕES DE TRANSCRIÇÃO DE VÍDEO ==========

def convert_video_to_audio(video_path: str) -> str:
    """Converte vídeo para áudio usando ffmpeg"""
    audio_path = video_path.rsplit('.', 1)[0] + '_audio.wav'
    
    cmd = [
        'ffmpeg', '-i', video_path,
        '-vn',  # Sem vídeo
        '-acodec', 'pcm_s16le',  # Codec de áudio
        '-ar', '16000',  # Sample rate otimizado para Whisper
        '-ac', '1',  # Mono
        '-y',  # Sobrescrever
        audio_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return audio_path
    except subprocess.CalledProcessError as e:
        logger.error(f"Erro na conversão: {e.stderr}")
        raise HTTPException(status_code=500, detail="Erro na conversão do vídeo")

def transcribe_video_file(video_path: str, language: str = "pt") -> dict:
    """Transcreve arquivo de vídeo usando Whisper"""
    if not whisper_model:
        raise HTTPException(status_code=500, detail="Modelo Whisper não disponível")
    
    try:
        # Converter vídeo para áudio
        audio_path = convert_video_to_audio(video_path)
        
        # Transcrever áudio
        transcribe_options = {
            "fp16": False,  # Melhor compatibilidade
            "temperature": 0.0,  # Mais determinístico
        }
        
        if language and language != "auto":
            transcribe_options["language"] = language
        
        result = whisper_model.transcribe(audio_path, **transcribe_options)
        
        # Limpar arquivo de áudio temporário
        try:
            os.unlink(audio_path)
        except:
            pass
        
        return {
            "text": result["text"].strip(),
            "language": result["language"],
            "segments": result["segments"],
            "duration": result.get("segments", [])[-1]["end"] if result.get("segments") else 0
        }
        
    except Exception as e:
        logger.error(f"Erro na transcrição: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro na transcrição: {str(e)}")

# ========== ENDPOINTS DE TRANSCRIÇÃO DE VÍDEO ==========

@app.post("/transcribe-video")
async def transcribe_video(
    file: UploadFile = File(...),
    language: Optional[str] = "pt"
):
    """
    Transcreve arquivo de vídeo para texto
    
    - **file**: Arquivo de vídeo (mp4, avi, mov, mkv, etc.)
    - **language**: Código do idioma (pt, en, es, etc.)
    """
    
    # Verificar se é um arquivo de vídeo
    allowed_video_types = {
        'video/mp4', 'video/avi', 'video/mov', 'video/mkv',
        'video/webm', 'video/quicktime'
    }
    
    content = await file.read()
    
    # Verificar tipo de arquivo
    if file.content_type not in allowed_video_types:
        # Tentar detectar pela extensão
        ext = file.filename.split('.')[-1].lower() if file.filename else ""
        if ext not in ['mp4', 'avi', 'mov', 'mkv', 'webm', 'qt']:
            raise HTTPException(
                status_code=400, 
                detail=f"Tipo de arquivo não suportado: {file.content_type}. Use arquivos de vídeo."
            )
    
    # Limite de tamanho (100MB)
    if len(content) > 100 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="Arquivo muito grande. Máximo: 100MB"
        )
    
    temp_files = []
    try:
        # Criar arquivo temporário
        suffix = f".{file.filename.split('.')[-1]}" if file.filename else ".mp4"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
            temp_files.append(temp_file_path)
        
        logger.info(f"Transcrevendo vídeo: {file.filename} ({len(content)} bytes)")
        
        # Transcrever vídeo
        result = transcribe_video_file(temp_file_path, language)
        
        # Preparar resposta
        response = {
            **result,
            "filename": file.filename,
            "file_size": len(content),
            "status": "success"
        }
        
        logger.info("Transcrição de vídeo concluída com sucesso")
        return response
        
    except Exception as e:
        logger.error(f"Erro na transcrição de vídeo: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro na transcrição: {str(e)}")
    
    finally:
        # Limpar arquivos temporários
        for temp_path in temp_files:
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            except Exception as e:
                logger.warning(f"Erro ao limpar arquivo {temp_path}: {e}")

@app.post("/transcribe-audio")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: Optional[str] = "pt"
):
    """
    Transcreve arquivo de áudio para texto
    
    - **file**: Arquivo de áudio (mp3, wav, m4a, ogg, flac, etc.)
    - **language**: Código do idioma (pt, en, es, etc.)
    """
    
    # Verificar se é um arquivo de áudio
    allowed_audio_types = {
        'audio/mpeg', 'audio/wav', 'audio/mp4', 'audio/m4a',
        'audio/ogg', 'audio/webm', 'audio/flac', 'audio/x-wav'
    }
    
    content = await file.read()
    
    # Verificar tipo de arquivo
    if file.content_type not in allowed_audio_types:
        # Tentar detectar pela extensão
        ext = file.filename.split('.')[-1].lower() if file.filename else ""
        if ext not in ['mp3', 'wav', 'm4a', 'ogg', 'webm', 'flac']:
            raise HTTPException(
                status_code=400, 
                detail=f"Tipo de arquivo não suportado: {file.content_type}. Use arquivos de áudio."
            )
    
    # Limite de tamanho (100MB)
    if len(content) > 100 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="Arquivo muito grande. Máximo: 100MB"
        )
    
    temp_files = []
    try:
        # Criar arquivo temporário
        suffix = f".{file.filename.split('.')[-1]}" if file.filename else ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
            temp_files.append(temp_file_path)
        
        logger.info(f"Transcrevendo áudio: {file.filename} ({len(content)} bytes)")
        
        # Transcrever áudio diretamente
        if not whisper_model:
            raise HTTPException(status_code=500, detail="Modelo Whisper não disponível")
        
        transcribe_options = {
            "fp16": False,
            "temperature": 0.0,
        }
        
        if language and language != "auto":
            transcribe_options["language"] = language
        
        result = whisper_model.transcribe(temp_file_path, **transcribe_options)
        
        # Preparar resposta
        response = {
            "text": result["text"].strip(),
            "language": result["language"],
            "segments": result["segments"],
            "duration": result.get("segments", [])[-1]["end"] if result.get("segments") else 0,
            "filename": file.filename,
            "file_size": len(content),
            "status": "success"
        }
        
        logger.info("Transcrição de áudio concluída com sucesso")
        return response
        
    except Exception as e:
        logger.error(f"Erro na transcrição de áudio: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro na transcrição: {str(e)}")
    
    finally:
        # Limpar arquivos temporários
        for temp_path in temp_files:
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            except Exception as e:
                logger.warning(f"Erro ao limpar arquivo {temp_path}: {e}")

@app.post("/transcribe-auto")
async def transcribe_auto(file: UploadFile = File(...)):
    """
    Detecção automática do tipo de arquivo e transcrição
    
    - **file**: Qualquer arquivo suportado (PDF, imagem, vídeo, áudio)
    """
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nome do arquivo é obrigatório")
    
    filename = file.filename.lower()
    
    # Redirecionar para endpoint apropriado baseado na extensão
    if any(filename.endswith(ext) for ext in ['.mp3', '.wav', '.ogg', '.m4a', '.flac']):
        return await transcribe_audio(file)
    
    elif any(filename.endswith(ext) for ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']):
        return await transcribe_video(file)
    
    elif any(filename.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']):
        # Para imagens, usar OCR
        return await extract(file)
    
    elif filename.endswith('.pdf'):
        return await extract(file)
    
    else:
        raise HTTPException(
            status_code=400, 
            detail=f"Tipo de arquivo não suportado: {filename.split('.')[-1] if '.' in filename else 'desconhecido'}"
        )
