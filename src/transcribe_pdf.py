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
        final_text = "\n\n".join(all_text).strip()
        
        return {
            "text": final_text,
            "pages_processed": len(reader.pages),
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Erro ao processar PDF: {e}")
        return {
            "text": "",
            "error": str(e),
            "status": "error"
        }