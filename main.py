# Code to be fixed hereimport os
import uuid
import json
import datetime
import csv
from flask import Flask, request, jsonify, render_template_string, send_file
from werkzeug.utils import secure_filename
from openai import OpenAI
import chromadb
from chromadb.utils import embedding_functions
from PyPDF2 import PdfReader
from docx import Document
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

# ----------------------------
# Flask setup
# ----------------------------
app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# ----------------------------
# OpenAI client
# ----------------------------
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ----------------------------
# ChromaDB setup
# ----------------------------
chroma_client = chromadb.PersistentClient(path="chroma_db")
embedding_func = embedding_functions.OpenAIEmbeddingFunction(
    api_key=os.getenv("OPENAI_API_KEY"),
    model_name="text-embedding-3-small"
)
try:
    collection = chroma_client.get_collection("kanoonpk")
except:
    collection = chroma_client.create_collection("kanoonpk", embedding_function=embedding_func)

LEGAL_SYSTEM_PROMPT = """
You are KanoonPK, an AI Legal Research Assistant specialized in Pakistan law.
Answer only from Pakistan's laws, case references, and uploaded documents.
Always provide citations if available.
"""

# ----------------------------
# File processing
# ----------------------------
def extract_text_from_pdf(path):
    reader = PdfReader(path)
    return "\n".join([page.extract_text() or "" for page in reader.pages])

def extract_text_from_docx(path):
    doc = Document(path)
    return "\n".join([p.text for p in doc.paragraphs])

def save_to_collection(file_path, filename):
    if filename.endswith(".pdf"):
        text = extract_text_from_pdf(file_path)
    elif filename.endswith(".docx"):
        text = extract_text_from_docx(file_path)
    else:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

    chunks = [text[i:i+1000] for i in range(0, len(text), 1000)]
    ids = [str(uuid.uuid4()) for _ in chunks]
    metas = [{"source": filename, "citation": filename}] * len(chunks)
    collection.add(documents=chunks, metadatas=metas, ids=ids)

# ----------------------------
# Routes
# ----------------------------

@app.route("/")
def home():
    return render_template_string("""
    <html>
    <head>
      <title>KanoonPK - AI Legal Research</title>
      <style>
        body { font-family: Arial; margin: 0; padding: 0; }
        .chat-container { max-width: 800px; margin: auto; padding: 20px; }
        .msg { padding: 10px; margin: 10px; border-radius: 10px; }
        .user { background: #007BFF; color: white; text-align: right; }
        .bot { background: #f1f1f1; color: black; text-align: left; }
        #messages { height: 500px; overflow-y: auto; border: 1px solid #ccc; padding: 10px; }
        input { width: 80%; padding: 10px; }
        button { padding: 10px; margin: 5px; }
      </style>
    </head>
    <body>
      <div class="chat-container">
        <h1>⚖️ KanoonPK AI Legal Research</h1>
        <div id="messages"></div>
        <input id="userInput" placeholder="Ask about Pakistan law..." onkeydown="if(event.key==='Enter')sendMessage()">
        <button onclick="sendMessage()">Send</button>
        <button onclick="downloadPDF()">📄 Download Last Answer as PDF</button>
      </div>

      <script>
        let lastAnswer = "";
        let lastCitations = [];

        async function sendMessage() {
          const input = document.getElementById("userInput");
          const msgBox = document.getElementById("messages");
          const userText = input.value.trim();
          if (!userText) return;

          msgBox.innerHTML += `<div class='msg user'>${userText}</div>`;
          input.value = "";

          const res = await fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: userText })
          });
          const data = await res.json();

          lastAnswer = data.reply;
          lastCitations = data.sources;

          let citationText = data.sources.length ? `<br><small>📑 Citations: ${data.sources.join(", ")}</small>` : "";
          msgBox.innerHTML += `<div class='msg bot'>${data.reply.replace(/\\n/g,"<br>")} ${citationText}</div>`;
          msgBox.scrollTop = msgBox.scrollHeight;
        }

        async function downloadPDF() {
          if (!lastAnswer) {
            alert("⚠️ No answer to download yet.");
            return;
          }
          const res = await fetch("/export_pdf", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: lastAnswer, citations: lastCitations })
          });
          const blob = await res.blob();
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = "KanoonPk_Answer.pdf";
          document.body.appendChild(a);
          a.click();
          a.remove();
        }
      </script>
    </body>
    </html>
    """)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        file = request.files["file"]
        if file:
            filename = secure_filename(file.filename)
            path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(path)
            save_to_collection(path, filename)
            return "Uploaded & indexed!"
    return """
    <h1>Admin - Upload Legal Docs</h1>
    <form method='POST' enctype='multipart/form-data'>
      <input type='file' name='file'>
      <input type='submit' value='Upload'>
    </form>
    """

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message")

    results = collection.query(query_texts=[user_input], n_results=3)
    context = ""
    citations_used = []
    for i, doc in enumerate(results["documents"][0]):
        citation = results["metadatas"][0][i]["citation"]
        citations_used.append(citation)
        context += f"\n\n[Citation: {citation}] {doc[:800]}..."

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": LEGAL_SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": "Relevant documents:\n" + context}
        ]
    )
    reply = response.choices[0].message.content

    # Log history
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "question": user_input,
        "reply": reply,
        "citations": citations_used
    }
    os.makedirs("logs", exist_ok=True)
    history_file = "logs/history.json"
    if os.path.exists(history_file):
        with open(history_file, "r", encoding="utf-8") as f:
            history = json.load(f)
    else:
        history = []
    history.append(log_entry)
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

    return jsonify({"reply": reply, "sources": citations_used})

