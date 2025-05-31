/**
 * Agent Manager for Agent Test Dashboard
 */

const AgentManager = {
    /**
     * Initialize agent management module
     */
    init() {
        this.setupEventListeners();
    },

    /**
     * Set up event listeners for agent management
     */
    setupEventListeners() {
        // Refresh current agent
        document.getElementById('refreshAgentBtn').addEventListener('click', () => {
            this.loadCurrentAgent();
        });

        // Load available models
        document.getElementById('loadModelsBtn').addEventListener('click', () => {
            this.loadAvailableModels();
        });

        // API Key form submission
        document.getElementById('apiKeyForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.updateApiKey();
        });

        // Agent configuration form submission
        document.getElementById('agentConfigForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.updateAgentConfig();
        });

        // Validate agent button
        document.getElementById('validateAgentBtn').addEventListener('click', () => {
            this.validateAgent();
        });

        // Toggle API key visibility
        document.getElementById('toggleApiKey').addEventListener('click', () => {
            this.toggleApiKeyVisibility();
        });
    },

    /**
     * Load current system agent configuration
     */
    async loadCurrentAgent() {
        if (!AuthManager.isAuthenticated()) {
            Utils.showAlert('Please authenticate first', 'warning');
            return;
        }

        const refreshBtn = document.getElementById('refreshAgentBtn');
        Utils.showLoading(refreshBtn);

        try {
            // Based on your agent routes, get current system agent
            const response = await Utils.apiCall('/chat/agent');

            if (response.error_code === 0) {
                this.displayCurrentAgent(response.data);
                Utils.showAlert('Current agent loaded successfully', 'success');
            } else {
                throw new Error(response.message || 'Failed to load agent');
            }
        } catch (error) {
            console.error('Load agent error:', error);
            Utils.showAlert(`Failed to load agent: ${error.message}`, 'danger');
            this.displayCurrentAgent(null);
        } finally {
            Utils.hideLoading(refreshBtn);
        }
    },

    /**
     * Display current agent information
     */
    displayCurrentAgent(agentData) {
        const container = document.getElementById('currentAgent');

        if (!agentData) {
            container.innerHTML = `
                <div class="agent-status unconfigured">
                    <i class="fas fa-exclamation-triangle"></i>
                    <strong>No Agent Configured</strong>
                    <p class="mb-0">No system agent is currently configured.</p>
                </div>
            `;
            return;
        }

        // Fill form fields with current agent data
        document.getElementById('configProvider').value = agentData.model_provider || '';
        document.getElementById('configModel').value = agentData.model_name || '';
        document.getElementById('configTemperature').value = agentData.temperature || 0.7;
        document.getElementById('configMaxTokens').value = agentData.max_tokens || 2048;
        document.getElementById('configSystemPrompt').value = agentData.default_system_prompt || '';

        // Also update API provider if available
        if (agentData.api_provider) {
            document.getElementById('apiProvider').value = agentData.api_provider;
        }

        container.innerHTML = `
            <div class="agent-status configured">
                <i class="fas fa-check-circle"></i>
                <strong>${agentData.name || 'Agent Configured'}</strong>
                <div class="mt-2">
                    <div class="row">
                        <div class="col-md-6">
                            <small class="text-muted">ID:</small><br>
                            <code>${agentData.id || 'N/A'}</code>
                        </div>
                        <div class="col-md-6">
                            <small class="text-muted">Status:</small><br>
                            <span class="badge ${agentData.is_active ? 'bg-success' : 'bg-warning'}">${agentData.is_active ? 'Active' : 'Inactive'}</span>
                        </div>
                    </div>
                    <div class="row mt-2">
                        <div class="col-md-6">
                            <small class="text-muted">Provider:</small><br>
                            <span class="badge bg-primary">${agentData.model_provider || 'N/A'}</span>
                        </div>
                        <div class="col-md-6">
                            <small class="text-muted">Model:</small><br>
                            <code>${agentData.model_name || 'N/A'}</code>
                        </div>
                    </div>
                    <div class="row mt-2">
                        <div class="col-md-6">
                            <small class="text-muted">Temperature:</small><br>
                            <code>${agentData.temperature || 'N/A'}</code>
                        </div>
                        <div class="col-md-6">
                            <small class="text-muted">Max Tokens:</small><br>
                            <code>${agentData.max_tokens || 'N/A'}</code>
                        </div>
                    </div>
                    <div class="row mt-2">
                        <div class="col-md-6">
                            <small class="text-muted">API Key:</small><br>
                            <span class="badge ${agentData.has_api_key ? 'bg-success' : 'bg-danger'}">${agentData.has_api_key ? 'Configured' : 'Not Set'}</span>
                        </div>
                        <div class="col-md-6">
                            <small class="text-muted">API Provider:</small><br>
                            <code>${agentData.api_provider || 'N/A'}</code>
                        </div>
                    </div>
                    ${agentData.tools_config ? `
                        <div class="row mt-2">
                            <div class="col-12">
                                <small class="text-muted">Tools:</small><br>
                                ${Object.entries(agentData.tools_config).map(([tool, enabled]) => 
                                    `<span class="badge ${enabled ? 'bg-success' : 'bg-secondary'} me-1">${tool}: ${enabled ? 'ON' : 'OFF'}</span>`
                                ).join('')}
                            </div>
                        </div>
                    ` : ''}
                    ${agentData.default_system_prompt ? `
                        <div class="mt-2">
                            <small class="text-muted">System Prompt:</small><br>
                            <div class="bg-light p-2 rounded" style="max-height: 100px; overflow-y: auto;">
                                <small>${Utils.truncateText(agentData.default_system_prompt, 200)}</small>
                            </div>
                        </div>
                    ` : ''}
                    ${agentData.description ? `
                        <div class="mt-2">
                            <small class="text-muted">Description:</small><br>
                            <small class="text-muted">${agentData.description}</small>
                        </div>
                    ` : ''}
                    <div class="mt-2">
                        <small class="text-muted">Created:</small><br>
                        <small>${Utils.formatTimestamp(agentData.create_date)}</small>
                        ${agentData.update_date ? `
                            <br><small class="text-muted">Updated:</small><br>
                            <small>${Utils.formatTimestamp(agentData.update_date)}</small>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
    },

    /**
     * Load available models
     */
    async loadAvailableModels() {
        if (!AuthManager.isAuthenticated()) {
            Utils.showAlert('Please authenticate first', 'warning');
            return;
        }

        const loadBtn = document.getElementById('loadModelsBtn');
        Utils.showLoading(loadBtn);

        try {
            const response = await Utils.apiCall('/chat/models');

            if (response.error_code === 0) {
                this.displayAvailableModels(response.data);
                Utils.showAlert('Available models loaded successfully', 'success');
            } else {
                throw new Error(response.message || 'Failed to load models');
            }
        } catch (error) {
            console.error('Load models error:', error);
            Utils.showAlert(`Failed to load models: ${error.message}`, 'danger');
            this.displayAvailableModels(null);
        } finally {
            Utils.hideLoading(loadBtn);
        }
    },

    /**
     * Display available models
     */
    displayAvailableModels(modelsData) {
        const container = document.getElementById('availableModels');

        if (!modelsData || !modelsData.providers || modelsData.providers.length === 0) {
            container.innerHTML = '<div class="text-muted">No models available or failed to load</div>';
            return;
        }

        let html = '<div class="available-models">';

        modelsData.providers.forEach(providerData => {
            const provider = providerData.provider;
            const models = providerData.models;

            html += `
                <div class="provider-group mb-3">
                    <h6 class="text-primary">${provider.toUpperCase()}</h6>
                    <div class="models-list">
            `;

            models.forEach(modelName => {
                html += `
                    <div class="model-item d-flex justify-content-between align-items-center p-2 border rounded mb-1">
                        <div>
                            <code class="text-primary">${modelName}</code>
                        </div>
                        <button class="btn btn-sm btn-outline-primary" 
                                onclick="AgentManager.selectModel('${provider}', '${modelName}')">
                            <i class="fas fa-check"></i> Select
                        </button>
                    </div>
                `;
            });

            html += '</div></div>';
        });

        html += '</div>';
        container.innerHTML = html;
    },

    /**
     * Select a model and fill the form
     */
    selectModel(provider, modelName) {
        document.getElementById('configProvider').value = provider;
        document.getElementById('configModel').value = modelName;
        Utils.showAlert(`Selected ${provider}/${modelName}`, 'info', 3000);
    },

    /**
     * Update API key
     */
    async updateApiKey() {
        if (!AuthManager.isAuthenticated()) {
            Utils.showAlert('Please authenticate first', 'warning');
            return;
        }

        const provider = document.getElementById('apiProvider').value;
        const apiKey = document.getElementById('apiKey').value.trim();

        if (!provider || !apiKey) {
            Utils.showAlert('Please provide both provider and API key', 'warning');
            return;
        }

        const submitBtn = document.querySelector('#apiKeyForm button[type="submit"]');
        Utils.showLoading(submitBtn);

        try {
            const response = await Utils.apiCall('/chat/agent/api-key', {
                method: 'PUT',
                body: JSON.stringify({
                    provider: provider,
                    api_key: apiKey
                })
            });

            if (response.error_code === 0) {
                Utils.showAlert(`API key updated successfully for ${provider}`, 'success');
                Utils.showResponse('apiKeyResponse', response);

                // Update agent display with the returned data
                if (response.data) {
                    this.displayAgentConfigUpdate(response.data);
                }

                // Clear the form
                document.getElementById('apiKey').value = '';

                // Refresh agent data
                this.loadCurrentAgent();
            } else {
                throw new Error(response.message || 'Failed to update API key');
            }
        } catch (error) {
            console.error('Update API key error:', error);
            Utils.showAlert(`Failed to update API key: ${error.message}`, 'danger');
            Utils.showResponse('apiKeyResponse', error.message, true);
        } finally {
            Utils.hideLoading(submitBtn);
        }
    },

    /**
     * Display agent configuration update information
     */
    displayAgentConfigUpdate(agentData) {
        // Pre-fill the configuration form with updated agent data
        if (agentData.model_provider) {
            document.getElementById('configProvider').value = agentData.model_provider;
        }
        if (agentData.model_name) {
            document.getElementById('configModel').value = agentData.model_name;
        }
        if (agentData.temperature !== undefined) {
            document.getElementById('configTemperature').value = agentData.temperature;
        }
        if (agentData.max_tokens !== undefined) {
            document.getElementById('configMaxTokens').value = agentData.max_tokens;
        }
        if (agentData.default_system_prompt) {
            document.getElementById('configSystemPrompt').value = agentData.default_system_prompt;
        }
    },

    /**
     * Update agent configuration
     */
    async updateAgentConfig() {
        if (!AuthManager.isAuthenticated()) {
            Utils.showAlert('Please authenticate first', 'warning');
            return;
        }

        const config = {
            model_provider: document.getElementById('configProvider').value,
            model_name: document.getElementById('configModel').value,
            temperature: parseFloat(document.getElementById('configTemperature').value),
            max_tokens: parseInt(document.getElementById('configMaxTokens').value),
            default_system_prompt: document.getElementById('configSystemPrompt').value
        };
        alert('Updating agent configuration with: ' + JSON.stringify(config));

        const submitBtn = document.querySelector('#agentConfigForm button[type="submit"]');
        Utils.showLoading(submitBtn);

        try {
            const response = await Utils.apiCall('/chat/agent/config', {
                method: 'PUT',
                body: JSON.stringify(config)
            });

            if (response.error_code === 0) {
                Utils.showAlert('Agent configuration updated successfully', 'success');
                Utils.showResponse('agentConfigResponse', response);

                // Refresh agent data
                this.loadCurrentAgent();
            } else {
                throw new Error(response.message || 'Failed to update agent configuration');
            }
        } catch (error) {
            console.error('Update agent config error:', error);
            Utils.showAlert(`Failed to update agent configuration: ${error.message}`, 'danger');
            Utils.showResponse('agentConfigResponse', error.message, true);
        } finally {
            Utils.hideLoading(submitBtn);
        }
    },

    /**
     * Validate agent configuration
     */
    async validateAgent() {
        if (!AuthManager.isAuthenticated()) {
            Utils.showAlert('Please authenticate first', 'warning');
            return;
        }

        const validateBtn = document.getElementById('validateAgentBtn');
        Utils.showLoading(validateBtn);

        try {
            const response = await Utils.apiCall('/chat/validate', {
                method: 'POST',
                body: JSON.stringify({
                    test_message: "Hello, this is a test message to validate the agent configuration."
                })
            });

            if (response.error_code === 0) {
                Utils.showAlert('Agent validation successful!', 'success');
                Utils.showResponse('agentConfigResponse', response);
            } else {
                throw new Error(response.message || 'Agent validation failed');
            }
        } catch (error) {
            console.error('Validate agent error:', error);
            Utils.showAlert(`Agent validation failed: ${error.message}`, 'danger');
            Utils.showResponse('agentConfigResponse', error.message, true);
        } finally {
            Utils.hideLoading(validateBtn);
        }
    },

    /**
     * Toggle API key visibility
     */
    toggleApiKeyVisibility() {
        const apiKeyInput = document.getElementById('apiKey');
        const toggleBtn = document.getElementById('toggleApiKey');
        const icon = toggleBtn.querySelector('i');

        if (apiKeyInput.type === 'password') {
            apiKeyInput.type = 'text';
            icon.className = 'fas fa-eye-slash';
        } else {
            apiKeyInput.type = 'password';
            icon.className = 'fas fa-eye';
        }
    }
};

// Export for use in other modules
window.AgentManager = AgentManager;
