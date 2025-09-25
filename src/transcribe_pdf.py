from fastapi import FastAPI, UploadFile, File
import io
from pypdf import PdfReader

app = FastAPI()

@app.get("/health")
def health(): return {"ok": True}

@app.post("/extract")
async def extract(file: UploadFile = File(...)):
    data = await file.read()
    reader = PdfReader(io.BytesIO(data))
    text = "\n\n".join([p.extract_text() or "" for p in reader.pages]).strip()
    return {"text": text}