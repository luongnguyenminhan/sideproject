/**
 * Google OAuth Authentication Test Suite
 * Handles testing of the simplified authentication flow
 */

class AuthTestSuite {
    constructor() {
        this.authToken = localStorage.getItem('auth_token');
        this.userInfo = null;
        this.baseURL = window.location.origin;
        
        this.initializeElements();
        this.attachEventListeners();
        this.checkAuthStatus();
        this.logActivity('info', 'AuthTestSuite initialized');
    }

    initializeElements() {
        // Status elements
        this.authStatus = document.getElementById('auth-status');
        this.userInfoDiv = document.getElementById('user-info');
        this.userAvatar = document.getElementById('user-avatar');
        this.userName = document.getElementById('user-name');
        this.userEmail = document.getElementById('user-email');
        this.userId = document.getElementById('user-id');

        // Button elements
        this.loginBtn = document.getElementById('login-btn');
        this.directAuthBtn = document.getElementById('direct-auth-btn');
        this.revokeBtn = document.getElementById('revoke-btn');
        this.refreshInfoBtn = document.getElementById('refresh-info-btn');
        this.testEndpointBtn = document.getElementById('test-endpoint-btn');
        this.clearLogsBtn = document.getElementById('clear-logs-btn');

        // Other elements
        this.authenticatedActions = document.getElementById('authenticated-actions');
        this.endpointSelect = document.getElementById('endpoint-select');
        this.responseContent = document.getElementById('response-content');
        this.logsContainer = document.getElementById('logs');
    }

    attachEventListeners() {
        this.loginBtn.addEventListener('click', () => this.handleGoogleLogin());
        this.directAuthBtn.addEventListener('click', () => this.handleDirectAuth());
        this.revokeBtn.addEventListener('click', () => this.handleRevokeToken());
        this.refreshInfoBtn.addEventListener('click', () => this.handleRefreshInfo());
        this.testEndpointBtn.addEventListener('click', () => this.handleTestEndpoint());
        this.clearLogsBtn.addEventListener('click', () => this.clearLogs());

        // Handle OAuth callback if present in URL
        this.handleOAuthCallback();
    }

    async checkAuthStatus() {
        if (this.authToken) {
            try {
                // In a real app, you'd validate the token with your backend
                this.logActivity('info', 'Found stored auth token, checking validity...');
                await this.fetchUserInfo();
            } catch (error) {
                this.logActivity('error', 'Stored token appears to be invalid');
                this.clearAuthData();
            }
        } else {
            this.updateAuthStatus(false);
        }
    }

    async handleGoogleLogin() {
        this.logActivity('info', 'Initiating Google OAuth login...');
        this.setButtonLoading(this.loginBtn, true);

        try {
            // Redirect to the Google OAuth login page
            window.location.href = `${this.baseURL}/auth/google/login`;
        } catch (error) {
            this.logActivity('error', `Login failed: ${error.message}`);
            this.setButtonLoading(this.loginBtn, false);
        }
    }

    async handleDirectAuth() {
        this.logActivity('info', 'Initiating direct Google OAuth...');
        this.setButtonLoading(this.directAuthBtn, true);

        try {
            // Redirect directly to Google OAuth
            window.location.href = `${this.baseURL}/auth/google/auth`;
        } catch (error) {
            this.logActivity('error', `Direct auth failed: ${error.message}`);
            this.setButtonLoading(this.directAuthBtn, false);
        }
    }

