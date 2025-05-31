/**
 * Utility functions for the Agent Test Dashboard
 */

const Utils = {
    // API Configuration
    API_BASE_URL: 'http://localhost:8000/api/v1',
    WS_BASE_URL: 'ws://localhost:8000/api/v1',
    
    /**
     * Show alert message
     */
    showAlert(message, type = 'info', duration = 5000) {
        const alertContainer = document.getElementById('alertContainer');
        const alertId = 'alert-' + Date.now();
        
        const alertHtml = `
            <div id="${alertId}" class="alert alert-${type} alert-dismissible fade show" role="alert">
                <i class="fas fa-${this.getAlertIcon(type)}"></i> ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        alertContainer.insertAdjacentHTML('beforeend', alertHtml);
        
        // Auto-dismiss after duration
        if (duration > 0) {
            setTimeout(() => {
                const alert = document.getElementById(alertId);
                if (alert) {
                    const bsAlert = new bootstrap.Alert(alert);
                    bsAlert.close();
                }
            }, duration);
        }
    },
    
    /**
     * Get FontAwesome icon for alert type
     */
    getAlertIcon(type) {
        const icons = {
            success: 'check-circle',
            danger: 'exclamation-triangle',
            warning: 'exclamation-circle',
            info: 'info-circle',
            primary: 'info-circle',
            secondary: 'info-circle'
        };
        return icons[type] || 'info-circle';
    },
    
    /**
     * Make API call with authentication
     */
    async apiCall(endpoint, options = {}) {
        const token = localStorage.getItem('jwt_token');
        
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                ...(token && { 'Authorization': `Bearer ${token}` })
            }
        };
        
        const mergedOptions = {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...options.headers
            }
        };
        
        try {
            const response = await fetch(`${this.API_BASE_URL}${endpoint}`, mergedOptions);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.message || `HTTP ${response.status}: ${response.statusText}`);
            }
            
            return data;
        } catch (error) {
            console.error('API Call Error:', error);
            throw error;
        }
    },
    
    /**
     * Format JSON with syntax highlighting
     */
    formatJSON(data) {
        if (typeof data === 'string') {
            try {
                data = JSON.parse(data);
            } catch (e) {
                return `<pre>${this.escapeHtml(data)}</pre>`;
            }
        }
        
        const json = JSON.stringify(data, null, 2);
        return `<pre>${this.syntaxHighlight(json)}</pre>`;
    },
    
    /**
     * Syntax highlighting for JSON
     */
    syntaxHighlight(json) {
        json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, function (match) {
            let cls = 'json-number';
            if (/^"/.test(match)) {
                if (/:$/.test(match)) {
                    cls = 'json-key';
                } else {
                    cls = 'json-string';
                }
            } else if (/true|false/.test(match)) {
                cls = 'json-boolean';
            } else if (/null/.test(match)) {
                cls = 'json-null';
            }
            return '<span class="' + cls + '">' + match + '</span>';
        });
    },
    
    /**
     * Escape HTML
     */
    escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    },
    
    /**
     * Show loading state on element
     */
    showLoading(element) {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }
        if (element) {
            element.classList.add('loading');
        }
    },
    
    /**
     * Hide loading state on element
     */
    hideLoading(element) {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }
        if (element) {
            element.classList.remove('loading');
        }
    },
    
    /**
     * Format timestamp for display
     */
    formatTimestamp(timestamp) {
        if (!timestamp) return 'Unknown';
        
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;
        
        // Less than 1 minute
        if (diff < 60000) {
            return 'Just now';
        }
        
        // Less than 1 hour
        if (diff < 3600000) {
            const minutes = Math.floor(diff / 60000);
            return `${minutes}m ago`;
        }
        
        // Less than 1 day
        if (diff < 86400000) {
            const hours = Math.floor(diff / 3600000);
            return `${hours}h ago`;
        }
        
        // More than 1 day
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    },
    
    /**
     * Truncate text
     */
    truncateText(text, maxLength = 100) {
        if (!text || text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    },
    
    /**
     * Debounce function
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    /**
     * Check if user is authenticated
     */
    isAuthenticated() {
        const token = localStorage.getItem('jwt_token');
        return !!token;
    },
    
    /**
     * Clear authentication
     */
    clearAuth() {
        localStorage.removeItem('jwt_token');
        localStorage.removeItem('user_profile');
        localStorage.removeItem('ws_token');
    },
    
    /**
     * Show response in container
     */
    showResponse(containerId, data, isError = false) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        container.style.display = 'block';
        container.innerHTML = `
            <div class="${isError ? 'text-danger' : 'text-success'}">
                <strong>Status:</strong> ${isError ? 'Error' : 'Success'}
            </div>
            ${this.formatJSON(data)}
        `;
    },
    
    /**
     * Hide response container
     */
    hideResponse(containerId) {
        const container = document.getElementById(containerId);
        if (container) {
            container.style.display = 'none';
        }
    },
    
    /**
     * Generate random conversation name
     */
    generateConversationName() {
        const adjectives = ['Quick', 'Smart', 'Creative', 'Helpful', 'Friendly', 'Efficient', 'Intelligent'];
        const nouns = ['Chat', 'Discussion', 'Conversation', 'Talk', 'Session'];
        
        const adjective = adjectives[Math.floor(Math.random() * adjectives.length)];
        const noun = nouns[Math.floor(Math.random() * nouns.length)];
        const number = Math.floor(Math.random() * 1000);
        
        return `${adjective} ${noun} ${number}`;
    },
    
    /**
     * Copy text to clipboard
     */
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            this.showAlert('Copied to clipboard!', 'success', 2000);
        } catch (err) {
            console.error('Failed to copy: ', err);
            this.showAlert('Failed to copy to clipboard', 'danger');
        }
    },
    
    /**
     * Download data as JSON file
     */
    downloadJSON(data, filename = 'data.json') {
        const blob = new Blob([JSON.stringify(data, null, 2)], {
            type: 'application/json'
        });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
};

// Export for use in other modules
window.Utils = Utils;
