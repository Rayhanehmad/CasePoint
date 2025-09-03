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
Answer based on the provided documents and Pakistan's laws, case references.
Always provide citations if available from the documents.
"""

GENERAL_LEGAL_PROMPT = """
You are KanoonPK, an AI Legal Research Assistant specialized in Pakistan law.
Since no specific documents were found for this query, use your knowledge of Pakistan law to provide accurate information.
Focus on:
- Constitution of Pakistan 1973
- Pakistan Penal Code
- Civil Procedure Code
- Criminal Procedure Code
- Contract Act 1872
- Companies Act 2017
- Other relevant Pakistan legal statutes

Always mention that this answer is based on general legal knowledge and suggest uploading specific documents for more detailed analysis.
"""

# ----------------------------
# File processing
# ----------------------------
def get_uploaded_documents():
    """Get list of uploaded documents from ChromaDB"""
    try:
        # Get all documents from collection
        all_docs = collection.get()
        
        # Group by source file to avoid duplicates from chunks
        documents = {}
        for i, metadata in enumerate(all_docs['metadatas']):
            source = metadata.get('source', 'Unknown')
            if source not in documents:
                documents[source] = {
                    'filename': source,
                    'citation': metadata.get('citation', ''),
                    'year': metadata.get('year', ''),
                    'page': metadata.get('page', ''),
                    'court': metadata.get('court', ''),
                    'chunks': 1
                }
            else:
                documents[source]['chunks'] += 1
        
        return list(documents.values())
    except Exception as e:
        print(f"Error getting documents: {e}")
        return []

def process_pdf(path):
    try:
        reader = PdfReader(path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return f"Error processing PDF: {e}"

def process_docx(path):
    try:
        doc = Document(path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        return f"Error processing DOCX: {e}"

def extract_text(file_path):
    """Extract text from uploaded file"""
    ext = file_path.lower().split('.')[-1]
    if ext == 'pdf':
        return process_pdf(file_path)
    elif ext == 'docx':
        return process_docx(file_path)
    elif ext == 'txt':
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    else:
        return "Unsupported file format"

def save_to_collection(file_path, filename, citation="", year="", page="", court=""):
    """Save document chunks to ChromaDB"""
    text = extract_text(file_path)
    
    # Split into chunks (1000 characters each with 200 char overlap)
    chunk_size = 1000
    overlap = 200
    chunks = []
    
    for i in range(0, len(text), chunk_size - overlap):
        chunk = text[i:i + chunk_size]
        if chunk.strip():
            chunks.append({
                "text": chunk,
                "metadata": {
                    "source": filename,
                    "citation": citation,
                    "year": year,
                    "page": page,
                    "court": court,
                    "chunk_id": len(chunks)
                }
            })
    
    # Add to collection
    try:
        collection.add(
            documents=[chunk["text"] for chunk in chunks],
            metadatas=[chunk["metadata"] for chunk in chunks],
            ids=[f"{filename}_chunk_{i}" for i in range(len(chunks))]
        )
        return f"Successfully added {len(chunks)} chunks from {filename}"
    except Exception as e:
        return f"Error saving to database: {e}"

# ----------------------------
# Routes
# ----------------------------
@app.route("/")
def index():
    return render_template_string("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KanoonPK - AI Legal Research Assistant</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
            font-size: 13px;
        }
        
        .container {
            max-width: 100vw;
            height: 100vh;
            display: flex;
            flex-direction: column;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
        }
        
        .header {
            background: linear-gradient(135deg, #4dd0b7, #36a085);
            color: white;
            padding: 8px 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .header .logo {
            height: 30px;
            width: auto;
        }
        
        .user-profile {
            display: flex;
            align-items: center;
            gap: 8px;
            cursor: pointer;
            padding: 4px 8px;
            border-radius: 20px;
            transition: background 0.3s;
        }
        
        .user-profile:hover {
            background: rgba(255,255,255,0.2);
        }
        
        .user-avatar {
            width: 25px;
            height: 25px;
            border-radius: 50%;
        }
        
        .user-name {
            font-size: 12px;
            font-weight: 600;
        }
        
        .admin-link {
            color: white;
            text-decoration: none;
            font-size: 11px;
            margin-left: 10px;
        }
        
        .search-banner {
            background: linear-gradient(45deg, #ff9a56, #ffad56);
            color: white;
            padding: 8px 15px;
            cursor: pointer;
            font-weight: 600;
            text-align: center;
            font-size: 12px;
            transition: all 0.3s;
        }
        
        .search-banner:hover {
            background: linear-gradient(45deg, #ff8a46, #ff9d46);
        }
        
        .search-content {
            background: #f8f9fa;
            padding: 0;
            max-height: 0;
            overflow: hidden;
            transition: all 0.3s;
            border-bottom: 1px solid #eee;
        }
        
        .search-content.open {
            max-height: 200px;
            padding: 10px 15px;
        }
        
        .search-fields {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
        }
        
        .search-field label {
            display: block;
            font-size: 10px;
            font-weight: 600;
            margin-bottom: 3px;
            color: #666;
        }
        
        .search-field input {
            width: 100%;
            padding: 6px 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 11px;
        }
        
        .search-actions {
            margin-top: 8px;
            text-align: center;
        }
        
        .clear-btn {
            background: #dc3545;
            color: white;
            border: none;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 10px;
            cursor: pointer;
        }
        
        .messages {
            flex: 1;
            overflow-y: auto;
            padding: 10px;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        
        .msg {
            max-width: 85%;
            padding: 8px 12px;
            border-radius: 12px;
            font-size: 12px;
            line-height: 1.4;
            position: relative;
            transition: all 0.3s;
        }
        
        .msg.user {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            align-self: flex-end;
            border-bottom-right-radius: 4px;
        }
        
        .msg.bot {
            background: #f1f3f4;
            color: #333;
            align-self: flex-start;
            border-bottom-left-radius: 4px;
            border-left: 3px solid #4dd0b7;
        }
        
        .msg.selecting {
            margin-left: 25px;
        }
        
        .msg-checkbox {
            position: absolute;
            left: -20px;
            top: 50%;
            transform: translateY(-50%);
            display: none;
        }
        
        .msg.selecting .msg-checkbox {
            display: block;
        }
        
        .message-time {
            font-size: 9px;
            opacity: 0.7;
            margin-top: 4px;
        }
        
        .sources {
            margin-top: 6px;
            padding: 6px 8px;
            background: rgba(77, 208, 183, 0.1);
            border-radius: 6px;
            font-size: 10px;
            color: #666;
        }
        
        .controls {
            padding: 8px 15px;
            background: #f8f9fa;
            border-top: 1px solid #eee;
            display: flex;
            gap: 6px;
            align-items: center;
        }
        
        .control-group {
            display: flex;
            gap: 4px;
        }
        
        .control-btn {
            background: #6c757d;
            color: white;
            border: none;
            padding: 6px 10px;
            border-radius: 6px;
            font-size: 10px;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .control-btn:hover {
            background: #5a6268;
        }
        
        .control-btn.active {
            background: #4dd0b7;
        }
        
        .bulk-actions {
            display: none;
            gap: 4px;
        }
        
        .bulk-actions.active {
            display: flex;
        }
        
        .input-section {
            padding: 10px 15px;
            background: white;
            border-top: 1px solid #eee;
            display: flex;
            gap: 8px;
            align-items: center;
        }
        
        .file-upload-btn {
            background: #ffc107;
            color: #333;
            border: none;
            padding: 8px 10px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
        }
        
        .file-input {
            display: none;
        }
        
        #userInput {
            flex: 1;
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 20px;
            font-size: 12px;
            outline: none;
        }
        
        .send-btn {
            background: linear-gradient(135deg, #4dd0b7, #36a085);
            color: white;
            border: none;
            padding: 8px 15px;
            border-radius: 20px;
            cursor: pointer;
            font-size: 11px;
            font-weight: 600;
        }
        
        .pdf-btn {
            background: #dc3545;
            color: white;
            border: none;
            padding: 8px 12px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 10px;
        }
        
        .export-dropdown {
            position: relative;
        }
        
        .export-menu {
            position: absolute;
            bottom: 100%;
            right: 0;
            background: white;
            border: 1px solid #ddd;
            border-radius: 6px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            min-width: 120px;
            display: none;
        }
        
        .export-menu.show {
            display: block;
        }
        
        .export-option {
            padding: 8px 12px;
            cursor: pointer;
            font-size: 11px;
            border-bottom: 1px solid #eee;
        }
        
        .export-option:hover {
            background: #f8f9fa;
        }
        
        .export-option:last-child {
            border-bottom: none;
        }
        
        .typing {
            opacity: 0.7;
        }
        
        .admin-protected {
            display: none;
        }
        
        body.admin-user .admin-protected {
            display: inline;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <img src="/static/images/kanoonpk-logo.jpg" alt="KanoonPK Logo" class="logo">
            <div class="user-profile" id="userProfile">
                <img src="https://ui-avatars.com/api/?name=Legal+User&background=4dd0b7&color=fff&size=25" alt="User Avatar" class="user-avatar" id="userAvatar">
                <span class="user-name" id="userName">Legal User</span>
                <a href="/admin" class="admin-link admin-protected">🔧 Admin Panel</a>
            </div>
        </div>
        
        <div class="search-banner" onclick="toggleSearch()">
            🔍 Advanced Search Filters - Click to Expand
        </div>
        
        <div class="search-content" id="searchContent">
            <div class="search-fields">
                <div class="search-field">
                    <label for="citationFilter">📑 Citation:</label>
                    <input type="text" id="citationFilter" placeholder="e.g., PLD 2020 SC 123">
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
            <div class="search-actions">
                <button onclick="clearFilters()" class="clear-btn">🗑️ Clear Filters</button>
            </div>
        </div>
        
        <div class="controls">
            <div class="control-group">
                <button onclick="toggleSelectMode()" class="control-btn" id="selectModeBtn">☑️ Select</button>
                <button onclick="clearChat()" class="control-btn">🗑️ Clear</button>
                <div class="export-dropdown">
                    <button onclick="toggleExportMenu()" class="control-btn">📤 Export</button>
                    <div class="export-menu" id="exportMenu">
                        <div class="export-option" onclick="exportChat('txt')">📄 Export as TXT</div>
                        <div class="export-option" onclick="exportChat('pdf')">📁 Export as PDF</div>
                        <div class="export-option" onclick="exportChat('json')">📊 Export as JSON</div>
                        <div class="export-option" onclick="exportSelectedMessages()">☑️ Export Selected</div>
                    </div>
                </div>
            </div>
            <div class="bulk-actions" id="bulkActions">
                <button onclick="deleteSelected()" class="control-btn">🗑️ Delete Selected</button>
                <button onclick="forwardSelected()" class="control-btn">📧 Forward Selected</button>
                <button onclick="cancelSelection()" class="control-btn">❌ Cancel</button>
            </div>
        </div>
        
        <div class="messages" id="messages">
            <div class="msg bot">
                <div class="msg-checkbox"><input type="checkbox" onchange="updateSelection()"></div>
                🙏 Welcome to KanoonPK! I am your AI legal research assistant for Pakistan law. Ask me about legal cases, statutes, or upload documents for analysis.
                <div class="message-time">Online</div>
            </div>
        </div>
        
        <div class="input-section">
            <input type="file" id="documentInput" class="file-input" accept=".pdf,.docx,.txt" onchange="handleFileUpload()">
            <button onclick="document.getElementById('documentInput').click()" class="file-upload-btn" title="Upload Document for Analysis">📁</button>
            <input id="userInput" placeholder="Ask about Pakistan law..." onkeydown="handleKeyPress(event)">
            <button onclick="sendMessage()" class="send-btn">💬 Send</button>
            <button onclick="downloadPDF()" class="pdf-btn">📄 PDF</button>
        </div>
    </div>

    <script>
        // Global variables
        let lastAnswer = "";
        let lastCitations = [];
        let isSelectMode = false;
        let messageIdCounter = 0;
        
        // Utility functions
        function getCurrentTime() {
            const now = new Date();
            return now.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        }
        
        function addMessage(content, isUser = false, isTyping = false) {
            const msgBox = document.getElementById("messages");
            const messageDiv = document.createElement('div');
            const time = getCurrentTime();
            const msgId = 'msg_' + (++messageIdCounter);
            
            messageDiv.className = 'msg ' + (isUser ? 'user' : 'bot') + (isTyping ? ' typing' : '') + (isSelectMode ? ' selecting' : '');
            messageDiv.setAttribute('data-msg-id', msgId);
            
            const checkboxHtml = '<div class="msg-checkbox"><input type="checkbox" onchange="updateSelection()"></div>';
            
            if (isTyping) {
                messageDiv.id = 'typing';
                messageDiv.innerHTML = checkboxHtml + content;
            } else {
                messageDiv.innerHTML = checkboxHtml + content + '<div class="message-time">' + time + '</div>';
            }
            
            msgBox.appendChild(messageDiv);
            
            // Smooth scroll to bottom
            setTimeout(function() {
                msgBox.scrollTop = msgBox.scrollHeight;
            }, 50);
            
            return messageDiv;
        }
        
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }
        
        async function sendMessage() {
            const input = document.getElementById("userInput");
            const userText = input.value.trim();
            if (!userText) return;

            // Get filter values
            const filters = {
                citation: document.getElementById("citationFilter").value.trim(),
                year: document.getElementById("yearFilter").value.trim(),
                page: document.getElementById("pageFilter").value.trim(),
                court: document.getElementById("courtFilter").value.trim()
            };

            // Add user message
            addMessage(userText, true);
            input.value = "";
            
            // Show typing indicator
            const typingMsg = addMessage('💭 KanoonPK is analyzing your query...', false, true);

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
                typingMsg.remove();

                lastAnswer = data.reply;
                lastCitations = data.sources;

                // Build bot response
                let content = data.reply.split('\\n').join('<br>');
                
                if (data.sources.length) {
                    content += '<div class="sources"><strong>📑 Legal Sources:</strong> ' + data.sources.join(", ") + '</div>';
                }
                
                if (Object.values(filters).some(f => f)) {
                    const activeFilters = Object.entries(filters).filter(([k, v]) => v).map(([k, v]) => k + ': ' + v).join(", ");
                    content += '<div class="sources"><strong>🔍 Search Filters:</strong> ' + activeFilters + '</div>';
                }
                
                addMessage(content);
                
            } catch (error) {
                console.error('Chat error:', error);
                if (typingMsg && typingMsg.parentNode) {
                    typingMsg.remove();
                }
                addMessage('⚠️ Sorry, there was an error processing your request. Please try again.', false);
            }
        }

        function toggleSearch() {
            const searchContent = document.getElementById('searchContent');
            searchContent.classList.toggle('open');
        }

        function clearFilters() {
            document.getElementById("citationFilter").value = "";
            document.getElementById("yearFilter").value = "";
            document.getElementById("pageFilter").value = "";
            document.getElementById("courtFilter").value = "";
        }
        
        function clearChat() {
            if (confirm('Are you sure you want to clear all messages? This action cannot be undone.')) {
                const msgBox = document.getElementById('messages');
                msgBox.innerHTML = '<div class="msg bot">' +
                    '<div class="msg-checkbox"><input type="checkbox" onchange="updateSelection()"></div>' +
                    '🙏 Welcome to KanoonPK! I am your AI legal research assistant for Pakistan law. Ask me about legal cases, statutes, or upload documents for analysis.' +
                    '<div class="message-time">Online</div>' +
                    '</div>';
                messageIdCounter = 0;
                if (isSelectMode) {
                    toggleSelectMode();
                }
            }
        }
        
        function toggleSelectMode() {
            const selectBtn = document.getElementById('selectModeBtn');
            const bulkActions = document.getElementById('bulkActions');
            const messages = document.querySelectorAll('.msg');
            
            isSelectMode = !isSelectMode;
            
            if (isSelectMode) {
                selectBtn.classList.add('active');
                selectBtn.innerHTML = '☑️ Selecting...';
                bulkActions.classList.add('active');
                messages.forEach(function(msg) {
                    msg.classList.add('selecting');
                    const checkbox = msg.querySelector('input[type="checkbox"]');
                    if (checkbox) checkbox.checked = false;
                });
            } else {
                selectBtn.classList.remove('active');
                selectBtn.innerHTML = '☑️ Select';
                bulkActions.classList.remove('active');
                messages.forEach(function(msg) {
                    msg.classList.remove('selecting', 'selected');
                    const checkbox = msg.querySelector('input[type="checkbox"]');
                    if (checkbox) checkbox.checked = false;
                });
            }
        }
        
        function updateSelection() {
            const messages = document.querySelectorAll('.msg');
            messages.forEach(function(msg) {
                const checkbox = msg.querySelector('input[type="checkbox"]');
                if (checkbox && checkbox.checked) {
                    msg.classList.add('selected');
                } else {
                    msg.classList.remove('selected');
                }
            });
        }
        
        function deleteSelected() {
            const selectedMessages = document.querySelectorAll('.msg input[type="checkbox"]:checked');
            if (selectedMessages.length === 0) {
                alert('Please select messages to delete.');
                return;
            }
            
            if (confirm('Delete ' + selectedMessages.length + ' selected message(s)?')) {
                selectedMessages.forEach(function(checkbox) {
                    const msgElement = checkbox.closest('.msg');
                    msgElement.remove();
                });
                updateSelection();
            }
        }
        
        function forwardSelected() {
            const selectedMessages = document.querySelectorAll('.msg input[type="checkbox"]:checked');
            if (selectedMessages.length === 0) {
                alert('Please select messages to forward.');
                return;
            }
            
            let forwardText = 'Forwarded Messages:\\n\\n';
            selectedMessages.forEach(function(checkbox) {
                const msgElement = checkbox.closest('.msg');
                let msgContent = msgElement.textContent;
                msgContent = msgContent.split('Online').join('');
                msgContent = msgContent.trim();
                const isUser = msgElement.classList.contains('user');
                forwardText += (isUser ? 'You' : 'KanoonPK') + ': ' + msgContent + '\\n\\n';
            });
            
            // Copy to clipboard
            navigator.clipboard.writeText(forwardText).then(function() {
                alert(selectedMessages.length + ' message(s) copied to clipboard!');
            }).catch(function() {
                // Fallback: show in alert
                prompt('Copy this text to forward:', forwardText);
            });
        }
        
        function cancelSelection() {
            if (isSelectMode) {
                toggleSelectMode();
            }
        }
        
        async function handleFileUpload() {
            const fileInput = document.getElementById('documentInput');
            const file = fileInput.files[0];
            
            if (!file) return;
            
            // Show upload progress
            const uploadMsg = addMessage('📁 Uploading and analyzing: ' + file.name + '...', false, true);
            
            const formData = new FormData();
            formData.append('file', file);
            
            try {
                const response = await fetch('/upload-and-analyze', {
                    method: 'POST',
                    body: formData
                });
                
                if (!response.ok) {
                    throw new Error('Upload failed');
                }
                
                const result = await response.json();
                
                // Remove upload progress
                uploadMsg.remove();
                
                // Add analysis result
                addMessage('📄 Document uploaded and indexed successfully!<br><strong>File:</strong> ' + file.name + '<br><strong>Analysis:</strong> ' + (result.summary || 'Document processed and ready for queries.'));
                
                // Clear file input
                fileInput.value = '';
                
            } catch (error) {
                console.error('Upload error:', error);
                uploadMsg.remove();
                addMessage('❌ Error uploading document. Please try again.', false);
            }
        }
        
        // Check if user is admin and update UI
        function checkAdminStatus() {
            const userName = localStorage.getItem('userName') || 'Legal User';
            const isAdmin = localStorage.getItem('isAdmin') === 'true';
            
            const userNameEl = document.getElementById('userName');
            const userAvatarEl = document.getElementById('userAvatar');
            
            if (userNameEl) {
                userNameEl.textContent = userName;
            }
            if (userAvatarEl) {
                userAvatarEl.src = 'https://ui-avatars.com/api/?name=' + encodeURIComponent(userName) + '&background=4dd0b7&color=fff&size=25';
            }
            
            if (isAdmin) {
                document.body.classList.add('admin-user');
            } else {
                document.body.classList.remove('admin-user');
            }
        }
        
        function toggleExportMenu() {
            const menu = document.getElementById('exportMenu');
            menu.classList.toggle('show');
            
            // Close menu when clicking outside
            document.addEventListener('click', function(e) {
                if (!e.target.closest('.export-dropdown')) {
                    menu.classList.remove('show');
                }
            });
        }
        
        function collectChatMessages(selectedOnly = false) {
            const messages = [];
            const msgElements = selectedOnly ? 
                document.querySelectorAll('.msg input[type="checkbox"]:checked') :
                document.querySelectorAll('.msg');
            
            (selectedOnly ? 
                Array.from(msgElements).map(cb => cb.closest('.msg')) :
                Array.from(msgElements)
            ).forEach(function(msg) {
                const isUser = msg.classList.contains('user');
                const timeElement = msg.querySelector('.message-time');
                const time = timeElement ? timeElement.textContent : getCurrentTime();
                
                // Extract message content
                let content = msg.textContent.replace(time, '').trim();
                content = content.replace(/[^a-zA-Z0-9 .,!?;:()-]/g, '');
                content = content.trim();
                
                if (content && !msg.classList.contains('typing')) {
                    messages.push({
                        type: isUser ? 'user' : 'bot',
                        content: content,
                        timestamp: time,
                        id: msg.getAttribute('data-msg-id') || 'unknown'
                    });
                }
            });
            
            return messages;
        }
        
        async function exportChat(format) {
            document.getElementById('exportMenu').classList.remove('show');
            
            const messages = collectChatMessages();
            if (messages.length === 0) {
                alert('No messages to export.');
                return;
            }
            
            try {
                const response = await fetch('/export-chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ messages: messages, format: format })
                });
                
                if (!response.ok) {
                    throw new Error('Export failed');
                }
                
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                
                const timestamp = new Date().toISOString().slice(0, 19).split(':').join('-');
                const filename = 'KanoonPK_Chat_' + timestamp + '.' + format;
                
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(url);
                
                addMessage('✅ Chat exported as ' + format.toUpperCase() + ' successfully!', false);
                
            } catch (error) {
                console.error('Export error:', error);
                addMessage('❌ Error exporting chat. Please try again.', false);
            }
        }
        
        async function exportSelectedMessages() {
            document.getElementById('exportMenu').classList.remove('show');
            
            const selectedMessages = collectChatMessages(true);
            if (selectedMessages.length === 0) {
                alert('Please select messages to export.');
                return;
            }
            
            const format = prompt('Export format (txt, pdf, json):', 'txt');
            if (!format || !['txt', 'pdf', 'json'].includes(format.toLowerCase())) {
                return;
            }
            
            try {
                const response = await fetch('/export-chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ messages: selectedMessages, format: format.toLowerCase() })
                });
                
                if (!response.ok) {
                    throw new Error('Export failed');
                }
                
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                
                const timestamp = new Date().toISOString().slice(0, 19).split(':').join('-');
                const filename = 'KanoonPK_Selected_' + timestamp + '.' + format;
                
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(url);
                
                addMessage('✅ Selected messages exported as ' + format.toUpperCase() + ' successfully!', false);
                
            } catch (error) {
                console.error('Export error:', error);
                addMessage('❌ Error exporting selected messages. Please try again.', false);
            }
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
        
        // Initialize when DOM is ready
        document.addEventListener('DOMContentLoaded', function() {
            checkAdminStatus();
            
            // Click name to customize user profile
            const userNameEl = document.getElementById('userName');
            if (userNameEl) {
                userNameEl.addEventListener('click', function() {
                    const newName = prompt('Enter your name:', this.textContent);
                    if (newName && newName.trim()) {
                        localStorage.setItem('userName', newName.trim());
                        const makeAdmin = confirm('Are you an admin user?');
                        localStorage.setItem('isAdmin', makeAdmin.toString());
                        checkAdminStatus();
                    }
                });
            }
        });
    </script>
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
        results = collection.query(query_texts=[user_input], n_results=5)
    
    # Process results
    context = ""
    sources = []
    
    if results["documents"] and results["documents"][0]:
        for i, doc in enumerate(results["documents"][0]):
            context += f"Document {i+1}: {doc}\\n\\n"
            
            # Get source info
            metadata = results["metadatas"][0][i] if results["metadatas"] and results["metadatas"][0] else {}
            source_info = metadata.get("source", "Unknown source")
            if metadata.get("citation"):
                source_info = metadata["citation"]
            elif metadata.get("year"):
                source_info += f" ({metadata['year']})"
            
            if source_info not in sources:
                sources.append(source_info)
    
    # Prepare system prompt
    if context:
        system_prompt = LEGAL_SYSTEM_PROMPT + f"\\n\\nRelevant context from uploaded documents:\\n{context}"
    else:
        system_prompt = GENERAL_LEGAL_PROMPT
    
    try:
        # the newest OpenAI model is "gpt-5" which was released August 7, 2025.
        # do not change this unless explicitly requested by the user
        response = client.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            max_completion_tokens=1500
        )
        
        ai_reply = response.choices[0].message.content
        
        # Save to history
        timestamp = datetime.datetime.now().isoformat()
        history_entry = {
            "timestamp": timestamp,
            "question": user_input,
            "reply": ai_reply,
            "sources": sources,
            "citations": sources
        }
        
        # Save to file
        os.makedirs("logs", exist_ok=True)
        history_file = "logs/history.json"
        
        try:
            with open(history_file, "r") as f:
                history = json.load(f)
        except:
            history = []
        
        history.append(history_entry)
        
        with open(history_file, "w") as f:
            json.dump(history, f, indent=2)
        
        return jsonify({
            "reply": ai_reply,
            "sources": sources
        })
        
    except Exception as e:
        return jsonify({
            "reply": f"I apologize, but I encountered an error while processing your request: {str(e)}",
            "sources": []
        })

@app.route("/upload-and-analyze", methods=["POST"])
def upload_and_analyze():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Process and save to collection
        result = save_to_collection(filepath, filename)
        
        return jsonify({
            "message": "File uploaded and analyzed successfully",
            "filename": filename,
            "summary": result
        })

@app.route("/export-chat", methods=["POST"])
def export_chat():
    try:
        data = request.json
        messages = data.get('messages', [])
        format_type = data.get('format', 'txt')
        
        if not messages:
            return jsonify({'error': 'No messages to export'}), 400
        
        # Create exports directory
        os.makedirs("exports", exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format_type == 'txt':
            filename = f"exports/chat_export_{timestamp}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("KanoonPK Chat Export\\n")
                f.write("=" * 50 + "\\n\\n")
                f.write(f"Exported: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n")
                f.write(f"Total Messages: {len(messages)}\\n\\n")
                
                for msg in messages:
                    sender = "You" if msg['type'] == 'user' else "KanoonPK"
                    f.write(f"[{msg['timestamp']}] {sender}: {msg['content']}\\n\\n")
            
            return send_file(filename, as_attachment=True, download_name=f"KanoonPK_Chat_{timestamp}.txt")
        
        elif format_type == 'json':
            export_data = {
                'export_info': {
                    'exported_at': datetime.datetime.now().isoformat(),
                    'total_messages': len(messages)
                },
                'messages': messages
            }
            filename = f"exports/chat_export_{timestamp}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            return send_file(filename, as_attachment=True, download_name=f"KanoonPK_Chat_{timestamp}.json")
        
        elif format_type == 'pdf':
            filename = f"exports/chat_export_{timestamp}.pdf"
            
            # Create PDF
            c = canvas.Canvas(filename, pagesize=A4)
            width, height = A4
            
            # Header
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, height - 50, "KanoonPK Chat Export")
            
            c.setFont("Helvetica", 10)
            c.drawString(50, height - 70, f"Exported: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            c.drawString(50, height - 85, f"Messages: {len(messages)}")
            
            # Messages
            y = height - 120
            c.setFont("Helvetica", 9)
            
            for msg in messages:
                sender = "You" if msg['type'] == 'user' else "KanoonPK"
                
                # Check if we need a new page
                if y < 100:
                    c.showPage()
                    y = height - 50
                
                # Message header
                c.setFont("Helvetica-Bold", 9)
                c.drawString(50, y, f"[{msg['timestamp']}] {sender}:")
                y -= 15
                
                # Message content
                c.setFont("Helvetica", 8)
                content = msg['content'][:500]  # Truncate very long messages
                lines = content.split('\\n')
                for line in lines:
                    if y < 50:
                        c.showPage()
                        y = height - 50
                    c.drawString(70, y, line[:80])  # Truncate long lines
                    y -= 12
                
                y -= 10  # Extra space between messages
            
            c.save()
            return send_file(filename, as_attachment=True, download_name=f"KanoonPK_Chat_{timestamp}.pdf")
        
        else:
            return jsonify({'error': 'Unsupported format'}), 400
            
    except Exception as e:
        print(f"Export error: {e}")
        return jsonify({'error': f'Export failed: {str(e)}'}), 500

@app.route("/export_pdf", methods=["POST"])
def export_pdf():
    data = request.json
    text = data.get("text", "")
    citations = data.get("citations", [])
    
    filename = f"exports/{uuid.uuid4().hex}.pdf"
    os.makedirs("exports", exist_ok=True)
    
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    
    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "KanoonPK Legal Analysis")
    
    # Date
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 70, f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Content
    y_position = height - 100
    c.setFont("Helvetica", 10)
    
    # Split text into lines that fit the page
    lines = text.split('\\n')
    for line in lines:
        if y_position < 100:
            c.showPage()
            y_position = height - 50
        c.drawString(50, y_position, line[:100])  # Truncate long lines
        y_position -= 15
    
    # Citations
    if citations:
        y_position -= 20
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y_position, "Sources:")
        y_position -= 20
        
        c.setFont("Helvetica", 10)
        for citation in citations:
            if y_position < 50:
                c.showPage()
                y_position = height - 50
            c.drawString(70, y_position, f"• {citation}")
            y_position -= 15
    
    c.save()
    return send_file(filename, as_attachment=True, download_name="KanoonPK_Analysis.pdf")

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
            return f"<div class='success'>✅ {filename} uploaded & indexed successfully!</div><a href='/admin' style='color: #4dd0b7; text-decoration: none; font-weight: 600;'>Upload Another Document</a>"
    
    # Get existing documents for display
    documents = get_uploaded_documents()
    
    # Build documents HTML
    documents_html = ""
    if documents:
        documents_html = "<div class='documents-grid'>"
        for doc in documents:
            doc_details = ""
            if doc['citation']:
                doc_details += f"<p><strong>Citation:</strong> {doc['citation']}</p>"
            if doc['year']:
                doc_details += f"<p><strong>Year:</strong> {doc['year']}</p>"
            if doc['page']:
                doc_details += f"<p><strong>Page:</strong> {doc['page']}</p>"
            if doc['court']:
                doc_details += f"<p><strong>Court:</strong> {doc['court']}</p>"
            doc_details += f"<p><strong>Chunks:</strong> {doc['chunks']}</p>"
            
            documents_html += f"""
            <div class='document-card'>
                <h4>{doc['filename']}</h4>
                {doc_details}
                <button onclick="deleteDocument('{doc['filename']}')" class='delete-btn'>🗑️ Delete</button>
            </div>
            """
        documents_html += "</div>"
    else:
        documents_html = "<div class='no-documents'><p>No documents uploaded yet. Upload your first document below!</p></div>"
    
    return render_template_string(f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KanoonPK Admin Panel</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .logo {{
            height: 60px;
            margin-bottom: 10px;
        }}
        h1 {{
            color: #4dd0b7;
            font-size: 28px;
            margin-bottom: 10px;
        }}
        .subtitle {{
            color: #666;
            font-size: 16px;
        }}
        .upload-section {{
            background: #f8f9fa;
            padding: 25px;
            border-radius: 15px;
            margin-bottom: 30px;
            border: 2px dashed #4dd0b7;
        }}
        .form-group {{
            margin-bottom: 20px;
        }}
        label {{
            display: block;
            font-weight: 600;
            margin-bottom: 8px;
            color: #333;
        }}
        input[type="text"], input[type="file"] {{
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #e1e5e9;
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.3s;
        }}
        input[type="text"]:focus, input[type="file"]:focus {{
            outline: none;
            border-color: #4dd0b7;
        }}
        .file-types {{
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }}
        input[type="submit"] {{
            background: linear-gradient(135deg, #4dd0b7, #36a085);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 25px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.3s;
            width: 100%;
        }}
        input[type="submit"]:hover {{
            transform: translateY(-2px);
        }}
        .back-link {{
            display: inline-block;
            margin-top: 20px;
            color: #4dd0b7;
            text-decoration: none;
            font-weight: 600;
            padding: 10px 20px;
            border: 2px solid #4dd0b7;
            border-radius: 25px;
            transition: all 0.3s;
        }}
        .back-link:hover {{
            background: #4dd0b7;
            color: white;
        }}
        .documents-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }}
        .document-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            border-left: 4px solid #4dd0b7;
        }}
        .document-card h4 {{
            color: #333;
            margin-bottom: 15px;
            font-size: 16px;
        }}
        .document-card p {{
            margin-bottom: 8px;
            font-size: 14px;
            color: #666;
        }}
        .delete-btn {{
            background: #dc3545;
            color: white;
            border: none;
            padding: 8px 15px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 12px;
            margin-top: 10px;
        }}
        .no-documents {{
            text-align: center;
            padding: 40px;
            color: #666;
            background: #f8f9fa;
            border-radius: 10px;
            margin-top: 30px;
        }}
        .success {{
            background: #d4edda;
            color: #155724;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            border: 1px solid #c3e6cb;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <img src="/static/images/kanoonpk-logo.jpg" alt="KanoonPK Logo" class="logo">
            <h1>Admin Panel</h1>
            <p class="subtitle">Document Management & Legal Database Administration</p>
        </div>
        
        <div class="upload-section">
            <h3 style="margin-bottom: 20px; color: #4dd0b7;">📤 Upload Legal Document</h3>
            <form method="post" enctype="multipart/form-data">
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
        
        <h3 style="color: #4dd0b7; margin-bottom: 20px;">📚 Uploaded Documents</h3>
        {documents_html}
        
        <script>
            async function deleteDocument(filename) {{
                if (!confirm('Are you sure you want to delete "' + filename + '"? This action cannot be undone.')) {{
                    return;
                }}
                
                try {{
                    const response = await fetch('/admin/delete', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ filename: filename }})
                    }});
                    
                    const result = await response.json();
                    
                    if (result.success) {{
                        alert('Document deleted successfully!');
                        location.reload();
                    }} else {{
                        alert('Error deleting document: ' + result.message);
                    }}
                }} catch (error) {{
                    alert('Error deleting document: ' + error.message);
                }}
            }}
        </script>
    </div>
</body>
</html>
""")

