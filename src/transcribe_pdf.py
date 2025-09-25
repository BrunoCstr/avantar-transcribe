from fastapi import FastAPI, UploadFile, File
import io
import re
from pypdf import PdfReader
from pdf2image import convert_from_bytes
import pytesseract
from PIL import Image
import logging
import fitz  # PyMuPDF para extração com coordenadas

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.get("/health")
def health(): 
    return {"ok": True}

@app.post("/extract-structured")
async def extract_structured(file: UploadFile = File(...)):
    """Endpoint que retorna texto estruturado em JSON"""
    try:
        data = await file.read()
        reader = PdfReader(io.BytesIO(data))
        
        all_text = []
        
        for page_num, page in enumerate(reader.pages, 1):
            logger.info(f"Processando página {page_num}")
            
            # Extrair texto com coordenadas
            page_text = extract_text_with_coordinates(data, page_num)
            page_text = clean_text(page_text)
            
            # OCR se necessário
            ocr_text = ""
            if len(page_text.strip()) < 100:
                try:
                    images = convert_from_bytes(data, first_page=page_num, last_page=page_num, dpi=300)
                    if images:
                        img_buffer = io.BytesIO()
                        images[0].save(img_buffer, format='PNG')
                        img_bytes = img_buffer.getvalue()
                        ocr_text = extract_text_from_image(img_bytes)
                        ocr_text = clean_text(ocr_text)
                except Exception as e:
                    logger.warning(f"Erro no OCR página {page_num}: {e}")
            
            combined_text = merge_text_content(page_text, ocr_text)
            if combined_text.strip():
                all_text.append(combined_text)
        
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

def extract_text_from_image(image_bytes):
    """Extrai texto de uma imagem usando OCR"""
    try:
        # Converter bytes para imagem
        image = Image.open(io.BytesIO(image_bytes))
        
        # Configurar Tesseract para português
        custom_config = r'--oem 3 --psm 6 -l por'
        text = pytesseract.image_to_string(image, config=custom_config)
        
        return text.strip()
    except Exception as e:
        logger.error(f"Erro ao processar imagem: {e}")
        return ""

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

def extract_text_with_coordinates(pdf_bytes, page_num):
    """Extrai texto usando coordenadas para preservar ordem de leitura"""
    try:
        # Usar PyMuPDF para extrair com coordenadas
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page = doc[page_num - 1]  # PyMuPDF usa indexação baseada em 0
        
        # Extrair blocos de texto com coordenadas
        blocks = page.get_text("dict")
        
        text_blocks = []
        for block in blocks["blocks"]:
            if "lines" in block:  # Bloco de texto
                for line in block["lines"]:
                    line_text = ""
                    for span in line["spans"]:
                        line_text += span["text"]
                    
                    if line_text.strip():
                        # Usar coordenada Y para ordenação (de cima para baixo)
                        y_pos = line["bbox"][1]  # Coordenada Y do topo
                        text_blocks.append((y_pos, line_text.strip()))
        
        # Ordenar por posição Y (de cima para baixo)
        text_blocks.sort(key=lambda x: x[0])
        
        # Extrair apenas o texto, mantendo a ordem
        ordered_text = [block[1] for block in text_blocks]
        
        doc.close()
        return '\n'.join(ordered_text)
        
    except Exception as e:
        logger.warning(f"Erro ao extrair com coordenadas: {e}")
        # Fallback para método simples
        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            return reader.pages[page_num - 1].extract_text() or ""
        except:
            return ""

def extract_text_with_positioning(page):
    """Função de fallback para extração simples"""
    try:
        text = page.extract_text()
        if text:
            lines = text.split('\n')
            filtered_lines = [line.strip() for line in lines if line.strip()]
            return '\n'.join(filtered_lines)
        return ""
    except Exception as e:
        logger.warning(f"Erro ao extrair texto: {e}")
        return ""

def merge_text_content(page_text, ocr_text):
    """Combina texto do PDF com OCR de forma ordenada"""
    if not page_text and not ocr_text:
        return ""
    
    if not page_text:
        return ocr_text
    
    if not ocr_text:
        return page_text
    
    # Se temos ambos, vamos combinar de forma inteligente
    # Por enquanto, retorna o texto do PDF (que geralmente é mais preciso)
    # e adiciona o OCR apenas se o texto do PDF for muito curto
    if len(page_text.strip()) < 50:  # Se texto muito curto, pode ter perdido conteúdo
        return f"{page_text}\n\n[Conteúdo adicional via OCR]:\n{ocr_text}"
    else:
        return page_text

@app.post("/extract")
async def extract(file: UploadFile = File(...)):
    try:
    data = await file.read()
    reader = PdfReader(io.BytesIO(data))
        
        all_text = []
        
        for page_num, page in enumerate(reader.pages, 1):
            logger.info(f"Processando página {page_num}")
            
            # 1. Extrair texto direto do PDF (preserva ordem de leitura)
            page_text = extract_text_with_coordinates(data, page_num)
            page_text = clean_text(page_text)
            
            # 2. Se o texto for muito curto ou vazio, tentar OCR
            ocr_text = ""
            if len(page_text.strip()) < 100:  # Se pouco texto extraído
                try:
                    # Converter página para imagem para OCR
                    images = convert_from_bytes(data, first_page=page_num, last_page=page_num, dpi=300)
                    
                    if images:
                        # Converter imagem para bytes
                        img_buffer = io.BytesIO()
                        images[0].save(img_buffer, format='PNG')
                        img_bytes = img_buffer.getvalue()
                        
                        # Extrair texto da imagem
                        ocr_text = extract_text_from_image(img_bytes)
                        ocr_text = clean_text(ocr_text)
                        
                except Exception as e:
                    logger.warning(f"Erro ao processar OCR da página {page_num}: {e}")
            
            # 3. Combinar conteúdo de forma ordenada
            combined_text = merge_text_content(page_text, ocr_text)
            
            if combined_text.strip():
                all_text.append(combined_text)
        
        # Combinar todo o texto mantendo ordem sequencial
        raw_text = "\n\n".join(all_text).strip()
        
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
        
        return {
            "text": final_markdown,
            "raw_text": raw_text,
            "pages_processed": len(reader.pages),
            "status": "success",
            "format": "markdown"
        }
        
    except Exception as e:
        logger.error(f"Erro ao processar PDF: {e}")
        return {
            "text": "",
            "error": str(e),
            "status": "error"
        }