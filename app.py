import os
import uuid
import json
import datetime
import logging
from flask import Flask, request, jsonify, render_template, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
from openai import OpenAI
import chromadb
from chromadb.utils import embedding_functions
from PyPDF2 import PdfReader
from docx import Document
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Flask
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "fallback-secret-key")
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Initialize OpenAI
# the newest OpenAI model is "gpt-5" which was released August 7, 2025.
# do not change this unless explicitly requested by the user
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize ChromaDB
try:
    chroma_client = chromadb.PersistentClient(path="chroma_db")
    embedding_func = embedding_functions.OpenAIEmbeddingFunction(
        api_key=os.getenv("OPENAI_API_KEY"),
        model_name="text-embedding-3-small"
    )
    try:
        collection = chroma_client.get_collection("kanoonpk")
    except:
        collection = chroma_client.create_collection("kanoonpk", embedding_function=embedding_func)
    logging.info("ChromaDB initialized successfully")
except Exception as e:
    logging.error(f"Failed to initialize ChromaDB: {e}")
    collection = None

LEGAL_SYSTEM_PROMPT = """
You are KanoonPK, an AI Legal Research Assistant specialized in Pakistan law.
You must answer only based on Pakistan's laws, case references, and uploaded legal documents.
Always provide specific citations when available from the retrieved documents.
If you cannot find relevant information in the provided context, clearly state that you don't have sufficient information.
Focus on accuracy and cite specific sections, cases, or document references when possible.
"""

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ----------------------------
# File Processing Functions
# ----------------------------
def extract_text_from_pdf(path):
    try:
        reader = PdfReader(path)
        text_content = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_content.append(page_text)
        return "\n".join(text_content)
    except Exception as e:
        logging.error(f"Error extracting text from PDF {path}: {e}")
        raise

def extract_text_from_docx(path):
    try:
        doc = Document(path)
        return "\n".join([paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip()])
    except Exception as e:
        logging.error(f"Error extracting text from DOCX {path}: {e}")
        raise

def save_to_collection(file_path, filename):
    if not collection:
        raise Exception("ChromaDB collection not initialized")
    
    try:
        if filename.lower().endswith(".pdf"):
            text = extract_text_from_pdf(file_path)
        elif filename.lower().endswith(".docx"):
            text = extract_text_from_docx(file_path)
        else:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()

        if not text.strip():
            raise Exception("No text content found in file")

        # Create chunks of text for better searchability
        chunk_size = 1000
        overlap = 200
        chunks = []
        for i in range(0, len(text), chunk_size - overlap):
            chunk = text[i:i + chunk_size]
            if chunk.strip():
                chunks.append(chunk)

        if not chunks:
            raise Exception("No valid text chunks created")

        # Generate unique IDs and metadata
        ids = [f"{filename}_{i}_{str(uuid.uuid4())[:8]}" for i in range(len(chunks))]
        metadatas = [{"source": filename, "citation": filename, "chunk_id": i} for i in range(len(chunks))]
        
        # Add to collection
        collection.add(
            documents=chunks,
            metadatas=metadatas,
            ids=ids
        )
        
        logging.info(f"Successfully indexed {len(chunks)} chunks from {filename}")
        return len(chunks)
        
    except Exception as e:
        logging.error(f"Error saving {filename} to collection: {e}")
        raise

# ----------------------------
# Routes
# ----------------------------

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            try:
                filename = secure_filename(file.filename)
                # Add timestamp to prevent conflicts
                name, ext = os.path.splitext(filename)
                filename = f"{name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
                
                file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(file_path)
                
                chunks_count = save_to_collection(file_path, filename)
                flash(f'Successfully uploaded and indexed "{filename}" ({chunks_count} chunks)', 'success')
                
            except Exception as e:
                flash(f'Error processing file: {str(e)}', 'error')
                logging.error(f"File upload error: {e}")
        else:
            flash('Invalid file type. Please upload PDF, DOCX, or TXT files only.', 'error')
        
        return redirect(url_for('admin'))
    
    return render_template("admin.html")