    async handleRevokeToken() {
        if (!this.authToken) {
            this.logActivity('error', 'No token to revoke');
            return;
        }

        this.logActivity('info', 'Revoking Google OAuth token...');
        this.setButtonLoading(this.revokeBtn, true);

        try {
            const response = await fetch(`${this.baseURL}/auth/google/revoke`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.authToken}`,
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();

            if (response.ok) {
                this.logActivity('success', 'Token revoked successfully');
                this.clearAuthData();
                this.updateResponseDisplay(data);
            } else {
                this.logActivity('error', `Token revocation failed: ${data.message || 'Unknown error'}`);
                this.updateResponseDisplay(data);
            }
        } catch (error) {
            this.logActivity('error', `Network error during token revocation: ${error.message}`);
        } finally {
            this.setButtonLoading(this.revokeBtn, false);
        }
    }

    async handleRefreshInfo() {
        this.logActivity('info', 'Refreshing user information...');
        this.setButtonLoading(this.refreshInfoBtn, true);

        try {
            await this.fetchUserInfo();
            this.logActivity('success', 'User information refreshed');
        } catch (error) {
            this.logActivity('error', `Failed to refresh user info: ${error.message}`);
        } finally {
            this.setButtonLoading(this.refreshInfoBtn, false);
        }
    }

    async handleTestEndpoint() {
        const endpoint = this.endpointSelect.value;
        this.logActivity('info', `Testing endpoint: ${endpoint}`);
        this.setButtonLoading(this.testEndpointBtn, true);

        try {
            let options = {
                method: 'GET',
                headers: {}
            };

            // Add authorization header if we have a token
            if (this.authToken && (endpoint.includes('/revoke') || endpoint.includes('/callback'))) {
                options.headers['Authorization'] = `Bearer ${this.authToken}`;
            }

            // Handle POST endpoints
            if (endpoint.includes('/revoke')) {
                options.method = 'POST';
                options.headers['Content-Type'] = 'application/json';
            }

            const response = await fetch(`${this.baseURL}${endpoint}`, options);
            
            let responseData;
            const contentType = response.headers.get('content-type');
            
            if (contentType && contentType.includes('application/json')) {
                responseData = await response.json();
            } else {
                responseData = await response.text();
            }

            this.updateResponseDisplay({
                status: response.status,
                statusText: response.statusText,
                headers: Object.fromEntries(response.headers.entries()),
                data: responseData
            });

            this.logActivity('success', `Endpoint test completed: ${response.status} ${response.statusText}`);
        } catch (error) {
            this.logActivity('error', `Endpoint test failed: ${error.message}`);
            this.updateResponseDisplay({ error: error.message });
        } finally {
            this.setButtonLoading(this.testEndpointBtn, false);
        }
    }

    handleOAuthCallback() {
        const urlParams = new URLSearchParams(window.location.search);
        const code = urlParams.get('code');
        const error = urlParams.get('error');
        const token = urlParams.get('token');

        if (error) {
            this.logActivity('error', `OAuth error: ${error}`);
            // Clean up URL
            window.history.replaceState({}, document.title, window.location.pathname);
            return;
        }

        if (code) {
            this.logActivity('success', 'OAuth authorization code received');
            // In a real app, this would be handled by the callback endpoint
            // Clean up URL
            window.history.replaceState({}, document.title, window.location.pathname);
            return;
        }

        if (token) {
            this.logActivity('success', 'OAuth token received via URL parameter');
            this.authToken = token;
            localStorage.setItem('auth_token', token);
            this.fetchUserInfo();
            // Clean up URL
            window.history.replaceState({}, document.title, window.location.pathname);
            return;
        }
    }

    async fetchUserInfo() {
        if (!this.authToken) {
            throw new Error('No authentication token available');
        }

        // Simulate fetching user info from your backend
        // In a real app, you'd call your protected user info endpoint
        this.logActivity('info', 'Fetching user information...');
        
        // For testing purposes, we'll decode the JWT token if it's a JWT
        try {
            const tokenParts = this.authToken.split('.');
            if (tokenParts.length === 3) {
                // Looks like a JWT token
                const payload = JSON.parse(atob(tokenParts[1]));
                this.userInfo = {
                    id: payload.sub || payload.user_id || 'unknown',
                    name: payload.name || 'Unknown User',
                    email: payload.email || 'unknown@example.com',
                    picture: payload.picture || 'https://via.placeholder.com/60x60?text=U'
                };
                this.updateAuthStatus(true);
                this.logActivity('success', 'User information loaded from JWT token');
            } else {
                // Mock user info for testing
                this.userInfo = {
                    id: 'test_user_123',
                    name: 'Test User',
                    email: 'test@example.com',
                    picture: 'https://via.placeholder.com/60x60?text=TU'
                };
                this.updateAuthStatus(true);
                this.logActivity('info', 'Using mock user information for testing');
            }
        } catch (error) {
            this.logActivity('error', `Failed to decode user info: ${error.message}`);
            throw error;
        }
    }

    updateAuthStatus(isAuthenticated) {
        if (isAuthenticated && this.userInfo) {
            // Update status message
            this.authStatus.innerHTML = `
                <span class="status-icon">✅</span>
                <span class="status-text">Authenticated</span>
            `;
            this.authStatus.className = 'status-message authenticated';

            // Show user info
            this.userAvatar.src = this.userInfo.picture;
            this.userName.textContent = this.userInfo.name;
            this.userEmail.textContent = this.userInfo.email;
            this.userId.textContent = `ID: ${this.userInfo.id}`;
            
            this.userInfoDiv.style.display = 'flex';
            this.authenticatedActions.style.display = 'block';

            // Update button states
            this.loginBtn.style.display = 'none';
            this.directAuthBtn.style.display = 'none';
        } else {
            // Update status message
            this.authStatus.innerHTML = `
                <span class="status-icon">🔒</span>
                <span class="status-text">Not authenticated</span>
            `;
            this.authStatus.className = 'status-message unauthenticated';

            // Hide user info
            this.userInfoDiv.style.display = 'none';
            this.authenticatedActions.style.display = 'none';

            // Update button states
            this.loginBtn.style.display = 'flex';
            this.directAuthBtn.style.display = 'flex';
        }
    }

    clearAuthData() {
        this.authToken = null;
        this.userInfo = null;
        localStorage.removeItem('auth_token');
        this.updateAuthStatus(false);
        this.logActivity('info', 'Authentication data cleared');
    }

    updateResponseDisplay(data) {
        this.responseContent.textContent = JSON.stringify(data, null, 2);
    }

    setButtonLoading(button, isLoading) {
        if (isLoading) {
            button.classList.add('loading');
            button.disabled = true;
        } else {
            button.classList.remove('loading');
            button.disabled = false;
        }
    }

    logActivity(type, message) {
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry ${type}`;
        logEntry.innerHTML = `
            <span class="log-time">${timestamp}</span>
            <span class="log-message">${message}</span>
        `;
        
        this.logsContainer.appendChild(logEntry);
        this.logsContainer.scrollTop = this.logsContainer.scrollHeight;
    }

    clearLogs() {
        this.logsContainer.innerHTML = `
            <div class="log-entry">
                <span class="log-time">Ready</span>
                <span class="log-message">Logs cleared</span>
            </div>
        `;
        this.logActivity('info', 'Ready for testing');
    }
}

// Utility functions for OAuth testing
const OAuthUtils = {
    /**
     * Parse JWT token payload
     */
    parseJWT: (token) => {
        try {
            const base64Url = token.split('.')[1];
            const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
            const jsonPayload = decodeURIComponent(atob(base64).split('').map(c => {
                return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
            }).join(''));
            return JSON.parse(jsonPayload);
        } catch (error) {
            console.error('Error parsing JWT:', error);
            return null;
        }
    },

    /**
     * Check if JWT token is expired
     */
    isTokenExpired: (token) => {
        const payload = OAuthUtils.parseJWT(token);
        if (!payload || !payload.exp) return true;
        
        const currentTime = Math.floor(Date.now() / 1000);
        return payload.exp < currentTime;
    },

    /**
     * Get time until token expires
     */
    getTokenExpiryTime: (token) => {
        const payload = OAuthUtils.parseJWT(token);
        if (!payload || !payload.exp) return null;
        
        const expiryTime = new Date(payload.exp * 1000);
        return expiryTime;
    },

    /**
     * Format token information for display
     */
    formatTokenInfo: (token) => {
        const payload = OAuthUtils.parseJWT(token);
        if (!payload) return 'Invalid token';
        
        const expiryTime = OAuthUtils.getTokenExpiryTime(token);
        const isExpired = OAuthUtils.isTokenExpired(token);
        
        return {
            userId: payload.sub || payload.user_id,
            email: payload.email,
            name: payload.name,
            issuer: payload.iss,
            audience: payload.aud,
            issuedAt: new Date(payload.iat * 1000),
            expiresAt: expiryTime,
            isExpired: isExpired
        };
    }
};

// Initialize the test suite when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.authTestSuite = new AuthTestSuite();
    
    // Make utilities globally available for console testing
    window.OAuthUtils = OAuthUtils;
    
    // Add some helpful console commands
    console.log('🔧 Google OAuth Test Suite loaded!');
    console.log('Available commands:');
    console.log('- authTestSuite.checkAuthStatus()');
    console.log('- authTestSuite.clearAuthData()');
    console.log('- OAuthUtils.parseJWT(token)');
    console.log('- OAuthUtils.isTokenExpired(token)');
    console.log('- OAuthUtils.formatTokenInfo(token)');
});
