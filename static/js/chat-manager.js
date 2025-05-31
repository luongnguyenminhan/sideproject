/**
 * Chat Manager for Agent Test Dashboard
 */

const ChatManager = {
    websocket: null,
    wsToken: null,
    currentConversationId: null,
    isConnected: false,
    debugMode: false,
    reconnectAttempts: 0,
    maxReconnectAttempts: 5,

    /**
     * Initialize chat management module
     */
    init() {
        this.setupEventListeners();
        this.loadConversations();
    },

    /**
     * Set up event listeners for chat management
     */
    setupEventListeners() {
        // WebSocket connection controls
        document.getElementById('wsConnectBtn').addEventListener('click', () => {
            this.connectWebSocket();
        });

        document.getElementById('wsDisconnectBtn').addEventListener('click', () => {
            this.disconnectWebSocket();
        });

        // Message sending
        document.getElementById('sendMessageBtn').addEventListener('click', () => {
            this.sendMessage();
        });

        document.getElementById('messageInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Conversation selection
        document.getElementById('chatConversationSelect').addEventListener('change', (e) => {
            this.selectConversation(e.target.value);
        });

        // Load conversations
        document.getElementById('loadChatConversationsBtn').addEventListener('click', () => {
            this.loadConversations();
        });

        // Debug mode toggle
        document.getElementById('debugMode').addEventListener('change', (e) => {
            this.debugMode = e.target.checked;
            this.logDebug('Debug mode ' + (this.debugMode ? 'enabled' : 'disabled'), 'info');
        });
    },

    /**
     * Load conversations for chat selection
     */
    async loadConversations() {
        if (!AuthManager.isAuthenticated()) {
            Utils.showAlert('Please authenticate first', 'warning');
            return;
        }

        const loadBtn = document.getElementById('loadChatConversationsBtn');
        Utils.showLoading(loadBtn);

        try {
            const response = await Utils.apiCall('/conversations/?page=1&page_size=50');

            if (response.error_code === 0) {
                this.populateConversationSelect(response.data.items);
                Utils.showAlert('Conversations loaded successfully', 'success', 2000);
            } else {
                throw new Error(response.message || 'Failed to load conversations');
            }
        } catch (error) {
            console.error('Load conversations error:', error);
            Utils.showAlert(`Failed to load conversations: ${error.message}`, 'danger');
        } finally {
            Utils.hideLoading(loadBtn);
        }
    },

    /**
     * Populate conversation selection dropdown
     */
    populateConversationSelect(conversations) {
        const select = document.getElementById('chatConversationSelect');
        select.innerHTML = '<option value="">Select conversation...</option>';

        conversations.forEach(conv => {
            const option = document.createElement('option');
            option.value = conv.id;
            option.textContent = `${conv.name} (${conv.message_count || 0} messages)`;
            select.appendChild(option);
        });
    },

    /**
     * Select a conversation for chat
     */
    selectConversation(conversationId) {
        if (this.isConnected && this.currentConversationId !== conversationId) {
            this.disconnectWebSocket();
        }

        this.currentConversationId = conversationId;

        if (conversationId) {
            this.loadConversationMessages(conversationId);
            this.enableChatInterface();
        } else {
            this.disableChatInterface();
            this.clearChatMessages();
        }
    },

    /**
     * Load conversation messages
     */
    async loadConversationMessages(conversationId) {
        try {
            const response = await Utils.apiCall(`/conversations/${conversationId}/messages?page=1&page_size=50`);

            if (response.error_code === 0) {
                this.displayMessages(response.data.items.reverse()); // Reverse to show oldest first
            } else {
                throw new Error(response.message || 'Failed to load messages');
            }
        } catch (error) {
            console.error('Load messages error:', error);
            Utils.showAlert(`Failed to load messages: ${error.message}`, 'danger');
        }
    },

    /**
     * Display messages in chat interface
     */
    displayMessages(messages) {
        const chatMessages = document.getElementById('chatMessages');
        chatMessages.innerHTML = '';

        messages.forEach(message => {
            this.appendMessage(message);
        });

        this.scrollToBottom();
    },

    /**
     * Append a single message to chat
     */
    appendMessage(message) {
        const chatMessages = document.getElementById('chatMessages');

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${message.role}`;
        messageDiv.innerHTML = `
            <div class="message-content">
                ${this.formatMessageContent(message.content)}
                <div class="message-meta">
                    ${Utils.formatTimestamp(message.timestamp)}
                    ${message.model_used ? `• ${message.model_used}` : ''}
                    ${message.response_time_ms ? `• ${message.response_time_ms}ms` : ''}
                </div>
            </div>
        `;

        chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    },

    /**
     * Format message content for display
     */
    formatMessageContent(content) {
        // Basic markdown-like formatting
        return content
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>');
    },

    /**
     * Connect to WebSocket
     */
    async connectWebSocket() {
        if (!AuthManager.isAuthenticated()) {
            Utils.showAlert('Please authenticate first', 'warning');
            return;
        }

        if (!this.currentConversationId) {
            Utils.showAlert('Please select a conversation first', 'warning');
            return;
        }

        if (this.isConnected) {
            Utils.showAlert('Already connected to WebSocket', 'info');
            return;
        }

        try {
            // Get WebSocket token
            this.logDebug('Getting WebSocket token...', 'info');
            const tokenResponse = await Utils.apiCall('/chat/websocket/token', {
                method: 'POST'
            });

            if (tokenResponse.error_code !== 0) {
                throw new Error(tokenResponse.message || 'Failed to get WebSocket token');
            }

            this.wsToken = tokenResponse.data.token;
            this.logDebug('WebSocket token obtained', 'info');

            // Connect to WebSocket
            const wsUrl = `${Utils.WS_BASE_URL}/chat/ws/${this.currentConversationId}?token=${this.wsToken}`;
            this.logDebug(`Connecting to: ${wsUrl}`, 'info');

            this.websocket = new WebSocket(wsUrl);

            this.websocket.onopen = (event) => {
                this.onWebSocketOpen(event);
            };

            this.websocket.onmessage = (event) => {
                this.onWebSocketMessage(event);
            };

            this.websocket.onclose = (event) => {
                this.onWebSocketClose(event);
            };

            this.websocket.onerror = (event) => {
                this.onWebSocketError(event);
            };

            this.updateConnectionStatus('connecting');

        } catch (error) {
            console.error('WebSocket connection error:', error);
            Utils.showAlert(`Failed to connect: ${error.message}`, 'danger');
            this.logDebug(`Connection failed: ${error.message}`, 'error');
            this.updateConnectionStatus('disconnected');
        }
    },

    /**
     * Disconnect WebSocket
     */
    disconnectWebSocket() {
        if (this.websocket) {
            this.logDebug('Disconnecting WebSocket...', 'info');
            this.websocket.close();
            this.websocket = null;
        }

        this.isConnected = false;
        this.updateConnectionStatus('disconnected');
        this.hideTypingIndicator();
    },

    /**
     * WebSocket event handlers
     */
    onWebSocketOpen(event) {
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.updateConnectionStatus('connected');
        this.logDebug('WebSocket connected', 'info');
        Utils.showAlert('Connected to chat', 'success', 2000);

        // Send ping to test connection
        this.sendWebSocketMessage({
            type: 'ping'
        });
    },

    onWebSocketMessage(event) {
        try {
            const data = JSON.parse(event.data);
            this.logDebug(`Received: ${data.type}`, 'received');

            switch (data.type) {
                case 'user_message':
                    this.appendMessage(data.message);
                    break;

                case 'assistant_message_complete':
                    this.hideTypingIndicator();
                    this.appendMessage(data.message);
                    break;

                case 'assistant_typing':
                    if (data.status) {
                        this.showTypingIndicator();
                    } else {
                        this.hideTypingIndicator();
                    }
                    break;

                case 'error':
                    Utils.showAlert(`Chat error: ${data.message}`, 'danger');
                    this.logDebug(`Error: ${data.message}`, 'error');
                    break;

                case 'pong':
                    this.logDebug('Pong received', 'received');
                    break;

                default:
                    this.logDebug(`Unknown message type: ${data.type}`, 'error');
            }

        } catch (error) {
            console.error('Error processing WebSocket message:', error);
            this.logDebug(`Message processing error: ${error.message}`, 'error');
        }
    },

    onWebSocketClose(event) {
        this.isConnected = false;
        this.updateConnectionStatus('disconnected');
        this.hideTypingIndicator();

        this.logDebug(`WebSocket closed: ${event.code} - ${event.reason}`, 'info');

        if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
            // Attempt to reconnect for unexpected closures
            this.attemptReconnect();
        } else if (event.code === 4001) {
            Utils.showAlert('Authentication failed. Please refresh your token.', 'danger');
        } else if (event.code === 4003) {
            Utils.showAlert('Access denied to conversation.', 'danger');
        }
    },

    onWebSocketError(event) {
        console.error('WebSocket error:', event);
        this.logDebug('WebSocket error occurred', 'error');
        this.updateConnectionStatus('error');
    },

    /**
     * Attempt to reconnect WebSocket
     */
    attemptReconnect() {
        this.reconnectAttempts++;
        this.logDebug(`Reconnection attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts}`, 'info');

        setTimeout(() => {
            if (!this.isConnected && this.currentConversationId) {
                this.connectWebSocket();
            }
        }, 2000 * this.reconnectAttempts); // Exponential backoff
    },

    /**
     * Send message through WebSocket
     */
    sendMessage() {
        const messageInput = document.getElementById('messageInput');
        const content = messageInput.value.trim();

        if (!content) {
            Utils.showAlert('Please enter a message', 'warning');
            return;
        }

        if (!this.isConnected) {
            Utils.showAlert('Not connected to chat. Please connect first.', 'warning');
            return;
        }

        this.sendWebSocketMessage({
            type: 'chat_message',
            content: content,
            api_key: null // Using agent's configured API key
        });

        messageInput.value = '';
        this.logDebug(`Sent message: ${content.substring(0, 50)}...`, 'sent');
    },

    /**
     * Send WebSocket message
     */
    sendWebSocketMessage(message) {
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.send(JSON.stringify(message));
        } else {
            Utils.showAlert('WebSocket not connected', 'warning');
        }
    },

    /**
     * Update connection status UI
     */
    updateConnectionStatus(status) {
        const statusBadge = document.getElementById('wsStatus');
        const connectBtn = document.getElementById('wsConnectBtn');
        const disconnectBtn = document.getElementById('wsDisconnectBtn');

        switch (status) {
            case 'connected':
                statusBadge.textContent = 'Connected';
                statusBadge.className = 'badge bg-success ws-connected';
                connectBtn.style.display = 'none';
                disconnectBtn.style.display = 'inline-block';
                break;

            case 'connecting':
                statusBadge.textContent = 'Connecting...';
                statusBadge.className = 'badge bg-warning ws-connecting';
                connectBtn.style.display = 'none';
                disconnectBtn.style.display = 'inline-block';
                break;

            case 'disconnected':
                statusBadge.textContent = 'Disconnected';
                statusBadge.className = 'badge bg-secondary ws-disconnected';
                connectBtn.style.display = 'inline-block';
                disconnectBtn.style.display = 'none';
                break;

            case 'error':
                statusBadge.textContent = 'Error';
                statusBadge.className = 'badge bg-danger ws-error';
                connectBtn.style.display = 'inline-block';
                disconnectBtn.style.display = 'none';
                break;
        }
    },

    /**
     * Show typing indicator
     */
    showTypingIndicator() {
        document.getElementById('typingIndicator').style.display = 'block';
        this.scrollToBottom();
    },

    /**
     * Hide typing indicator
     */
    hideTypingIndicator() {
        document.getElementById('typingIndicator').style.display = 'none';
    },

    /**
     * Enable chat interface
     */
    enableChatInterface() {
        document.getElementById('messageInput').disabled = false;
        document.getElementById('sendMessageBtn').disabled = false;
    },

    /**
     * Disable chat interface
     */
    disableChatInterface() {
        document.getElementById('messageInput').disabled = true;
        document.getElementById('sendMessageBtn').disabled = true;
    },

    /**
     * Clear chat messages
     */
    clearChatMessages() {
        document.getElementById('chatMessages').innerHTML = '';
    },

    /**
     * Scroll to bottom of chat
     */
    scrollToBottom() {
        const chatMessages = document.getElementById('chatMessages');
        chatMessages.scrollTop = chatMessages.scrollHeight;
    },

    /**
     * Log debug message
     */
    logDebug(message, type = 'info') {
        if (!this.debugMode) return;

        const debugLog = document.getElementById('wsDebugLog');
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = document.createElement('div');
        logEntry.className = `debug-${type}`;
        logEntry.textContent = `[${timestamp}] ${message}`;

        debugLog.appendChild(logEntry);
        debugLog.scrollTop = debugLog.scrollHeight;

        // Keep only last 100 entries
        while (debugLog.children.length > 100) {
            debugLog.removeChild(debugLog.firstChild);
        }
    }
};

// Export for use in other modules
window.ChatManager = ChatManager;
