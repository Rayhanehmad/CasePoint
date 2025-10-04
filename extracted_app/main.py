from fastapi import FastAPI, UploadFile, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn
import uuid
import pdfplumber

app = FastAPI()

templates = Jinja2Templates(directory="templates")

# In-memory DB (replace with Postgres later)
DATABASE = {}

class ChatRequest(BaseModel):
    judgment_id: str
    query: str

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "judgments": DATABASE})

@app.post("/upload-judgment/")
async def upload_judgment(file: UploadFile, title: str = Form(...), court: str = Form(...), date: str = Form(...)):
    # --- Extract Text ---
    text = ""
    if file.filename.lower().endswith(".pdf"):
        # Extract PDF text
        with pdfplumber.open(file.file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    else:
        # Assume plain text file
        raw = await file.read()
        text = raw.decode("utf-8", errors="ignore")

    if not text.strip():
        text = "⚠️ Could not extract text from this file."

    # --- Mock Headnote & Summary ---
    headnote = f"Headnote for {title}"
    summary = f"Summary for {title[:50]}..."

    # --- Save in DB ---
    judgment_id = str(uuid.uuid4())
    DATABASE[judgment_id] = {
        "title": title,
        "court": court,
        "date": date,
        "full_text": text,
        "headnote": headnote,
        "summary": summary,
    }

    return {"judgment_id": judgment_id, "message": "Uploaded successfully!"}

@app.post("/chat-judgment/")
async def chat_with_judgment(req: ChatRequest):
    # Mock AI answer (replace with GPT + embeddings)
    answer = f"Mock AI response for: {req.query} (from judgment {req.judgment_id})"
    return {"answer": answer}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