@app.route("/admin/delete", methods=["POST"])
def delete_document():
    try:
        data = request.json
        filename = data.get('filename')
        
        if not filename:
            return jsonify({'success': False, 'message': 'No filename provided'})
        
        # Delete from ChromaDB (all chunks of this document)
        try:
            all_docs = collection.get()
            ids_to_delete = []
            
            for i, metadata in enumerate(all_docs['metadatas']):
                if metadata.get('source') == filename:
                    ids_to_delete.append(all_docs['ids'][i])
            
            if ids_to_delete:
                collection.delete(ids=ids_to_delete)
        except Exception as e:
            print(f"Error deleting from ChromaDB: {e}")
        
        # Delete physical file
        try:
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error deleting file: {e}")
        
        return jsonify({'success': True, 'message': 'Document deleted successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route("/history")
def history():
    try:
        with open("logs/history.json", "r") as f:
            history = json.load(f)
    except:
        history = []
    
    html = "<h1>Chat History</h1>"
    html += "<a href='/export_csv'>⬇️ Download as CSV</a><br><br>"
    html += "<table border='1'>"
    html += "<tr><th>Time</th><th>Question</th><th>AI Reply (short)</th><th>Citations</th></tr>"
    
    for h in history[-50:]:  # Show last 50 entries
        short_reply = h['reply'][:100] + "..." if len(h['reply']) > 100 else h['reply']
        html += f"<tr><td>{h['timestamp']}</td><td>{h['question']}</td><td>{short_reply}</td><td>{', '.join(h['citations'])}</td></tr>"
    
    html += "</table>"
    return html

@app.route("/export_csv")
def export_csv():
    try:
        with open("logs/history.json", "r") as f:
            history = json.load(f)
    except:
        history = []
    
    filename = f"exports/history_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    os.makedirs("exports", exist_ok=True)
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['timestamp', 'question', 'reply', 'citations']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for entry in history:
            writer.writerow({
                'timestamp': entry['timestamp'],
                'question': entry['question'],
                'reply': entry['reply'],
                'citations': '; '.join(entry.get('citations', []))
            })
    
    return send_file(filename, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)