@app.route("/history")
def history():
    history_file = "logs/history.json"
    if not os.path.exists(history_file):
        return "<h2>No history yet.</h2>"

    with open(history_file, "r", encoding="utf-8") as f:
        history = json.load(f)

    html = "<h1>⚖️ KanoonPK — Search History</h1>"
    html += "<a href='/export_csv'>⬇️ Download as CSV</a><br><br>"
    html += "<table border='1' cellpadding='8' style='border-collapse:collapse;'>"
    html += "<tr><th>Time</th><th>Question</th><th>AI Reply (short)</th><th>Citations</th></tr>"

    for h in reversed(history[-50:]):
        short_reply = (h['reply'][:200] + "...") if len(h['reply']) > 200 else h['reply']
        html += f"<tr><td>{h['timestamp']}</td><td>{h['question']}</td><td>{short_reply}</td><td>{', '.join(h['citations'])}</td></tr>"

    html += "</table>"
    return html

@app.route("/export_csv")
def export_csv():
    history_file = "logs/history.json"
    if not os.path.exists(history_file):
        return "No history to export."
    with open(history_file, "r", encoding="utf-8") as f:
        history = json.load(f)

    filename = f"exports/history_{uuid.uuid4().hex}.csv"
    os.makedirs("exports", exist_ok=True)

    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Timestamp", "Question", "Reply", "Citations"])
        for h in history:
            writer.writerow([h["timestamp"], h["question"], h["reply"], "; ".join(h["citations"])])

    return send_file(filename, as_attachment=True)

@app.route("/export_pdf", methods=["POST"])
def export_pdf():
    data = request.json
    text = data.get("text", "")
    citations = data.get("citations", [])

    filename = f"exports/{uuid.uuid4().hex}.pdf"
    os.makedirs("exports", exist_ok=True)

    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    # Watermark
    c.setFont("Helvetica-Bold", 60)
    c.setFillGray(0.9, 0.3)
    c.saveState()
    c.translate(width/2, height/2)
    c.rotate(45)
    c.drawCentredString(0, 0, "KanoonPK")
    c.restoreState()

    y = height - 60

    # Citation Banner
    if citations:
        c.setFillColor(colors.HexColor("#007BFF"))
        c.rect(40, y-30, width-80, 30, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y-20, "Citations: " + ", ".join(citations))
        y -= 50

    # Answer text
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 12)
    for line in text.split("\n"):
        c.drawString(50, y, line)
        y -= 18
        if y < 80:
            c.showPage()
            y = height - 80
            c.setFont("Helvetica", 12)

    c.save()
    return send_file(filename, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
