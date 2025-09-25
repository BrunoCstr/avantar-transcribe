from fastapi import FastAPI, UploadFile, File
from pypdf import PdfReader

app = FastAPI()

@app.post("/extract")
async def extract(file: UploadFile = File(...)):
    reader = PdfReader(await file.read())
    texts = []
    for page in reader.pages:
        texts.append(page.extract_text() or "")
    return {"text": "\n\n".join(texts).strip()}
