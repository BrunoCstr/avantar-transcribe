from fastapi import FastAPI, UploadFile, File
import io
import re
from pypdf import PdfReader
from pdf2image import convert_from_bytes
import pytesseract
from PIL import Image
import logging

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

@app.post("/extract")
async def extract(file: UploadFile = File(...)):
    try:
        data = await file.read()
        reader = PdfReader(io.BytesIO(data))
        
        all_text = []
        
        for page_num, page in enumerate(reader.pages, 1):
            logger.info(f"Processando página {page_num}")
            
            # 1. Extrair texto direto do PDF
            page_text = page.extract_text() or ""
            page_text = clean_text(page_text)
            
            if page_text:
                all_text.append(f"=== PÁGINA {page_num} (TEXTO) ===")
                all_text.append(page_text)
            
            # 2. Extrair texto de imagens na página
            try:
                # Converter página para imagem
                images = convert_from_bytes(data, first_page=page_num, last_page=page_num, dpi=300)
                
                if images:
                    # Converter imagem para bytes
                    img_buffer = io.BytesIO()
                    images[0].save(img_buffer, format='PNG')
                    img_bytes = img_buffer.getvalue()
                    
                    # Extrair texto da imagem
                    image_text = extract_text_from_image(img_bytes)
                    image_text = clean_text(image_text)
                    
                    if image_text:
                        all_text.append(f"=== PÁGINA {page_num} (OCR) ===")
                        all_text.append(image_text)
                        
            except Exception as e:
                logger.warning(f"Erro ao processar imagens da página {page_num}: {e}")
        
        # Combinar todo o texto
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