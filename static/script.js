// KanoonPK Chat Interface Script

class ChatInterface {
    constructor() {
        this.messagesContainer = document.getElementById('messages');
        this.userInput = document.getElementById('userInput');
        this.sendBtn = document.getElementById('sendBtn');
        this.downloadPdfBtn = document.getElementById('downloadPdfBtn');
        this.clearChatBtn = document.getElementById('clearChatBtn');
        this.welcomeCard = document.getElementById('welcomeCard');
        
        this.lastAnswer = '';
        this.lastCitations = [];
        this.lastQuestion = '';
        this.isProcessing = false;
        
        this.initializeEventListeners();
        this.loadChatHistory();
    }

    initializeEventListeners() {
        // Send message on Enter key
        this.userInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Send button click
        this.sendBtn.addEventListener('click', () => {
            this.sendMessage();
        });

        // Download PDF button
        this.downloadPdfBtn.addEventListener('click', () => {
            this.downloadPDF();
        });

        // Clear chat button
        this.clearChatBtn.addEventListener('click', () => {
            this.clearChat();
        });

        // Auto-resize input
        this.userInput.addEventListener('input', () => {
            this.userInput.style.height = 'auto';
            this.userInput.style.height = this.userInput.scrollHeight + 'px';
        });
    }

    async sendMessage() {
        const message = this.userInput.value.trim();
        if (!message || this.isProcessing) return;

        this.isProcessing = true;
        this.hideWelcomeCard();
        
        // Add user message to chat
        this.addMessage(message, 'user');
        this.userInput.value = '';
        this.userInput.style.height = 'auto';

        // Update UI
        this.updateSendButton(true);
        this.showTypingIndicator();

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to get response');
            }

            // Store last answer for PDF export
            this.lastAnswer = data.reply;
            this.lastCitations = data.sources || [];
            this.lastQuestion = message;

            // Add bot response to chat
            this.addMessage(data.reply, 'bot', data.sources, data.timestamp);
            
