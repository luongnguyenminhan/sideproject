class AgentTestingInterface {
    constructor() {
        this.baseURL = "http://localhost:8000/api/v1";
        this.currentConversationId = '';
        this.conversationHistory = [];
        this.currentAgent = null;
        this.availableModels = {};
        this.authToken = null;
        this.currentUser = null;
        this.isAuthenticated = false;

        this.init();
    }

    async init() {
        this.setupEventListeners();
        this.loadStoredToken();
        await this.checkAuthentication();

        if (this.isAuthenticated) {
            this.generateConversationId();
            await this.loadInitialData();
            this.showToast('Interface loaded successfully', 'success');
        } else {
            this.showLoginInterface();
        }
    }

    setupEventListeners() {
        // Tab navigation
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.switchTab(e.target.dataset.tab));
        });

        // Chat form
        document.getElementById('chatForm').addEventListener('submit', (e) => this.handleChatSubmit(e));
        document.getElementById('generateIdBtn').addEventListener('click', () => this.generateConversationId());
        document.getElementById('clearChatBtn').addEventListener('click', () => this.clearChat());
        document.getElementById('newConversationBtn').addEventListener('click', () => this.newConversation());

        // Config management
        document.getElementById('editConfigBtn').addEventListener('click', () => this.toggleConfigEdit());
        document.getElementById('cancelConfigBtn').addEventListener('click', () => this.toggleConfigEdit(false));
        document.getElementById('configForm').addEventListener('submit', (e) => this.handleConfigSubmit(e));

        // Temperature slider
        document.getElementById('temperature').addEventListener('input', (e) => {
            document.getElementById('temperatureValue').textContent = e.target.value;
        });

        // API key management
        document.getElementById('apikeyForm').addEventListener('submit', (e) => this.handleApiKeySubmit(e));
        document.getElementById('toggleApiKey').addEventListener('click', () => this.togglePasswordVisibility('apiKey'));
        document.getElementById('toggleOverrideKey').addEventListener('click', () => this.togglePasswordVisibility('overrideApiKey'));

        // Validation
        document.getElementById('validationForm').addEventListener('submit', (e) => this.handleValidationSubmit(e));

        // Refresh buttons
        document.getElementById('refreshBtn').addEventListener('click', () => this.loadInitialData());
        document.getElementById('refreshModelsBtn').addEventListener('click', () => this.loadModels());

        // Authentication
        document.getElementById('loginForm').addEventListener('submit', (e) => this.handleLogin(e));
        document.getElementById('logoutBtn').addEventListener('click', () => this.handleLogout());
    }

    // Authentication Methods
    loadStoredToken() {
        this.authToken = localStorage.getItem('jwt_token');
        if (this.authToken) {
            this.updateAuthHeader();
        }
    }

    updateAuthHeader() {
        // This will be used in API calls
    }

    async checkAuthentication() {
        if (!this.authToken) {
            this.isAuthenticated = false;
            return;
        }

        try {
            const response = await this.apiCall('/users/me');
            this.currentUser = response.data;
            this.isAuthenticated = true;
            this.updateAuthenticationUI();
        } catch (error) {
            console.error('Authentication check failed:', error);
            this.authToken = null;
            localStorage.removeItem('jwt_token');
            this.isAuthenticated = false;
        }
    }

    async handleLogin(e) {
        e.preventDefault();

        const formData = new FormData(e.target);
        const token = formData.get('token').trim();

        if (!token) {
            this.showToast('Please enter a JWT token', 'warning');
            return;
        }

        // Set token temporarily for validation
        this.authToken = token;

        try {
            const response = await this.apiCall('/users/me');
            this.currentUser = response.data;
            this.isAuthenticated = true;

            // Store token on successful validation
            localStorage.setItem('jwt_token', token);

            this.hideLoginInterface();
            this.updateAuthenticationUI();
            this.generateConversationId();
            await this.loadInitialData();
            this.showToast('Login successful', 'success');
        } catch (error) {
            console.error('Login failed:', error);
            this.authToken = null;
            this.isAuthenticated = false;
            this.showToast(`Login failed: ${error.message}`, 'error');
        }
    }

    handleLogout() {
        this.authToken = null;
        this.currentUser = null;
        this.isAuthenticated = false;
        localStorage.removeItem('jwt_token');

        this.showLoginInterface();
        this.updateAuthenticationUI();
        this.showToast('Logged out successfully', 'success');
    }

    showLoginInterface() {
        document.getElementById('loginOverlay').classList.remove('hidden');
        document.getElementById('mainInterface').classList.add('hidden');
    }

    hideLoginInterface() {
        document.getElementById('loginOverlay').classList.add('hidden');
        document.getElementById('mainInterface').classList.remove('hidden');
    }

    updateAuthenticationUI() {
        const authInfo = document.getElementById('authInfo');
        const logoutBtn = document.getElementById('logoutBtn');

        if (this.isAuthenticated && this.currentUser) {
            authInfo.innerHTML = `
                <div class="auth-user">
                    <span class="auth-label">User:</span>
                    <span class="auth-value">${this.currentUser.username || this.currentUser.email || 'Unknown'}</span>
                </div>
            `;
            logoutBtn.classList.remove('hidden');
        } else {
            authInfo.innerHTML = '<span class="auth-status">Not authenticated</span>';
            logoutBtn.classList.add('hidden');
        }
    }

    // Utility Methods
    generateConversationId() {
        this.currentConversationId = 'conv_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        document.getElementById('conversationId').value = this.currentConversationId;
    }

    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        // Update tab content
        document.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));
        document.getElementById(`${tabName}-tab`).classList.add('active');

        // Load tab-specific data
        if (tabName === 'models') {
            this.loadModels();
        }
    }

    togglePasswordVisibility(inputId) {
        const input = document.getElementById(inputId);
        const button = input.nextElementSibling;

        if (input.type === 'password') {
            input.type = 'text';
            button.textContent = '🙈';
        } else {
            input.type = 'password';
            button.textContent = '👁️';
        }
    }

    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <span class="toast-icon">${this.getToastIcon(type)}</span>
            <span class="toast-message">${message}</span>
        `;

        document.getElementById('toastContainer').appendChild(toast);

        setTimeout(() => {
            toast.remove();
        }, 5000);
    }

    getToastIcon(type) {
        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };
        return icons[type] || icons.info;
    }

    showLoading(show = true) {
        const overlay = document.getElementById('loadingOverlay');
        if (show) {
            overlay.classList.remove('hidden');
        } else {
            overlay.classList.add('hidden');
        }
    }

    // API Methods
    async apiCall(endpoint, options = {}) {
        try {
            const headers = {
                'Content-Type': 'application/json',
                ...options.headers
            };

            // Add Authorization header if token exists
            if (this.authToken) {
                headers['Authorization'] = `Bearer ${this.authToken}`;
            }

            const response = await fetch(`${this.baseURL}${endpoint}`, {
                headers,
                ...options
            });

            if (!response.ok) {
                // Handle authentication errors
                if (response.status === 401) {
                    this.handleAuthenticationError();
                    throw new Error('Authentication required');
                }

                const error = await response.json();
                throw new Error(error.message || `HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    handleAuthenticationError() {
        this.authToken = null;
        this.currentUser = null;
        this.isAuthenticated = false;
        localStorage.removeItem('jwt_token');

        this.showLoginInterface();
        this.updateAuthenticationUI();
        this.showToast('Session expired. Please login again.', 'warning');
    }

    // Data Loading Methods
    async loadInitialData() {
        this.showLoading(true);
        try {
            await Promise.all([
                this.loadAgent(),
                this.loadModels()
            ]);
            this.updateStatusIndicator(true);
        } catch (error) {
            console.error('Failed to load initial data:', error);
            this.showToast('Failed to load initial data', 'error');
            this.updateStatusIndicator(false);
        } finally {
            this.showLoading(false);
        }
    }

    async loadAgent() {
        try {
            const response = await this.apiCall('/chat/agent');
            this.currentAgent = response.data;
            this.updateAgentSummary();
            this.updateConfigDisplay();
        } catch (error) {
            console.error('Failed to load agent:', error);
            throw error;
        }
    }

    async loadModels() {
        try {
            const response = await this.apiCall('/chat/models');
            this.availableModels = response.data;
            this.updateModelsDisplay();
            this.updateModelSelect();
        } catch (error) {
            console.error('Failed to load models:', error);
            this.showToast('Failed to load models', 'error');
        }
    }

    // UI Update Methods
    updateStatusIndicator(isActive) {
        const statusDot = document.querySelector('.status-dot');
        const statusText = document.querySelector('.status-text');

        if (isActive) {
            statusDot.classList.add('active');
            statusText.textContent = 'Connected';
        } else {
            statusDot.classList.remove('active');
            statusText.textContent = 'Disconnected';
        }
    }

    updateAgentSummary() {
        if (!this.currentAgent) return;

        document.getElementById('summaryModel').textContent = this.currentAgent.model_name;
        document.getElementById('summaryProvider').textContent = this.currentAgent.model_provider;
        document.getElementById('summaryApiKey').textContent = this.currentAgent.has_api_key ? '✅ Set' : '❌ Missing';
    }

    updateConfigDisplay() {
        if (!this.currentAgent) return;

        const configDisplay = document.getElementById('configDisplay');
        configDisplay.innerHTML = `
            <div class="config-item">
                <span class="config-label">Name:</span>
                <span class="config-value">${this.currentAgent.name}</span>
            </div>
            <div class="config-item">
                <span class="config-label">Description:</span>
                <span class="config-value">${this.currentAgent.description || 'None'}</span>
            </div>
            <div class="config-item">
                <span class="config-label">Model Provider:</span>
                <span class="config-value">${this.currentAgent.model_provider}</span>
            </div>
            <div class="config-item">
                <span class="config-label">Model Name:</span>
                <span class="config-value">${this.currentAgent.model_name}</span>
            </div>
            <div class="config-item">
                <span class="config-label">Temperature:</span>
                <span class="config-value">${this.currentAgent.temperature}</span>
            </div>
            <div class="config-item">
                <span class="config-label">Max Tokens:</span>
                <span class="config-value">${this.currentAgent.max_tokens || 'Default'}</span>
            </div>
            <div class="config-item">
                <span class="config-label">API Key Status:</span>
                <span class="config-value">${this.currentAgent.has_api_key ? '✅ Configured' : '❌ Not Set'}</span>
            </div>
            <div class="config-item">
                <span class="config-label">System Prompt:</span>
                <span class="config-value">${this.currentAgent.default_system_prompt ? 'Set' : 'None'}</span>
            </div>
        `;

        // Update current key status
        this.updateCurrentKeyStatus();
    }

    updateCurrentKeyStatus() {
        if (!this.currentAgent) return;

        const statusDiv = document.getElementById('currentKeyStatus');
        statusDiv.innerHTML = `
            <div class="key-status">
                <h3>Current API Key Status</h3>
                <div class="status-info">
                    <div class="status-item">
                        <span class="status-label">Provider:</span>
                        <span class="status-value">${this.currentAgent.api_provider}</span>
                    </div>
                    <div class="status-item">
                        <span class="status-label">Status:</span>
                        <span class="status-value ${this.currentAgent.has_api_key ? 'success' : 'error'}">
                            ${this.currentAgent.has_api_key ? '✅ Configured' : '❌ Not Set'}
                        </span>
                    </div>
                    <div class="status-item">
                        <span class="status-label">Last Updated:</span>
                        <span class="status-value">${this.currentAgent.update_date || 'Never'}</span>
                    </div>
                </div>
            </div>
        `;
    }

    updateModelsDisplay() {
        const modelsContent = document.getElementById('modelsContent');

        if (!this.availableModels.providers || this.availableModels.providers.length === 0) {
            modelsContent.innerHTML = '<p>No models available</p>';
            return;
        }

        const modelsHTML = this.availableModels.providers.map(provider => `
            <div class="model-provider">
                <div class="provider-header">${provider.provider.toUpperCase()}</div>
                <ul class="model-list">
                    ${provider.models.map(model => `
                        <li class="model-item ${this.currentAgent && this.currentAgent.model_name === model ? 'current' : ''}"
                            data-provider="${provider.provider}" data-model="${model}">
                            ${model} ${this.currentAgent && this.currentAgent.model_name === model ? '(Current)' : ''}
                        </li>
                    `).join('')}
                </ul>
            </div>
        `).join('');

        modelsContent.innerHTML = `<div class="models-grid">${modelsHTML}</div>`;
    }

    updateModelSelect() {
        const select = document.getElementById('modelName');
        select.innerHTML = '<option value="">Select a model...</option>';

        if (this.availableModels.providers) {
            this.availableModels.providers.forEach(provider => {
                provider.models.forEach(model => {
                    const option = document.createElement('option');
                    option.value = model;
                    option.textContent = `${provider.provider}: ${model}`;
                    if (this.currentAgent && this.currentAgent.model_name === model) {
                        option.selected = true;
                    }
                    select.appendChild(option);
                });
            });
        }
    }

    // Chat Methods
    async handleChatSubmit(e) {
        e.preventDefault();

        const formData = new FormData(e.target);
        const message = formData.get('userMessage').trim();
        const conversationId = formData.get('conversationId') || this.currentConversationId;
        const systemPrompt = formData.get('systemPrompt').trim();
        const streaming = document.getElementById('streamingMode').checked;

        if (!message) {
            this.showToast('Please enter a message', 'warning');
            return;
        }

        // Add user message to chat
        this.addMessageToChat('user', message);

        // Clear input
        document.getElementById('userMessage').value = '';

        // Set loading state
        const sendButton = document.getElementById('sendMessageBtn');
        const buttonText = sendButton.querySelector('.btn-text');
        const buttonSpinner = sendButton.querySelector('.btn-spinner');

        buttonText.classList.add('hidden');
        buttonSpinner.classList.remove('hidden');
        sendButton.disabled = true;

        try {
            const requestData = {
                message,
                conversation_id: conversationId,
                streaming
            };

            if (systemPrompt) {
                requestData.system_prompt = systemPrompt;
            }

            if (streaming) {
                await this.handleStreamingChat(requestData);
            } else {
                await this.handleRegularChat(requestData);
            }
        } catch (error) {
            console.error('Chat error:', error);
            this.showToast(`Chat failed: ${error.message}`, 'error');
            this.addMessageToChat('system', `Error: ${error.message}`, 'error');
        } finally {
            buttonText.classList.remove('hidden');
            buttonSpinner.classList.add('hidden');
            sendButton.disabled = false;
        }
    }

    async handleRegularChat(requestData) {
        const response = await this.apiCall('/chat/', {
            method: 'POST',
            body: JSON.stringify(requestData)
        });

        this.addMessageToChat('assistant', response.data.content, null, response.data.metadata);
    }

    async handleStreamingChat(requestData) {
        // For streaming, we would typically use Server-Sent Events or WebSockets
        // For now, implementing as regular call
        await this.handleRegularChat(requestData);
    }

    addMessageToChat(role, content, type = null, metadata = null) {
        const messagesContainer = document.getElementById('chatMessages');

        // Remove welcome message if it exists
        const welcomeMessage = messagesContainer.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;

        let metadataHTML = '';
        if (metadata) {
            metadataHTML = `
                <div class="message-metadata">
                    Model: ${metadata.model_used || 'Unknown'} | 
                    Tokens: ${metadata.tokens_used || 0} | 
                    Time: ${metadata.response_time_ms || 0}ms
                </div>
            `;
        }

        messageDiv.innerHTML = `
            <div class="message-content ${type || ''}">${content}</div>
            ${metadataHTML}
        `;

        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        // Update conversation history
        this.conversationHistory.push({ role, content });
        this.updateConversationsList();
    }

    clearChat() {
        const messagesContainer = document.getElementById('chatMessages');
        messagesContainer.innerHTML = `
            <div class="welcome-message">
                <h3>Chat Cleared</h3>
                <p>Start a new conversation by typing a message below.</p>
            </div>
        `;
        this.conversationHistory = [];
    }

    newConversation() {
        this.clearChat();
        this.generateConversationId();
        this.showToast('New conversation started', 'success');
    }

    updateConversationsList() {
        const conversationsList = document.getElementById('conversationsList');

        if (this.conversationHistory.length === 0) {
            conversationsList.innerHTML = '<div class="no-conversations">No recent conversations</div>';
            return;
        }

        const recentMessages = this.conversationHistory.slice(-5).map((msg, index) => `
            <div class="conversation-item">
                <div class="conversation-role">${msg.role}</div>
                <div class="conversation-preview">${msg.content.substring(0, 50)}...</div>
            </div>
        `).join('');

        conversationsList.innerHTML = recentMessages;
    }

    // Configuration Methods
    toggleConfigEdit(show = null) {
        const displayDiv = document.getElementById('configDisplay');
        const editDiv = document.getElementById('configEdit');
        const editBtn = document.getElementById('editConfigBtn');

        if (show === null) {
            show = editDiv.classList.contains('hidden');
        }

        if (show) {
            displayDiv.classList.add('hidden');
            editDiv.classList.remove('hidden');
            editBtn.textContent = 'Cancel Edit';
            this.populateConfigForm();
        } else {
            displayDiv.classList.remove('hidden');
            editDiv.classList.add('hidden');
            editBtn.textContent = 'Edit Configuration';
        }
    }

    populateConfigForm() {
        if (!this.currentAgent) return;

        document.getElementById('modelName').value = this.currentAgent.model_name;
        document.getElementById('temperature').value = this.currentAgent.temperature;
        document.getElementById('temperatureValue').textContent = this.currentAgent.temperature;
        document.getElementById('maxTokens').value = this.currentAgent.max_tokens || 2048;
        document.getElementById('defaultSystemPrompt').value = this.currentAgent.default_system_prompt || '';
        document.getElementById('toolsConfig').value = JSON.stringify(this.currentAgent.tools_config || {}, null, 2);
    }

    async handleConfigSubmit(e) {
        e.preventDefault();

        const formData = new FormData(e.target);
        const updates = {};

        // Collect form data
        const modelName = formData.get('modelName');
        const temperature = parseFloat(formData.get('temperature'));
        const maxTokens = parseInt(formData.get('maxTokens'));
        const defaultSystemPrompt = formData.get('defaultSystemPrompt');
        const toolsConfigText = formData.get('toolsConfig');

        if (modelName) updates.model_name = modelName;
        if (!isNaN(temperature)) updates.temperature = temperature;
        if (!isNaN(maxTokens)) updates.max_tokens = maxTokens;
        if (defaultSystemPrompt) updates.default_system_prompt = defaultSystemPrompt;

        // Parse tools config
        if (toolsConfigText) {
            try {
                updates.tools_config = JSON.parse(toolsConfigText);
            } catch (error) {
                this.showToast('Invalid JSON in tools configuration', 'error');
                return;
            }
        }

        try {
            await this.apiCall('/chat/agent/config', {
                method: 'PUT',
                body: JSON.stringify(updates)
            });

            this.showToast('Configuration updated successfully', 'success');
            await this.loadAgent();
            this.toggleConfigEdit(false);
        } catch (error) {
            console.error('Config update error:', error);
            this.showToast(`Failed to update configuration: ${error.message}`, 'error');
        }
    }

    // API Key Methods
    async handleApiKeySubmit(e) {
        e.preventDefault();

        const formData = new FormData(e.target);
        const apiKey = formData.get('apiKey').trim();
        const apiProvider = formData.get('apiProvider');

        if (!apiKey) {
            this.showToast('Please enter an API key', 'warning');
            return;
        }

        try {
            await this.apiCall('/chat/agent/api-key', {
                method: 'PUT',
                body: JSON.stringify({
                    api_key: apiKey,
                    api_provider: apiProvider
                })
            });

            this.showToast('API key updated successfully', 'success');
            await this.loadAgent();

            // Clear form
            document.getElementById('apiKey').value = '';
        } catch (error) {
            console.error('API key update error:', error);
            this.showToast(`Failed to update API key: ${error.message}`, 'error');
        }
    }

    // Validation Methods
    async handleValidationSubmit(e) {
        e.preventDefault();

        const formData = new FormData(e.target);
        const testMessage = formData.get('testMessage').trim();
        const overrideApiKey = formData.get('overrideApiKey').trim();

        const requestData = { test_message: testMessage };
        if (overrideApiKey) {
            requestData.override_api_key = overrideApiKey;
        }

        const resultsDiv = document.getElementById('validationResults');
        resultsDiv.innerHTML = '<div class="loading">Running validation...</div>';

        try {
            const response = await this.apiCall('/chat/validate', {
                method: 'POST',
                body: JSON.stringify(requestData)
            });

            const result = response.data;
            const statusClass = result.is_valid ? 'success' : 'error';
            const statusIcon = result.is_valid ? '✅' : '❌';
            const statusText = result.is_valid ? 'Valid' : 'Invalid';

            resultsDiv.innerHTML = `
                <div class="validation-status ${statusClass}">
                    ${statusIcon} Agent Configuration: ${statusText}
                </div>
                ${result.test_response ? `
                    <div class="validation-section">
                        <h4>Test Response:</h4>
                        <div class="validation-response">${result.test_response}</div>
                    </div>
                ` : ''}
                ${result.error_message ? `
                    <div class="validation-section">
                        <h4>Error Message:</h4>
                        <div class="validation-response error">${result.error_message}</div>
                    </div>
                ` : ''}
                ${result.execution_time_ms ? `
                    <div class="validation-section">
                        <h4>Execution Time:</h4>
                        <div class="validation-response">${result.execution_time_ms}ms</div>
                    </div>
                ` : ''}
            `;

            this.showToast(`Validation ${result.is_valid ? 'passed' : 'failed'}`, statusClass);
        } catch (error) {
            console.error('Validation error:', error);
            resultsDiv.innerHTML = `
                <div class="validation-status error">
                    ❌ Validation Failed
                </div>
                <div class="validation-section">
                    <h4>Error:</h4>
                    <div class="validation-response error">${error.message}</div>
                </div>
            `;
            this.showToast(`Validation failed: ${error.message}`, 'error');
        }
    }
}

// Initialize the interface when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new AgentTestingInterface();
});
