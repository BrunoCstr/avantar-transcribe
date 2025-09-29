from fastapi import FastAPI, UploadFile, File
import io
import re
from pypdf import PdfReader
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.get("/health")
def health(): 
    return {"ok": True}

@app.get("/test")
def test():
    """Endpoint de teste para verificar funcionamento"""
    return {
        "status": "ok",
        "message": "Serviço funcionando",
        "version": "1.0.0"
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
        
        # Verificar se é um PDF válido (mais flexível)
        pdf_headers = [b'%PDF', b'%pdf', b'\x25PDF', b'\x25pdf']
        is_pdf = any(data.startswith(header) for header in pdf_headers)
        
        if not is_pdf:
            # Log dos primeiros bytes para debug
            first_bytes = data[:20] if len(data) >= 20 else data
            logger.warning(f"Arquivo não tem header PDF padrão. Primeiros bytes: {first_bytes}")
            logger.info("Tentando processar mesmo assim...")
        
        # Criar reader com tratamento de erro (tenta mesmo sem header padrão)
        try:
            reader = PdfReader(io.BytesIO(data))
            logger.info(f"PDF carregado com sucesso. Páginas: {len(reader.pages)}")
        except Exception as pdf_error:
            # Log dos primeiros bytes para debug
            first_bytes = data[:20] if len(data) >= 20 else data
            logger.error(f"Erro ao carregar PDF: {pdf_error}")
            logger.error(f"Primeiros bytes do arquivo: {first_bytes}")
            return {
                "text": "",
                "error": f"Erro ao carregar PDF: {str(pdf_error)}. Primeiros bytes: {first_bytes}",
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