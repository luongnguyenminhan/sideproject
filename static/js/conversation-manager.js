/**
 * Conversation Manager for Agent Test Dashboard
 */

const ConversationManager = {
    currentPage: 1,
    pageSize: 10,
    totalPages: 1,
    conversations: [],
    selectedConversationId: null,

    /**
     * Initialize conversation management module
     */
    init() {
        this.setupEventListeners();
    },

    /**
     * Set up event listeners for conversation management
     */
    setupEventListeners() {
        // Refresh conversations
        document.getElementById('refreshConversationsBtn').addEventListener('click', () => {
            this.refreshConversations();
        });

        // Create conversation form
        document.getElementById('createConversationForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.createConversation();
        });

        // Update conversation form
        document.getElementById('updateConversationForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.updateConversation();
        });
    },

    /**
     * Refresh conversations list
     */
    async refreshConversations() {
        if (!AuthManager.isAuthenticated()) {
            Utils.showAlert('Please authenticate first', 'warning');
            return;
        }

        const refreshBtn = document.getElementById('refreshConversationsBtn');
        Utils.showLoading(refreshBtn);

        try {
            const response = await Utils.apiCall(`/conversations/?page=${this.currentPage}&page_size=${this.pageSize}`);

            if (response.error_code === 0) {
                this.conversations = response.data.items;
                this.updateConversationsList(response.data);
                this.updatePagination(response.data.paging);
                Utils.showAlert('Conversations loaded successfully', 'success', 2000);
            } else {
                throw new Error(response.message || 'Failed to load conversations');
            }
        } catch (error) {
            console.error('Load conversations error:', error);
            Utils.showAlert(`Failed to load conversations: ${error.message}`, 'danger');
            this.showEmptyConversationsList();
        } finally {
            Utils.hideLoading(refreshBtn);
        }
    },

    /**
     * Update conversations table
     */
    updateConversationsList(data) {
        const tbody = document.getElementById('conversationsTableBody');

        if (!data.items || data.items.length === 0) {
            this.showEmptyConversationsList();
            return;
        }

        let html = '';
        data.items.forEach(conversation => {
            html += `
                <tr onclick="ConversationManager.selectConversation('${conversation.id}')" style="cursor: pointer;">
                    <td>
                        <strong>${Utils.escapeHtml(conversation.name)}</strong>
                        ${conversation.system_prompt ? `<br><small class="text-muted">${Utils.truncateText(conversation.system_prompt, 50)}</small>` : ''}
                    </td>
                    <td>
                        <small>${Utils.formatTimestamp(conversation.created_at)}</small>
                    </td>
                    <td>
                        <span class="badge bg-info">${conversation.message_count || 0}</span>
                    </td>
                    <td>
                        <div class="btn-group btn-group-sm">
                            <button class="btn btn-outline-primary" onclick="event.stopPropagation(); ConversationManager.viewConversationDetails('${conversation.id}')" title="View Details">
                                <i class="fas fa-eye"></i>
                            </button>
                            <button class="btn btn-outline-warning" onclick="event.stopPropagation(); ConversationManager.editConversation('${conversation.id}')" title="Edit">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-outline-danger" onclick="event.stopPropagation(); ConversationManager.deleteConversation('${conversation.id}', '${Utils.escapeHtml(conversation.name)}')" title="Delete">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        });

        tbody.innerHTML = html;
    },

    /**
     * Show empty conversations message
     */
    showEmptyConversationsList() {
        const tbody = document.getElementById('conversationsTableBody');
        tbody.innerHTML = `
            <tr>
                <td colspan="4" class="text-center text-muted py-4">
                    <i class="fas fa-comments fa-2x mb-2"></i><br>
                    No conversations found. Create your first conversation to get started.
                </td>
            </tr>
        `;
    },

    /**
     * Update pagination controls
     */
    updatePagination(paging) {
        const pagination = document.getElementById('conversationsPagination');

        if (paging.total_pages <= 1) {
            pagination.style.display = 'none';
            return;
        }

        pagination.style.display = 'block';
        this.totalPages = paging.total_pages;
        this.currentPage = paging.page;

        let html = '<nav><ul class="pagination pagination-sm">';

        // Previous button
        html += `
            <li class="page-item ${this.currentPage === 1 ? 'disabled' : ''}">
                <a class="page-link" href="#" onclick="ConversationManager.goToPage(${this.currentPage - 1})">Previous</a>
            </li>
        `;

        // Page numbers
        for (let i = 1; i <= this.totalPages; i++) {
            if (i === this.currentPage || i === 1 || i === this.totalPages || Math.abs(i - this.currentPage) <= 2) {
                html += `
                    <li class="page-item ${i === this.currentPage ? 'active' : ''}">
                        <a class="page-link" href="#" onclick="ConversationManager.goToPage(${i})">${i}</a>
                    </li>
                `;
            } else if (i === this.currentPage - 3 || i === this.currentPage + 3) {
                html += '<li class="page-item disabled"><span class="page-link">...</span></li>';
            }
        }

        // Next button
        html += `
            <li class="page-item ${this.currentPage === this.totalPages ? 'disabled' : ''}">
                <a class="page-link" href="#" onclick="ConversationManager.goToPage(${this.currentPage + 1})">Next</a>
            </li>
        `;

        html += '</ul></nav>';
        pagination.innerHTML = html;
    },

    /**
     * Go to specific page
     */
    goToPage(page) {
        if (page < 1 || page > this.totalPages || page === this.currentPage) {
            return;
        }

        this.currentPage = page;
        this.refreshConversations();
    },

    /**
     * Select conversation for details view
     */
    selectConversation(conversationId) {
        this.selectedConversationId = conversationId;

        // Highlight selected row
        document.querySelectorAll('#conversationsTableBody tr').forEach(row => {
            row.classList.remove('table-active');
        });

        const selectedRow = document.querySelector(`#conversationsTableBody tr[onclick*="${conversationId}"]`);
        if (selectedRow) {
            selectedRow.classList.add('table-active');
        }

        this.loadConversationDetails(conversationId);
        this.loadConversationMessages(conversationId);
    },

    /**
     * Load conversation details
     */
    async loadConversationDetails(conversationId) {
        try {
            const response = await Utils.apiCall(`/conversations/${conversationId}`);

            if (response.error_code === 0) {
                this.displayConversationDetails(response.data);
            } else {
                throw new Error(response.message || 'Failed to load conversation details');
            }
        } catch (error) {
            console.error('Load conversation details error:', error);
            this.displayConversationDetails(null);
        }
    },

    /**
     * Display conversation details
     */
    displayConversationDetails(conversation) {
        const container = document.getElementById('conversationDetails');

        if (!conversation) {
            container.innerHTML = '<div class="text-muted">Failed to load conversation details</div>';
            return;
        }

        container.innerHTML = `
            <div class="conversation-details">
                <div class="mb-3">
                    <h6 class="mb-1">${Utils.escapeHtml(conversation.name)}</h6>
                    <small class="text-muted">ID: ${conversation.id}</small>
                </div>
                
                <div class="mb-2">
                    <strong>Created:</strong><br>
                    <small>${Utils.formatTimestamp(conversation.created_at)}</small>
                </div>
                
                <div class="mb-2">
                    <strong>Last Updated:</strong><br>
                    <small>${Utils.formatTimestamp(conversation.updated_at)}</small>
                </div>
                
                <div class="mb-2">
                    <strong>Messages:</strong><br>
                    <span class="badge bg-info">${conversation.message_count || 0}</span>
                </div>
                
                ${conversation.system_prompt ? `
                    <div class="mb-2">
                        <strong>System Prompt:</strong><br>
                        <div class="bg-light p-2 rounded mt-1" style="max-height: 100px; overflow-y: auto; font-size: 0.875rem;">
                            ${Utils.escapeHtml(conversation.system_prompt)}
                        </div>
                    </div>
                ` : ''}
                
                <div class="mt-3">
                    <div class="d-grid gap-2">
                        <button class="btn btn-sm btn-primary" onclick="ConversationManager.openInChat('${conversation.id}')">
                            <i class="fas fa-comments"></i> Open in Chat
                        </button>
                        <button class="btn btn-sm btn-outline-warning" onclick="ConversationManager.editConversation('${conversation.id}')">
                            <i class="fas fa-edit"></i> Edit
                        </button>
                        <button class="btn btn-sm btn-outline-danger" onclick="ConversationManager.deleteConversation('${conversation.id}', '${Utils.escapeHtml(conversation.name)}')">
                            <i class="fas fa-trash"></i> Delete
                        </button>
                    </div>
                </div>
            </div>
        `;
    },

    /**
     * Load conversation messages for preview
     */
    async loadConversationMessages(conversationId) {
        try {
            const response = await Utils.apiCall(`/conversations/${conversationId}/messages?page=1&page_size=10`);

            if (response.error_code === 0) {
                this.displayMessagesPreview(response.data.items);
            } else {
                throw new Error(response.message || 'Failed to load messages');
            }
        } catch (error) {
            console.error('Load messages error:', error);
            this.displayMessagesPreview(null);
        }
    },

    /**
     * Display messages preview
     */
    displayMessagesPreview(messages) {
        const container = document.getElementById('messagesPreview');

        if (!messages || messages.length === 0) {
            container.innerHTML = '<div class="text-muted">No messages in this conversation</div>';
            return;
        }

        let html = '';
        messages.reverse().forEach(message => { // Show newest first in preview
            html += `
                <div class="message-preview">
                    <div class="role">${message.role === 'user' ? 'You' : 'Assistant'}</div>
                    <div class="content">${Utils.escapeHtml(Utils.truncateText(message.content, 150))}</div>
                    <div class="timestamp">${Utils.formatTimestamp(message.timestamp)}</div>
                </div>
            `;
        });

        container.innerHTML = html;
    },

    /**
     * Create new conversation
     */
    async createConversation() {
        const form = document.getElementById('createConversationForm');
        const formData = new FormData(form);

        const data = {
            name: formData.get('name').trim(),
            initial_message: formData.get('initial_message')?.trim() || null,
            system_prompt: formData.get('system_prompt')?.trim() || null
        };

        if (!data.name) {
            Utils.showAlert('Conversation name is required', 'warning');
            return;
        }

        const submitBtn = form.querySelector('button[type="submit"]');
        Utils.showLoading(submitBtn);

        try {
            const response = await Utils.apiCall('/conversations/', {
                method: 'POST',
                body: JSON.stringify(data)
            });

            if (response.error_code === 0) {
                Utils.showAlert('Conversation created successfully', 'success');

                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('createConversationModal'));
                modal.hide();

                // Reset form
                form.reset();

                // Refresh conversations list
                this.refreshConversations();

                // Select the new conversation
                setTimeout(() => {
                    this.selectConversation(response.data.id);
                }, 500);

            } else {
                throw new Error(response.message || 'Failed to create conversation');
            }
        } catch (error) {
            console.error('Create conversation error:', error);
            Utils.showAlert(`Failed to create conversation: ${error.message}`, 'danger');
        } finally {
            Utils.hideLoading(submitBtn);
        }
    },

    /**
     * Edit conversation
     */
    editConversation(conversationId) {
        const conversation = this.conversations.find(c => c.id === conversationId);
        if (!conversation) {
            Utils.showAlert('Conversation not found', 'warning');
            return;
        }

        // Fill update form
        const form = document.getElementById('updateConversationForm');
        form.querySelector('input[name="conversation_id"]').value = conversationId;
        form.querySelector('input[name="name"]').value = conversation.name;
        form.querySelector('textarea[name="system_prompt"]').value = conversation.system_prompt || '';

        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('updateConversationModal'));
        modal.show();
    },

    /**
     * Update conversation
     */
    async updateConversation() {
        const form = document.getElementById('updateConversationForm');
        const formData = new FormData(form);

        const conversationId = formData.get('conversation_id');
        const data = {
            name: formData.get('name').trim(),
            system_prompt: formData.get('system_prompt')?.trim() || null
        };

        if (!data.name) {
            Utils.showAlert('Conversation name is required', 'warning');
            return;
        }

        const submitBtn = form.querySelector('button[type="submit"]');
        Utils.showLoading(submitBtn);

        try {
            const response = await Utils.apiCall(`/conversations/${conversationId}`, {
                method: 'PUT',
                body: JSON.stringify(data)
            });

            if (response.error_code === 0) {
                Utils.showAlert('Conversation updated successfully', 'success');

                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('updateConversationModal'));
                modal.hide();

                // Refresh conversations list
                this.refreshConversations();

                // Update details if this conversation is selected
                if (this.selectedConversationId === conversationId) {
                    this.loadConversationDetails(conversationId);
                }

            } else {
                throw new Error(response.message || 'Failed to update conversation');
            }
        } catch (error) {
            console.error('Update conversation error:', error);
            Utils.showAlert(`Failed to update conversation: ${error.message}`, 'danger');
        } finally {
            Utils.hideLoading(submitBtn);
        }
    },

    /**
     * Delete conversation
     */
    async deleteConversation(conversationId, conversationName) {
        if (!confirm(`Are you sure you want to delete "${conversationName}"?\n\nThis action cannot be undone and will delete all messages in this conversation.`)) {
            return;
        }

        try {
            const response = await Utils.apiCall(`/conversations/${conversationId}`, {
                method: 'DELETE'
            });

            if (response.error_code === 0) {
                Utils.showAlert('Conversation deleted successfully', 'success');

                // Clear details if this conversation was selected
                if (this.selectedConversationId === conversationId) {
                    this.selectedConversationId = null;
                    document.getElementById('conversationDetails').innerHTML = '<div class="text-muted">Select a conversation to view details</div>';
                    document.getElementById('messagesPreview').innerHTML = '<div class="text-muted">Select a conversation to view messages</div>';
                }

                // Refresh conversations list
                this.refreshConversations();

            } else {
                throw new Error(response.message || 'Failed to delete conversation');
            }
        } catch (error) {
            console.error('Delete conversation error:', error);
            Utils.showAlert(`Failed to delete conversation: ${error.message}`, 'danger');
        }
    },

    /**
     * Open conversation in chat tab
     */
    openInChat(conversationId) {
        // Switch to chat tab
        const chatTab = new bootstrap.Tab(document.getElementById('chat-tab'));
        chatTab.show();

        // Select conversation in chat interface
        setTimeout(() => {
            const chatSelect = document.getElementById('chatConversationSelect');
            chatSelect.value = conversationId;

            // Trigger change event
            const event = new Event('change');
            chatSelect.dispatchEvent(event);

            Utils.showAlert('Conversation opened in chat', 'info', 2000);
        }, 100);
    },

    /**
     * View conversation details (same as select)
     */
    viewConversationDetails(conversationId) {
        this.selectConversation(conversationId);
    }
};

// Export for use in other modules
window.ConversationManager = ConversationManager;
