import os
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

def save_to_collection(file_path, filename, citation="", year="", page="", court=""):
    if filename.lower().endswith(".pdf"):
        text = extract_text_from_pdf(file_path)
    elif filename.lower().endswith(".docx"):
        text = extract_text_from_docx(file_path)
    elif filename.lower().endswith((".txt", ".text")):
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
    elif filename.lower().endswith((".jpg", ".jpeg", ".png")):
        # For image files, we'll store the filename as text
        text = f"Image file: {filename}"
    else:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

    chunks = [text[i:i+1000] for i in range(0, len(text), 1000)]
    ids = [str(uuid.uuid4()) for _ in chunks]
    metas = [{
        "source": filename, 
        "citation": citation or filename,
        "year": year,
        "page": page,
        "court": court
    }] * len(chunks)
    collection.add(documents=chunks, metadatas=metas, ids=ids)

# ----------------------------
# Routes
# ----------------------------

@app.route("/")
def home():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
      <title>KanoonPK - AI Legal Research</title>
      <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 0; background: #f8f9fa; }
        .chat-container { max-width: 900px; margin: auto; padding: 20px; }
        .header { text-align: center; margin-bottom: 20px; color: #333; }
        .admin-link { float: right; color: #007BFF; text-decoration: none; font-size: 14px; }
        .msg { padding: 12px; margin: 10px 0; border-radius: 10px; }
        .user { background: #007BFF; color: white; text-align: right; margin-left: 20%; }
        .bot { background: #ffffff; color: #333; text-align: left; margin-right: 20%; border: 1px solid #e0e0e0; }
        #messages { height: 400px; overflow-y: auto; border: 1px solid #ddd; padding: 15px; background: white; border-radius: 10px; margin-bottom: 20px; }
        .search-panel { background: white; border: 1px solid #ddd; border-radius: 10px; padding: 15px; margin-bottom: 15px; }
        .search-row { display: flex; gap: 10px; margin-bottom: 10px; flex-wrap: wrap; }
        .search-field { flex: 1; min-width: 150px; }
        .search-field label { display: block; font-size: 12px; color: #666; margin-bottom: 3px; }
        .search-field input, .search-field select { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }
        .input-section { display: flex; gap: 10px; }
        .input-section input { flex: 1; padding: 12px; border: 1px solid #ddd; border-radius: 25px; outline: none; }
        .input-section button { padding: 12px 20px; border: none; border-radius: 25px; cursor: pointer; font-weight: bold; }
        .send-btn { background: #007BFF; color: white; }
        .send-btn:hover { background: #0056b3; }
        .pdf-btn { background: #28a745; color: white; }
        .pdf-btn:hover { background: #1e7e34; }
        .clear-btn { background: #6c757d; color: white; font-size: 12px; padding: 6px 12px; }
        .clear-btn:hover { background: #545b62; }
      </style>
    </head>
    <body>
      <div class="chat-container">
        <div class="header">
          <a href="/admin" class="admin-link">🔧 Admin Panel</a>
          <h1>⚖️ KanoonPK AI Legal Research</h1>
          <p style="color: #666; margin: 0;">Ask questions about Pakistan law with advanced search filters</p>
        </div>
        
        <div id="messages"></div>
        
        <div class="search-panel">
          <h4 style="margin: 0 0 15px 0; color: #333;">🔍 Advanced Search Filters</h4>
          <div class="search-row">
            <div class="search-field">
              <label for="citationFilter">📑 Citations:</label>
              <input type="text" id="citationFilter" placeholder="e.g., PLD 2020 SC">
            </div>
            <div class="search-field">
              <label for="yearFilter">📅 Year:</label>
              <input type="text" id="yearFilter" placeholder="e.g., 2020">
            </div>
            <div class="search-field">
              <label for="pageFilter">📄 Page:</label>
              <input type="text" id="pageFilter" placeholder="e.g., 123">
            </div>
            <div class="search-field">
              <label for="courtFilter">🏛️ Court:</label>
              <input type="text" id="courtFilter" placeholder="e.g., Supreme Court">
            </div>
          </div>
          <button onclick="clearFilters()" class="clear-btn">🗑️ Clear Filters</button>
        </div>
        
        <div class="input-section">
          <input id="userInput" placeholder="Ask about Pakistan law..." onkeydown="if(event.key==='Enter')sendMessage()">
          <button onclick="sendMessage()" class="send-btn">💬 Send</button>
          <button onclick="downloadPDF()" class="pdf-btn">📄 PDF</button>
        </div>
      </div>

      <script>
        let lastAnswer = "";
        let lastCitations = [];

        async function sendMessage() {
          const input = document.getElementById("userInput");
          const msgBox = document.getElementById("messages");
          const userText = input.value.trim();
          if (!userText) return;

          // Get filter values
          const filters = {
            citation: document.getElementById("citationFilter").value.trim(),
            year: document.getElementById("yearFilter").value.trim(),
            page: document.getElementById("pageFilter").value.trim(),
            court: document.getElementById("courtFilter").value.trim()
          };

          msgBox.innerHTML += `<div class='msg user'>${userText}</div>`;
          input.value = "";
          
          // Show typing indicator
          msgBox.innerHTML += `<div class='msg bot' id='typing'>💭 Thinking...</div>`;
          msgBox.scrollTop = msgBox.scrollHeight;

          try {
            const res = await fetch("/chat", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ message: userText, filters: filters })
            });
            
            if (!res.ok) {
              throw new Error('Network response was not ok');
            }
            
            const data = await res.json();
            
            // Remove typing indicator
            document.getElementById('typing').remove();

            lastAnswer = data.reply;
            lastCitations = data.sources;

            let citationText = data.sources.length ? `<br><small>📑 <strong>Sources:</strong> ${data.sources.join(", ")}</small>` : "";
            let filterInfo = "";
            if (Object.values(filters).some(f => f)) {
              const activeFilters = Object.entries(filters).filter(([k, v]) => v).map(([k, v]) => `${k}: ${v}`).join(", ");
              filterInfo = `<br><small>🔍 <strong>Filters applied:</strong> ${activeFilters}</small>`;
            }
            
            msgBox.innerHTML += `<div class='msg bot'>${data.reply.replace(/\\n/g,"<br>")} ${citationText} ${filterInfo}</div>`;
            msgBox.scrollTop = msgBox.scrollHeight;
          } catch (error) {
            console.error('Chat error:', error);
            document.getElementById('typing').remove();
            msgBox.innerHTML += `<div class='msg bot' style='color: red;'>⚠️ Sorry, there was an error processing your request. Please try again.</div>`;
            msgBox.scrollTop = msgBox.scrollHeight;
          }
        }

        function clearFilters() {
          document.getElementById("citationFilter").value = "";
          document.getElementById("yearFilter").value = "";
          document.getElementById("pageFilter").value = "";
          document.getElementById("courtFilter").value = "";
        }

        async function downloadPDF() {
          if (!lastAnswer) {
            alert("⚠️ No answer to download yet.");
            return;
          }
          try {
            const res = await fetch("/export_pdf", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ text: lastAnswer, citations: lastCitations })
            });
            
            if (!res.ok) {
              throw new Error('Failed to generate PDF');
            }
            
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = "KanoonPK_Answer.pdf";
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
          } catch (error) {
            console.error('PDF download error:', error);
            alert('⚠️ Error generating PDF. Please try again.');
          }
        }
      </script>
    </body>
    </html>
    """)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        file = request.files["file"]
        if file and file.filename:
            filename = secure_filename(file.filename)
            path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(path)
            
            # Get additional metadata from form
            citation = request.form.get("citation", "")
            year = request.form.get("year", "")
            page = request.form.get("page", "")
            court = request.form.get("court", "")
            
            save_to_collection(path, filename, citation, year, page, court)
            return f"<div style='color: green; font-weight: bold; margin: 20px;'>✅ {filename} uploaded & indexed successfully!</div><a href='/admin'>Upload Another</a>"
    
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>KanoonPK Admin Panel</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
            .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .form-group { margin-bottom: 20px; }
            label { display: block; margin-bottom: 5px; font-weight: bold; color: #333; }
            input[type="text"], input[type="file"], select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }
            input[type="submit"] { background: #007BFF; color: white; padding: 12px 30px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
            input[type="submit"]:hover { background: #0056b3; }
            .file-types { font-size: 12px; color: #666; margin-top: 5px; }
            h1 { color: #333; text-align: center; margin-bottom: 30px; }
            .back-link { display: block; text-align: center; margin-top: 20px; color: #007BFF; text-decoration: none; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>⚖️ KanoonPK Admin Panel</h1>
            <form method='POST' enctype='multipart/form-data'>
                <div class="form-group">
                    <label for="file">📁 Select Document:</label>
                    <input type='file' name='file' id='file' accept=".pdf,.docx,.txt,.jpg,.jpeg,.png" required>
                    <div class="file-types">Supported: PDF, DOCX, TXT, JPG, JPEG, PNG</div>
                </div>
                
                <div class="form-group">
                    <label for="citation">📑 Citation/Case Name:</label>
                    <input type='text' name='citation' id='citation' placeholder="e.g., PLD 2020 SC 123">
                </div>
                
                <div class="form-group">
                    <label for="year">📅 Year:</label>
                    <input type='text' name='year' id='year' placeholder="e.g., 2020">
                </div>
                
                <div class="form-group">
                    <label for="page">📄 Page Number:</label>
                    <input type='text' name='page' id='page' placeholder="e.g., 123">
                </div>
                
                <div class="form-group">
                    <label for="court">🏛️ Court:</label>
                    <input type='text' name='court' id='court' placeholder="e.g., Supreme Court of Pakistan">
                </div>
                
                <input type='submit' value='📤 Upload & Index Document'>
            </form>
            <a href='/' class="back-link">← Back to Chat</a>
        </div>
    </body>
    </html>
    """)

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message") if request.json else None
    filters = request.json.get("filters", {}) if request.json else {}
    
    if not user_input:
        return jsonify({"reply": "Please provide a message.", "sources": []})
    
    # Build where clause for filtering
    where_clause = {}
    if filters.get("citation"):
        where_clause["citation"] = {"$contains": filters["citation"]}
    if filters.get("year"):
        where_clause["year"] = {"$contains": filters["year"]}
    if filters.get("page"):
        where_clause["page"] = {"$contains": filters["page"]}
    if filters.get("court"):
        where_clause["court"] = {"$contains": filters["court"]}
    
    # Query with or without filters
    if where_clause:
        results = collection.query(
            query_texts=[user_input], 
            n_results=5,
            where=where_clause
        )
    else:
        results = collection.query(query_texts=[user_input], n_results=3)
    
    context = ""
    citations_used = []
    
    if results["documents"] and results["documents"][0]:
        for i, doc in enumerate(results["documents"][0]):
            metadata = results["metadatas"][0][i]
            citation = metadata.get("citation", metadata.get("source", "Unknown"))
            year = metadata.get("year", "")
            page = metadata.get("page", "")
            court = metadata.get("court", "")
            
            # Build citation display
            citation_display = citation
            if year or page or court:
                details = []
                if year: details.append(f"Year: {year}")
                if page: details.append(f"Page: {page}")
                if court: details.append(f"Court: {court}")
                citation_display += f" ({', '.join(details)})"
            
            citations_used.append(citation_display)
            context += f"\n\n[Citation: {citation_display}] {doc[:800]}..."
    
    if not context:
        return jsonify({
            "reply": "No relevant documents found matching your query and filters. Try adjusting your search terms or filters.",
            "sources": []
        })

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
    text = data.get("text", "") if data else ""
    citations = data.get("citations", []) if data else []

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
    app.run(host="0.0.0.0", port=5000, debug=True)
