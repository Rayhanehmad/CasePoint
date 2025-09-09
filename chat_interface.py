"""
Modern ChatGPT-style interface for KanoonPK Legal AI
"""
from flask import Blueprint, render_template_string, request, jsonify, session, g
from flask_login import login_required, current_user
import json
import datetime
from openai import OpenAI
import os

chat_bp = Blueprint('chat', __name__, url_prefix='/chat')

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@chat_bp.route('/')
def chat_interface():
    """Modern ChatGPT-style interface"""
    tenant_param = request.args.get('tenant', '')
    if tenant_param:
        session['tenant_subdomain'] = tenant_param
    
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en" data-bs-theme="dark">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>KanoonPK AI - Legal Research Assistant</title>
        <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            :root {
                --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                --chat-bg: #1a1a1a;
                --message-user: linear-gradient(135deg, #667eea, #764ba2);
                --message-ai: #2d2d2d;
                --input-bg: rgba(255, 255, 255, 0.1);
            }
            
            body {
                background: var(--chat-bg);
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                height: 100vh;
                overflow: hidden;
            }
            
            .chat-container {
                display: flex;
                flex-direction: column;
                height: 100vh;
                max-width: 900px;
                margin: 0 auto;
                background: var(--chat-bg);
            }
            
            .chat-header {
                background: var(--primary-gradient);
                padding: 20px;
                text-align: center;
                color: white;
                box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            }
            
            .chat-header h1 {
                margin: 0;
                font-size: 1.8rem;
                font-weight: 300;
            }
            
            .chat-header .subtitle {
                opacity: 0.9;
                margin-top: 5px;
                font-size: 0.9rem;
            }
            
            .chat-messages {
                flex: 1;
                overflow-y: auto;
                padding: 20px;
                display: flex;
                flex-direction: column;
                gap: 20px;
            }
            
            .message {
                display: flex;
                gap: 12px;
                max-width: 80%;
                animation: fadeIn 0.5s ease-in;
            }
            
            .message.user {
                align-self: flex-end;
                flex-direction: row-reverse;
            }
            
            .message-avatar {
                width: 40px;
                height: 40px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                flex-shrink: 0;
                font-size: 1.2rem;
            }
            
            .message.user .message-avatar {
                background: var(--message-user);
                color: white;
            }
            
            .message.ai .message-avatar {
                background: var(--message-ai);
                color: #667eea;
                border: 2px solid #667eea;
            }
            
            .message-content {
                padding: 15px 20px;
                border-radius: 20px;
                line-height: 1.5;
                font-size: 0.95rem;
            }
            
            .message.user .message-content {
                background: var(--message-user);
                color: white;
                border-bottom-right-radius: 5px;
            }
            
            .message.ai .message-content {
                background: var(--message-ai);
                color: #e0e0e0;
                border-bottom-left-radius: 5px;
                border: 1px solid #3a3a3a;
            }
            
            .chat-input-container {
                padding: 20px;
                background: rgba(0,0,0,0.2);
                border-top: 1px solid #3a3a3a;
            }
            
            .chat-input-wrapper {
                display: flex;
                gap: 10px;
                align-items: flex-end;
                max-width: 100%;
                background: var(--input-bg);
                border-radius: 25px;
                padding: 15px 20px;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255,255,255,0.1);
            }
            
            .chat-input {
                flex: 1;
                border: none;
                background: transparent;
                color: white;
                font-size: 1rem;
                resize: none;
                outline: none;
                min-height: 24px;
                max-height: 120px;
                line-height: 1.5;
            }
            
            .chat-input::placeholder {
                color: rgba(255,255,255,0.5);
            }
            
            .send-button {
                background: var(--primary-gradient);
                border: none;
                border-radius: 50%;
                width: 45px;
                height: 45px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                cursor: pointer;
                transition: all 0.3s;
                flex-shrink: 0;
            }
            
            .send-button:hover {
                transform: scale(1.1);
                box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
            }
            
            .send-button:disabled {
                opacity: 0.5;
                transform: none;
                cursor: not-allowed;
            }
            
            .typing-indicator {
                display: none;
                padding: 15px 20px;
                background: var(--message-ai);
                border-radius: 20px;
                border-bottom-left-radius: 5px;
                color: #667eea;
                border: 1px solid #3a3a3a;
                max-width: 80px;
            }
            
            .typing-dots {
                display: flex;
                gap: 4px;
            }
            
            .typing-dot {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: #667eea;
                animation: typingBounce 1.4s infinite ease-in-out;
            }
            
            .typing-dot:nth-child(1) { animation-delay: -0.32s; }
            .typing-dot:nth-child(2) { animation-delay: -0.16s; }
            
            @keyframes typingBounce {
                0%, 80%, 100% { transform: scale(0); }
                40% { transform: scale(1); }
            }
            
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            .welcome-message {
                text-align: center;
                color: rgba(255,255,255,0.6);
                font-style: italic;
                margin: 40px 0;
            }
            
            .legal-badges {
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
                margin-top: 10px;
            }
            
            .legal-badge {
                background: rgba(102, 126, 234, 0.2);
                color: #a78bfa;
                padding: 4px 12px;
                border-radius: 15px;
                font-size: 0.8rem;
                border: 1px solid rgba(102, 126, 234, 0.3);
            }
            
            /* Mobile responsiveness */
            @media (max-width: 768px) {
                .chat-container {
                    height: 100vh;
                }
                
                .message {
                    max-width: 95%;
                }
                
                .chat-header h1 {
                    font-size: 1.4rem;
                }
                
                .chat-input-wrapper {
                    padding: 12px 15px;
                }
            }
        </style>
    </head>
    <body>
        <div class="chat-container">
            <!-- Chat Header -->
            <div class="chat-header">
                <div class="d-flex align-items-center justify-content-center gap-3">
                    <i class="fas fa-balance-scale fa-2x"></i>
                    <div>
                        <h1>KanoonPK AI Assistant</h1>
                        <div class="subtitle">Pakistan Legal Research • Powered by AI</div>
                    </div>
                </div>
            </div>
            
            <!-- Chat Messages -->
            <div class="chat-messages" id="chatMessages">
                <div class="welcome-message">
                    <i class="fas fa-gavel fa-2x mb-3" style="color: #667eea;"></i>
                    <h4>Welcome to Pakistan's Advanced Legal AI</h4>
                    <p>Ask me anything about Pakistani law, case precedents, or legal procedures</p>
                    
                    <div class="legal-badges">
                        <span class="legal-badge">Constitutional Law</span>
                        <span class="legal-badge">Criminal Law</span>
                        <span class="legal-badge">Civil Procedure</span>
                        <span class="legal-badge">Contract Law</span>
                        <span class="legal-badge">Family Law</span>
                    </div>
                </div>
                
                <!-- Typing indicator -->
                <div class="message ai" id="typingIndicator">
                    <div class="message-avatar">
                        <i class="fas fa-robot"></i>
                    </div>
                    <div class="typing-indicator">
                        <div class="typing-dots">
                            <div class="typing-dot"></div>
                            <div class="typing-dot"></div>
                            <div class="typing-dot"></div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Chat Input -->
            <div class="chat-input-container">
                <div class="chat-input-wrapper">
                    <textarea 
                        id="chatInput" 
                        class="chat-input" 
                        placeholder="Ask about Pakistan law, case precedents, legal procedures..."
                        rows="1"
                    ></textarea>
                    <button id="sendButton" class="send-button">
                        <i class="fas fa-paper-plane"></i>
                    </button>
                </div>
            </div>
        </div>

        <script>
            const chatMessages = document.getElementById('chatMessages');
            const chatInput = document.getElementById('chatInput');
            const sendButton = document.getElementById('sendButton');
            const typingIndicator = document.getElementById('typingIndicator');
            
            // Hide typing indicator initially
            typingIndicator.style.display = 'none';
            
            // Auto-resize textarea
            chatInput.addEventListener('input', function() {
                this.style.height = 'auto';
                this.style.height = Math.min(this.scrollHeight, 120) + 'px';
            });
            
            // Send message on Enter (but not Shift+Enter)
            chatInput.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                }
            });
            
            // Send button click
            sendButton.addEventListener('click', sendMessage);
            
            async function sendMessage() {
                const message = chatInput.value.trim();
                if (!message) return;
                
                // Add user message
                addMessage(message, 'user');
                chatInput.value = '';
                chatInput.style.height = 'auto';
                
                // Show typing indicator
                showTyping();
                
                // Disable send button
                sendButton.disabled = true;
                
                try {
                    const response = await fetch('/chat/api/send', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ message: message })
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        addMessage(data.reply, 'ai');
                    } else {
                        addMessage('Sorry, I encountered an error. Please try again.', 'ai');
                    }
                } catch (error) {
                    addMessage('Connection error. Please check your internet and try again.', 'ai');
                } finally {
                    hideTyping();
                    sendButton.disabled = false;
                    chatInput.focus();
                }
            }
            
            function addMessage(content, type) {
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${type}`;
                
                const avatar = document.createElement('div');
                avatar.className = 'message-avatar';
                avatar.innerHTML = type === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';
                
                const messageContent = document.createElement('div');
                messageContent.className = 'message-content';
                messageContent.innerHTML = formatMessage(content);
                
                messageDiv.appendChild(avatar);
                messageDiv.appendChild(messageContent);
                
                // Insert before typing indicator
                chatMessages.insertBefore(messageDiv, typingIndicator);
                
                // Scroll to bottom
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
            
            function formatMessage(content) {
                // Basic formatting for legal content
                content = content.replace(/\\n/g, '<br>');
                
                // Highlight legal citations (basic pattern)
                content = content.replace(/(\\b\\d{4}\\s+[A-Z]+\\s+\\d+)/g, '<span class="legal-badge">$1</span>');
                
                // Highlight section references
                content = content.replace(/(Section\\s+\\d+)/gi, '<strong style="color: #a78bfa;">$1</strong>');
                content = content.replace(/(Article\\s+\\d+)/gi, '<strong style="color: #a78bfa;">$1</strong>');
                
                return content;
            }
            
            function showTyping() {
                typingIndicator.style.display = 'flex';
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
            
            function hideTyping() {
                typingIndicator.style.display = 'none';
            }
            
            // Focus input on load
            chatInput.focus();
            
            // Example starter questions
            setTimeout(() => {
                const examples = [
                    "What are the basic rights under Pakistan's Constitution?",
                    "Explain the procedure for filing a civil suit in Pakistan",
                    "What are the grounds for divorce under Muslim Family Law?",
                    "How does the criminal justice system work in Pakistan?"
                ];
                
                // You could add example prompts here if needed
            }, 1000);
        </script>
    </body>
    </html>
    """)

@chat_bp.route('/api/send', methods=['POST'])
def send_message():
    """Handle chat messages and respond with ChatGPT"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'success': False, 'error': 'No message provided'})
        
        # Enhanced system prompt that maintains ChatGPT quality while adding legal expertise
        system_prompt = """You are ChatGPT, enhanced with specialized knowledge of Pakistani law and legal systems. 

You have all the capabilities of regular ChatGPT plus deep expertise in:
- Pakistan's Constitution 1973, laws, and legal procedures
- Pakistan Penal Code (PPC), Criminal Procedure Code (CrPC), Civil Procedure Code (CPC)  
- Pakistani case law, Supreme Court and High Court precedents
- Islamic jurisprudence as applied in Pakistan
- Business law, contracts, and corporate regulations in Pakistan

When answering legal questions about Pakistan:
- Provide accurate, comprehensive information
- Cite relevant sections, articles, or case law when helpful
- Note that this is informational only, not formal legal advice
- Use clear, accessible language while maintaining legal accuracy

For all other topics, respond exactly as regular ChatGPT would - be helpful, accurate, creative, and engaging. You can discuss any topic with the same quality and depth as standard ChatGPT."""

        # Generate response using OpenAI with optimal settings
        # the newest OpenAI model is "gpt-5" which was released August 7, 2025.
        # do not change this unless explicitly requested by the user
        response = client.chat.completions.create(
            model="gpt-5",  # Latest and most capable model
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=2000,  # Increased for more comprehensive responses
            temperature=0.7,  # Balanced for accuracy and natural conversation
            top_p=0.9,  # Better response quality
            frequency_penalty=0.1,  # Reduce repetition
            presence_penalty=0.1  # Encourage diverse topics
        )
        
        ai_reply = response.choices[0].message.content
        
        # Log the conversation (you could save to database here)
        # session.setdefault('chat_history', []).append({
        #     'user': user_message,
        #     'ai': ai_reply,
        #     'timestamp': datetime.datetime.now().isoformat()
        # })
        
        return jsonify({
            'success': True,
            'reply': ai_reply,
            'timestamp': datetime.datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Chat error: {e}")
        print(f"Error details: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'AI service error: {str(e)}. Please try again.'
        })