            // Enable PDF download if we have an answer
            this.downloadPdfBtn.disabled = false;

        } catch (error) {
            console.error('Chat error:', error);
            this.addMessage(
                `Sorry, I encountered an error: ${error.message}. Please try again.`, 
                'bot', 
                [], 
                null, 
                true
            );
        } finally {
            this.hideTypingIndicator();
            this.updateSendButton(false);
            this.isProcessing = false;
            this.saveChatHistory();
        }
    }

    addMessage(content, type, citations = [], timestamp = null, isError = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type} ${isError ? 'error-message' : ''}`;

        let messageHTML = `<div class="message-content">${this.formatMessageContent(content)}</div>`;

        // Add timestamp
        if (timestamp || type === 'user') {
            const timeStr = timestamp ? new Date(timestamp).toLocaleTimeString() : new Date().toLocaleTimeString();
            messageHTML += `<div class="timestamp"><i class="fas fa-clock me-1"></i>${timeStr}</div>`;
        }

        // Add citations
        if (citations && citations.length > 0) {
            messageHTML += '<div class="citations">';
            messageHTML += '<small class="text-muted"><i class="fas fa-quote-right me-1"></i>Sources:</small><br>';
            citations.forEach(citation => {
                messageHTML += `<span class="badge bg-secondary citation-badge me-1">${citation}</span>`;
            });
            messageHTML += '</div>';
        }

        messageDiv.innerHTML = messageHTML;
        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }

    formatMessageContent(content) {
        // Convert newlines to line breaks and handle basic formatting
        return content
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>');
    }

    showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'typing-indicator';
        typingDiv.id = 'typing-indicator';
        typingDiv.innerHTML = `
            <div class="typing-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
        `;
        this.messagesContainer.appendChild(typingDiv);
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    updateSendButton(isLoading) {
        if (isLoading) {
            this.sendBtn.disabled = true;
            this.sendBtn.classList.add('btn-loading');
            this.sendBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        } else {
            this.sendBtn.disabled = false;
            this.sendBtn.classList.remove('btn-loading');
            this.sendBtn.innerHTML = '<i class="fas fa-paper-plane"></i>';
        }
    }

    async downloadPDF() {
        if (!this.lastAnswer) {
            alert('No answer available to download.');
            return;
        }

        try {
            const response = await fetch('/export_pdf', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text: this.lastAnswer,
                    citations: this.lastCitations,
                    question: this.lastQuestion
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to generate PDF');
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'KanoonPK_Answer.pdf';
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);

        } catch (error) {
            console.error('PDF download error:', error);
            alert(`Failed to download PDF: ${error.message}`);
        }
    }

    clearChat() {
        if (confirm('Are you sure you want to clear the chat history?')) {
            this.messagesContainer.innerHTML = '';
            this.lastAnswer = '';
            this.lastCitations = [];
            this.lastQuestion = '';
            this.downloadPdfBtn.disabled = true;
            this.showWelcomeCard();
            this.clearChatHistory();
        }
    }

    hideWelcomeCard() {
        if (this.welcomeCard && !this.welcomeCard.classList.contains('d-none')) {
            this.welcomeCard.classList.add('d-none');
        }
    }

    showWelcomeCard() {
        if (this.welcomeCard && this.welcomeCard.classList.contains('d-none')) {
            this.welcomeCard.classList.remove('d-none');
        }
    }

    scrollToBottom() {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }

    // Local storage functions for chat history
    saveChatHistory() {
        try {
            const messages = Array.from(this.messagesContainer.children)
                .filter(el => el.classList.contains('message'))
                .map(el => ({
                    type: el.classList.contains('user') ? 'user' : 'bot',
                    content: el.querySelector('.message-content').innerHTML,
                    citations: Array.from(el.querySelectorAll('.citation-badge')).map(badge => badge.textContent),
                    timestamp: el.querySelector('.timestamp')?.textContent.replace('🕐', '').trim()
                }));
            
            localStorage.setItem('kanoonpk_chat_history', JSON.stringify({
                messages: messages,
                lastAnswer: this.lastAnswer,
                lastCitations: this.lastCitations,
                lastQuestion: this.lastQuestion
            }));
        } catch (error) {
            console.warn('Failed to save chat history:', error);
        }
    }

    loadChatHistory() {
        try {
            const saved = localStorage.getItem('kanoonpk_chat_history');
            if (saved) {
                const data = JSON.parse(saved);
                
                // Restore messages
                data.messages?.forEach(msg => {
                    const messageDiv = document.createElement('div');
                    messageDiv.className = `message ${msg.type}`;
                    
                    let html = `<div class="message-content">${msg.content}</div>`;
                    if (msg.timestamp) {
                        html += `<div class="timestamp"><i class="fas fa-clock me-1"></i>${msg.timestamp}</div>`;
                    }
                    if (msg.citations?.length > 0) {
                        html += '<div class="citations">';
                        html += '<small class="text-muted"><i class="fas fa-quote-right me-1"></i>Sources:</small><br>';
                        msg.citations.forEach(citation => {
                            html += `<span class="badge bg-secondary citation-badge me-1">${citation}</span>`;
                        });
                        html += '</div>';
                    }
                    
                    messageDiv.innerHTML = html;
                    this.messagesContainer.appendChild(messageDiv);
                });

                // Restore last answer data
                this.lastAnswer = data.lastAnswer || '';
                this.lastCitations = data.lastCitations || [];
                this.lastQuestion = data.lastQuestion || '';
                
                // Enable PDF download if we have an answer
                this.downloadPdfBtn.disabled = !this.lastAnswer;
                
                // Hide welcome card if we have messages
                if (data.messages?.length > 0) {
                    this.hideWelcomeCard();
                }
                
                this.scrollToBottom();
            }
        } catch (error) {
            console.warn('Failed to load chat history:', error);
        }
    }

    clearChatHistory() {
        try {
            localStorage.removeItem('kanoonpk_chat_history');
        } catch (error) {
            console.warn('Failed to clear chat history:', error);
        }
    }
}

// Initialize chat interface when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ChatInterface();
});

// Service worker registration for PWA capabilities (optional)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/sw.js')
            .then(() => console.log('ServiceWorker registered'))
            .catch(() => console.log('ServiceWorker registration failed'));
    });
}
