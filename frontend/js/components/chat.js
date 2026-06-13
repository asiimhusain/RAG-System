import ApiService from '../services/api.js';
import { Toast, ThemeManager } from './utils.js';

class ChatUI {
    constructor() {
        this.chatBox = document.getElementById('chat-history');
        this.input = document.getElementById('chat-input');
        this.sendBtn = document.getElementById('send-btn');
        this.micBtn = document.getElementById('mic-btn');
        this.micPulse = document.getElementById('mic-pulse');
        this.sessionsList = document.getElementById('sessions-list');
        this.newChatBtn = document.getElementById('new-chat-btn');
        this.activeChatTitle = document.getElementById('active-chat-title');
        
        // Sidebar controls
        this.sidebar = document.getElementById('sidebar');
        this.sidebarToggle = document.getElementById('sidebar-toggle');
        this.sidebarOverlay = document.getElementById('sidebar-overlay');
        this.sidebarClose = document.getElementById('sidebar-close');

        this.isGenerating = false;
        this.recognition = null;
        this.isListening = false;
        
        // Session states
        this.currentSessionId = null;

        this.init();
    }

    async init() {
        lucide.createIcons();
        ThemeManager.init();
        document.getElementById('theme-toggle').addEventListener('click', () => ThemeManager.toggle());

        this.sendBtn.addEventListener('click', () => this.handleSend());
        this.input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.handleSend();
            }
        });

        // Auto resize textarea
        this.input.addEventListener('input', () => {
            this.input.style.height = 'auto';
            this.input.style.height = (this.input.scrollHeight) + 'px';
            this.updateSendButtonState();
        });

        this.newChatBtn.addEventListener('click', () => this.startNewChat());
        
        // Sidebar Toggle Handlers
        this.sidebarToggle.addEventListener('click', () => this.toggleSidebar());
        this.sidebarClose.addEventListener('click', () => this.hideSidebarMobile());
        this.sidebarOverlay.addEventListener('click', () => this.hideSidebarMobile());

        this.initSpeechRecognition();
        this.updateSendButtonState();
        
        // Load existing sessions
        await this.loadSessions();
    }

    toggleSidebar() {
        this.sidebar.classList.toggle('-translate-x-full');
        this.sidebar.classList.toggle('collapsed');
        if (window.innerWidth < 768) {
            const isHidden = this.sidebarOverlay.classList.contains('hidden');
            if (isHidden) {
                this.sidebarOverlay.classList.remove('hidden');
                setTimeout(() => this.sidebarOverlay.classList.remove('opacity-0'), 20);
            } else {
                this.hideSidebarMobile();
            }
        }
    }

    hideSidebarMobile() {
        if (window.innerWidth < 768) {
            this.sidebar.classList.add('-translate-x-full');
            this.sidebarOverlay.classList.add('opacity-0');
            setTimeout(() => this.sidebarOverlay.classList.add('hidden'), 300);
        }
    }

    async loadSessions() {
        try {
            const sessions = await ApiService.getSessions();
            this.sessionsList.innerHTML = '';
            
            if (sessions.length === 0) {
                this.sessionsList.innerHTML = `
                    <div class="text-xs text-neutral-400 dark:text-neutral-500 text-center py-4">
                        No previous chats
                    </div>
                `;
                return;
            }

            sessions.forEach(session => {
                const isActive = session.id === this.currentSessionId;
                const item = document.createElement('div');
                item.className = `session-item ${isActive ? 'active' : ''}`;
                item.dataset.id = session.id;
                
                item.innerHTML = `
                    <div class="flex items-center gap-2 truncate flex-grow mr-2 select-none">
                        <span class="truncate session-title">${session.title}</span>
                    </div>
                    <div class="session-actions flex-shrink-0">
                        <button class="session-action-btn rename-btn" data-id="${session.id}" title="Rename chat">
                            <i data-lucide="edit-2" class="w-3.5 h-3.5"></i>
                        </button>
                        <button class="session-action-btn delete-btn" data-id="${session.id}" title="Delete chat">
                            <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
                        </button>
                    </div>
                `;
                
                // Add click handler to switch session
                item.addEventListener('click', (e) => {
                    // Ignore clicks on actions inside session item
                    if (e.target.closest('.session-action-btn')) return;
                    this.switchSession(session.id, session.title);
                });
                
                // Actions click listeners
                const renameBtn = item.querySelector('.rename-btn');
                renameBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.handleRenameSession(session.id, session.title);
                });

                const deleteBtn = item.querySelector('.delete-btn');
                deleteBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.handleDeleteSession(session.id);
                });

                this.sessionsList.appendChild(item);
            });
            
            lucide.createIcons();
        } catch (error) {
            console.error('Failed to load chat sessions:', error);
            Toast.show('Failed to load chat history', 'error');
        }
    }

    async switchSession(sessionId, title) {
        if (this.isGenerating) return;
        this.currentSessionId = sessionId;
        this.activeChatTitle.textContent = title;
        this.hideSidebarMobile();
        
        // Mark session active in UI
        document.querySelectorAll('.session-item').forEach(el => {
            el.classList.toggle('active', el.dataset.id === sessionId);
        });

        // Set workspace state to active
        const workspace = document.getElementById('chat-workspace');
        workspace.classList.remove('state-initial');
        workspace.classList.add('state-active');

        // Clear log and load messages
        this.chatBox.innerHTML = '';
        const loadingId = this.appendLoading();

        try {
            const messages = await ApiService.getSessionMessages(sessionId);
            document.getElementById(loadingId).remove();
            
            messages.forEach(msg => {
                this.appendMessage(msg.role, msg.content, msg.sources);
            });
        } catch (error) {
            document.getElementById(loadingId).remove();
            Toast.show('Failed to load messages', 'error');
        }
    }

    startNewChat() {
        if (this.isGenerating) return;
        this.currentSessionId = null;
        this.chatBox.innerHTML = '';
        this.activeChatTitle.textContent = 'New Chat';
        
        const workspace = document.getElementById('chat-workspace');
        workspace.classList.remove('state-active');
        workspace.classList.add('state-initial');
        
        // Remove active highlights
        document.querySelectorAll('.session-item').forEach(el => el.classList.remove('active'));
        
        this.hideSidebarMobile();
        this.input.value = '';
        this.input.style.height = 'auto';
        this.updateSendButtonState();
    }

    async handleRenameSession(sessionId, currentTitle) {
        const newTitle = prompt('Rename this conversation:', currentTitle);
        if (newTitle === null) return;
        const trimmed = newTitle.trim();
        if (!trimmed) return;

        try {
            await ApiService.renameSession(sessionId, trimmed);
            if (this.currentSessionId === sessionId) {
                this.activeChatTitle.textContent = trimmed;
            }
            await this.loadSessions();
            Toast.show('Conversation renamed', 'success');
        } catch (error) {
            Toast.show('Failed to rename conversation', 'error');
        }
    }

    async handleDeleteSession(sessionId) {
        if (!confirm('Are you sure you want to delete this conversation?')) return;

        try {
            await ApiService.deleteSession(sessionId);
            if (this.currentSessionId === sessionId) {
                this.startNewChat();
            }
            await this.loadSessions();
            Toast.show('Conversation deleted', 'success');
        } catch (error) {
            Toast.show('Failed to delete conversation', 'error');
        }
    }

    initSpeechRecognition() {
        if ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            this.recognition = new SpeechRecognition();
            this.recognition.continuous = false;
            this.recognition.interimResults = false;
            this.recognition.lang = 'en-US';

            this.recognition.onstart = () => {
                this.isListening = true;
                this.micPulse.classList.remove('hidden');
                const micIcon = this.micBtn.querySelector('i');
                if (micIcon) micIcon.classList.add('mic-listening');
            };

            this.recognition.onend = () => {
                this.isListening = false;
                this.micPulse.classList.add('hidden');
                const micIcon = this.micBtn.querySelector('i');
                if (micIcon) micIcon.classList.remove('mic-listening');
            };

            this.recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                this.input.value = (this.input.value ? this.input.value + ' ' : '') + transcript;
                this.input.style.height = 'auto';
                this.input.style.height = (this.input.scrollHeight) + 'px';
                this.updateSendButtonState();
            };

            this.recognition.onerror = (event) => {
                console.error('Speech recognition error', event.error);
                Toast.show('Speech recognition error: ' + event.error, 'error');
            };

            this.micBtn.addEventListener('click', () => {
                if (this.isListening) {
                    this.recognition.stop();
                } else {
                    this.recognition.start();
                }
            });
        } else {
            this.micBtn.addEventListener('click', () => {
                Toast.show('Speech recognition is not supported in this browser.', 'error');
            });
        }
    }

    updateSendButtonState() {
        const text = this.input.value.trim();
        this.sendBtn.disabled = !text || this.isGenerating;
    }

    async handleSend() {
        const text = this.input.value.trim();
        if (!text || this.isGenerating) return;

        // Transition layout from initial to active state on first message
        const workspace = document.getElementById('chat-workspace');
        if (workspace && workspace.classList.contains('state-initial')) {
            workspace.classList.remove('state-initial');
            workspace.classList.add('state-active');
        }

        this.input.value = '';
        this.input.style.height = 'auto';
        this.updateSendButtonState();
        this.appendMessage('user', text);

        this.isGenerating = true;
        this.updateSendButtonState();
        this.sendBtn.innerHTML = '<i data-lucide="loader" class="w-5 h-5 animate-spin"></i>';
        lucide.createIcons();

        // Create the container for streaming response
        const aiMessageId = 'ai-msg-' + Date.now();
        const msgDiv = document.createElement('div');
        msgDiv.id = aiMessageId;
        msgDiv.className = 'message-row assistant';
        msgDiv.innerHTML = `
            <div class="message-avatar flex-shrink-0">AI</div>
            <div class="message-bubble prose dark:prose-invert">
                <span class="stream-text"><div class="typing-indicator flex gap-1"><span></span><span></span><span></span></div></span>
            </div>
        `;
        this.chatBox.appendChild(msgDiv);
        this.scrollToBottom();

        const streamTextSpan = msgDiv.querySelector('.stream-text');

        let accumulatedAnswer = '';

        try {
            await ApiService.queryStream(
                text,
                this.currentSessionId,
                50,
                5,
                async (metadata) => {
                    // onMetadata
                    if (!this.currentSessionId) {
                        this.currentSessionId = metadata.session_id;
                        this.activeChatTitle.textContent = text.slice(0, 40) + (text.length > 40 ? '...' : '');
                        await this.loadSessions();
                    }
                },
                (token) => {
                    // onToken
                    if (accumulatedAnswer === '') {
                        streamTextSpan.innerHTML = '';
                    }
                    accumulatedAnswer += token;
                    streamTextSpan.innerHTML = this.formatMarkdown(accumulatedAnswer);
                    this.scrollToBottom();
                },
                () => {
                    // onDone
                    this.isGenerating = false;
                    this.updateSendButtonState();
                    this.sendBtn.innerHTML = '<i data-lucide="arrow-up" class="w-5 h-5"></i>';
                    lucide.createIcons();
                    this.scrollToBottom();
                },
                (error) => {
                    // onError
                    if (accumulatedAnswer === '') {
                        streamTextSpan.innerHTML = 'Error generating response: ' + error.message;
                    } else {
                        streamTextSpan.innerHTML += '\n\n[Error: Stream disconnected - ' + error.message + ']';
                    }
                    Toast.show('Failed to connect to RAG backend', 'error');
                    this.isGenerating = false;
                    this.updateSendButtonState();
                    this.sendBtn.innerHTML = '<i data-lucide="arrow-up" class="w-5 h-5"></i>';
                    lucide.createIcons();
                }
            );
        } catch (error) {
            streamTextSpan.innerHTML = 'Error generating response: ' + error.message;
            this.isGenerating = false;
            this.updateSendButtonState();
            this.sendBtn.innerHTML = '<i data-lucide="arrow-up" class="w-5 h-5"></i>';
            lucide.createIcons();
        }
    }

    formatMarkdown(text) {
        // Simple code block and basic markdown formatter
        let parts = text.split(/(```[\s\S]*?```)/g);
        let html = parts.map(part => {
            if (part.startsWith('```') && part.endsWith('```')) {
                let lines = part.slice(3, -3).trim().split('\n');
                let language = 'text';
                if (lines.length > 0 && /^[a-zA-Z0-9+#-]+$/.test(lines[0].trim())) {
                    language = lines.shift().trim();
                }
                let code = lines.join('\n');
                let escapedCode = code.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
                
                // Return styled code block with copy button
                return `
                    <div class="relative my-4">
                        <pre><div class="code-header">
                            <span>${language}</span>
                            <button class="copy-btn" onclick="navigator.clipboard.writeText(this.getAttribute('data-code')).then(() => { this.innerText = 'Copied!'; setTimeout(() => this.innerHTML = '<i data-lucide=\\'copy\\' class=\\'w-3.5 h-3.5\\'></i> Copy code', 2000) })" data-code="${code.replace(/"/g, '&quot;')}">
                                <i data-lucide="copy" class="w-3.5 h-3.5"></i> Copy code
                            </button>
                        </div><code>${escapedCode}</code></pre>
                    </div>
                `;
            } else {
                let formatted = part
                    .replace(/&/g, '&amp;')
                    .replace(/</g, '&lt;')
                    .replace(/>/g, '&gt;')
                    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                    .replace(/\*(.*?)\*/g, '<em>$1</em>')
                    .replace(/`(.*?)`/g, '<code class="px-1.5 py-0.5 bg-neutral-100 dark:bg-neutral-800 rounded font-mono text-sm">$1</code>')
                    .replace(/\n/g, '<br/>');
                return formatted;
            }
        }).join('');
        return html;
    }

    appendMessage(role, text, sources = []) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message-row ${role === 'user' ? 'user' : 'assistant'}`;

        const formatText = this.formatMarkdown(text);

        if (role === 'user') {
            msgDiv.innerHTML = `
                <div class="message-bubble">
                    ${formatText}
                </div>
                <div class="message-avatar flex-shrink-0">U</div>
            `;
        } else {
            msgDiv.innerHTML = `
                <div class="message-avatar flex-shrink-0">AI</div>
                <div class="message-bubble prose dark:prose-invert">
                    ${formatText}
                </div>
            `;
        }

        this.chatBox.appendChild(msgDiv);
        lucide.createIcons();
        this.scrollToBottom();
    }

    appendLoading() {
        const id = 'loading-' + Date.now();
        const msgDiv = document.createElement('div');
        msgDiv.id = id;
        msgDiv.className = 'message-row assistant';

        msgDiv.innerHTML = `
            <div class="message-avatar flex-shrink-0">AI</div>
            <div class="message-bubble flex items-center">
                <div class="typing-indicator flex gap-1">
                    <span></span><span></span><span></span>
                </div>
            </div>
        `;
        this.chatBox.appendChild(msgDiv);
        this.scrollToBottom();
        return id;
    }

    scrollToBottom() {
        const scrollContainer = document.getElementById('chat-history-scroll');
        if (scrollContainer) {
            scrollContainer.scrollTo({ top: scrollContainer.scrollHeight, behavior: 'smooth' });
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new ChatUI();
});