@app.route("/chat", methods=["POST"])
def chat():
    try:
        user_input = request.json.get("message", "").strip()
        if not user_input:
            return jsonify({"error": "No message provided"}), 400

        if not collection:
            return jsonify({"error": "Document collection not available"}), 500

        # Query the collection for relevant documents
        results = collection.query(query_texts=[user_input], n_results=5)
        
        context = ""
        citations_used = []
        
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                if i < len(results["metadatas"][0]):
                    citation = results["metadatas"][0][i]["citation"]
                    if citation not in citations_used:
                        citations_used.append(citation)
                    
                    # Truncate document for context
                    doc_excerpt = doc[:800] + "..." if len(doc) > 800 else doc
                    context += f"\n\n[Source: {citation}] {doc_excerpt}"

        # Generate response using OpenAI
        messages = [
            {"role": "system", "content": LEGAL_SYSTEM_PROMPT},
            {"role": "user", "content": f"Question: {user_input}\n\nRelevant Documents:{context}"}
        ]
        
        response = client.chat.completions.create(
            model="gpt-5",  # Using latest model
            messages=messages,
            max_completion_tokens=1500
        )
        
        reply = response.choices[0].message.content

        # Log the interaction
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "question": user_input,
            "reply": reply,
            "citations": citations_used,
            "context_length": len(context)
        }
        
        os.makedirs("logs", exist_ok=True)
        history_file = "logs/history.json"
        
        try:
            if os.path.exists(history_file):
                with open(history_file, "r", encoding="utf-8") as f:
                    history = json.load(f)
            else:
                history = []
            
            history.append(log_entry)
            
            # Keep only last 1000 entries
            if len(history) > 1000:
                history = history[-1000:]
            
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Error logging interaction: {e}")

        return jsonify({
            "reply": reply,
            "sources": citations_used,
            "timestamp": log_entry["timestamp"]
        })

    except Exception as e:
        logging.error(f"Chat error: {e}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route("/history")
def history():
    history_file = "logs/history.json"
    
    if not os.path.exists(history_file):
        return render_template("history.html", history=[])
    
    try:
        with open(history_file, "r", encoding="utf-8") as f:
            history_data = json.load(f)
        
        # Return last 50 entries, most recent first
        recent_history = list(reversed(history_data[-50:]))
        return render_template("history.html", history=recent_history)
        
    except Exception as e:
        logging.error(f"Error loading history: {e}")
        return render_template("history.html", history=[], error="Error loading history")

@app.route("/export_pdf", methods=["POST"])
def export_pdf():
    try:
        data = request.json
        text = data.get("text", "")
        citations = data.get("citations", [])
        question = data.get("question", "Legal Research Query")
        
        if not text:
            return jsonify({"error": "No text to export"}), 400

        # Create exports directory
        os.makedirs("exports", exist_ok=True)
        filename = f"exports/KanoonPK_Answer_{uuid.uuid4().hex[:8]}.pdf"
        
        # Create PDF
        c = canvas.Canvas(filename, pagesize=A4)
        width, height = A4
        
        # Add watermark
        c.setFont("Helvetica-Bold", 50)
        c.setFillGray(0.95)
        c.saveState()
        c.translate(width/2, height/2)
        c.rotate(45)
        c.drawCentredString(0, 0, "KanoonPK")
        c.restoreState()
        
        # Reset for content
        c.setFillColor(colors.black)
        y = height - 60
        
        # Header
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, y, "KanoonPK Legal Research Assistant")
        y -= 30
        
        c.setFont("Helvetica", 10)
        c.drawString(50, y, f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        y -= 40
        
        # Question section
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Question:")
        y -= 20
        
        c.setFont("Helvetica", 11)
        # Word wrap for question
        question_lines = []
        words = question.split()
        line = ""
        for word in words:
            if c.stringWidth(line + " " + word) < width - 100:
                line += " " + word if line else word
            else:
                question_lines.append(line)
                line = word
        if line:
            question_lines.append(line)
            
        for line in question_lines:
            c.drawString(50, y, line)
            y -= 15
        
        y -= 20
        
        # Citations banner
        if citations:
            c.setFillColor(colors.HexColor("#007BFF"))
            c.rect(40, y-25, width-80, 25, fill=1)
            c.setFillColor(colors.white)
            c.setFont("Helvetica-Bold", 10)
            citations_text = "Sources: " + ", ".join(citations)
            c.drawString(50, y-15, citations_text)
            y -= 40
        
        # Answer section
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Answer:")
        y -= 25
        
        c.setFont("Helvetica", 10)
        
        # Process text with word wrapping
        paragraphs = text.split('\n')
        for paragraph in paragraphs:
            if not paragraph.strip():
                y -= 10
                continue
                
            words = paragraph.split()
            line = ""
            
            for word in words:
                test_line = line + " " + word if line else word
                if c.stringWidth(test_line) < width - 100:
                    line = test_line
                else:
                    if line:
                        c.drawString(50, y, line)
                        y -= 12
                        line = word
                    else:
                        # Word too long, force break
                        c.drawString(50, y, word)
                        y -= 12
                
                # Check for page break
                if y < 80:
                    c.showPage()
                    y = height - 80
                    c.setFont("Helvetica", 10)
            
            # Draw remaining line
            if line:
                c.drawString(50, y, line)
                y -= 12
            
            y -= 5  # Paragraph spacing
            
            # Check for page break
            if y < 80:
                c.showPage()
                y = height - 80
                c.setFont("Helvetica", 10)
        
        c.save()
        return send_file(filename, as_attachment=True, download_name="KanoonPK_Answer.pdf")
        
    except Exception as e:
        logging.error(f"PDF export error: {e}")
        return jsonify({"error": f"PDF export failed: {str(e)}"}), 500

@app.errorhandler(413)
def too_large(e):
    flash("File too large. Maximum file size is 16MB.", "error")
    return redirect(url_for('admin'))

@app.errorhandler(404)
def not_found(e):
    return render_template("index.html"), 404

@app.errorhandler(500)
def server_error(e):
    logging.error(f"Server error: {e}")
    flash("An internal server error occurred. Please try again.", "error")
    return render_template("index.html"), 500
