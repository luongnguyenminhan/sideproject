/**
 * Authentication Manager for Agent Test Dashboard
 */

const AuthManager = {
    /**
     * Initialize authentication module
     */
    init() {
        this.setupEventListeners();
        this.checkExistingAuth();
    },
    
    /**
     * Set up event listeners for authentication
     */
    setupEventListeners() {
        // Authenticate button
        document.getElementById('authenticateBtn').addEventListener('click', () => {
            this.authenticate();
        });
        
        // Logout button
        document.getElementById('logoutBtn').addEventListener('click', () => {
            this.logout();
        });
        
        // Toggle token visibility
        document.getElementById('toggleToken').addEventListener('click', () => {
            this.toggleTokenVisibility();
        });
        
        // Enter key in token input
        document.getElementById('jwtToken').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.authenticate();
            }
        });
    },
    
    /**
     * Check for existing authentication
     */
    checkExistingAuth() {
        const token = localStorage.getItem('jwt_token');
        const userProfile = localStorage.getItem('user_profile');
        
        if (token && userProfile) {
            document.getElementById('jwtToken').value = token;
            this.updateAuthStatus(true, JSON.parse(userProfile));
            this.syncWithLegacyAuth();
        }
    },
    
    /**
     * Authenticate user with JWT token
     */
    async authenticate() {
        const tokenInput = document.getElementById('jwtToken');
        const token = tokenInput.value.trim();
        
        if (!token) {
            Utils.showAlert('Please enter a JWT token', 'warning');
            return;
        }
        
        const authBtn = document.getElementById('authenticateBtn');
        Utils.showLoading(authBtn);
        
        try {
            // Store token temporarily
            localStorage.setItem('jwt_token', token);
            
            // Call /users/me endpoint to verify token
            const response = await Utils.apiCall('/users/me');
            
            if (response.error_code === 0) {
                const userProfile = response.data;
                
                // Store user profile
                localStorage.setItem('user_profile', JSON.stringify(userProfile));
                
                // Update UI
                this.updateAuthStatus(true, userProfile);
                Utils.showAlert(`Successfully authenticated as ${userProfile.username || userProfile.email}`, 'success');
                
                // Show response
                Utils.showResponse('authResponse', response);
                
                // Sync with legacy auth variables
                this.syncWithLegacyAuth();
                
                // Enable other tabs
                this.enableTabs();
                
            } else {
                throw new Error(response.message || 'Authentication failed');
            }
        } catch (error) {
            console.error('Authentication error:', error);
            
            // Clear stored token on failure
            localStorage.removeItem('jwt_token');
            localStorage.removeItem('user_profile');
            
            this.updateAuthStatus(false);
            Utils.showAlert(`Authentication failed: ${error.message}`, 'danger');
            Utils.showResponse('authResponse', error.message, true);
            
        } finally {
            Utils.hideLoading(authBtn);
        }
    },
    
    /**
     * Sync with legacy authentication variables
     */
    syncWithLegacyAuth() {
        const token = localStorage.getItem('jwt_token');
        if (token) {
            // Update legacy variables
            window.authToken = token;
            window.isAuthenticated = true;
            
            // Update legacy input field if it exists
            const accessTokenInput = document.getElementById('accessToken');
            if (accessTokenInput) {
                accessTokenInput.value = token;
            }
        }
    },
    
    /**
     * Logout user
     */
    logout() {
        // Clear all stored data
        Utils.clearAuth();
        
        // Clear legacy variables
        window.authToken = '';
        window.isAuthenticated = false;
        
        // Reset UI
        this.updateAuthStatus(false);
        document.getElementById('jwtToken').value = '';
        Utils.hideResponse('authResponse');
        
        // Clear legacy input
        const accessTokenInput = document.getElementById('accessToken');
        if (accessTokenInput) {
            accessTokenInput.value = '';
        }
        
        // Disable other tabs
        this.disableTabs();
        
        // Show logout message
        Utils.showAlert('Successfully logged out', 'info');
        
        // Switch to auth tab
        const authTab = new bootstrap.Tab(document.getElementById('auth-tab'));
        authTab.show();
    },
    
    /**
     * Update authentication status in UI
     */
    updateAuthStatus(isAuthenticated, userProfile = null) {
        const authStatus = document.getElementById('authStatus');
        const userInfo = document.getElementById('userInfo');
        const userName = document.getElementById('userName');
        const logoutBtn = document.getElementById('logoutBtn');
        const userProfileDiv = document.getElementById('userProfile');
        
        if (isAuthenticated && userProfile) {
            // Update status badge
            authStatus.textContent = 'Authenticated';
            authStatus.className = 'badge bg-success authenticated';
            
            // Show user info
            userName.textContent = userProfile.username || userProfile.email || 'User';
            userInfo.style.display = 'block';
            
            // Show logout button
            logoutBtn.style.display = 'inline-block';
            
            // Update user profile display
            userProfileDiv.innerHTML = this.renderUserProfile(userProfile);
            
        } else {
            // Update status badge
            authStatus.textContent = 'Not Authenticated';
            authStatus.className = 'badge bg-danger unauthenticated';
            
            // Hide user info
            userInfo.style.display = 'none';
            
            // Hide logout button
            logoutBtn.style.display = 'none';
            
            // Reset user profile display
            userProfileDiv.innerHTML = '<div class="text-muted">Please authenticate to see profile</div>';
        }
    },
    
    /**
     * Render user profile information
     */
    renderUserProfile(userProfile) {
        return `
            <div class="user-profile">
                <div class="mb-2">
                    <strong>ID:</strong> ${userProfile.id || 'N/A'}
                </div>
                <div class="mb-2">
                    <strong>Name:</strong> ${userProfile.name || userProfile.first_name && userProfile.last_name ? `${userProfile.first_name} ${userProfile.last_name}` : 'N/A'}
                </div>
                <div class="mb-2">
                    <strong>Email:</strong> ${userProfile.email || 'N/A'}
                </div>
                <div class="mb-2">
                    <strong>Username:</strong> ${userProfile.username || 'N/A'}
                </div>
                <div class="mb-2">
                    <strong>Role:</strong> 
                    <span class="badge bg-primary">${userProfile.role || 'user'}</span>
                </div>
                <div class="mb-2">
                    <strong>Status:</strong> 
                    <span class="badge bg-${userProfile.confirmed ? 'success' : 'warning'}">
                        ${userProfile.confirmed ? 'Confirmed' : 'Pending'}
                    </span>
                </div>
                ${userProfile.profile_picture ? `
                    <div class="mb-2">
                        <strong>Profile Picture:</strong> 
                        <img src="${userProfile.profile_picture}" alt="Profile" class="rounded-circle ms-2" style="width: 32px; height: 32px;">
                    </div>
                ` : ''}
                <div class="mb-2">
                    <strong>Created:</strong> ${Utils.formatTimestamp(userProfile.create_date)}
                </div>
                <div class="mb-2">
                    <strong>Updated:</strong> ${Utils.formatTimestamp(userProfile.update_date)}
                </div>
                ${userProfile.locale ? `
                    <div class="mb-2">
                        <strong>Locale:</strong> ${userProfile.locale}
                    </div>
                ` : ''}
            </div>
        `;
    },
    
    /**
     * Toggle token input visibility
     */
    toggleTokenVisibility() {
        const tokenInput = document.getElementById('jwtToken');
        const toggleBtn = document.getElementById('toggleToken');
        const icon = toggleBtn.querySelector('i');
        
        if (tokenInput.type === 'password') {
            tokenInput.type = 'text';
            icon.className = 'fas fa-eye-slash';
        } else {
            tokenInput.type = 'password';
            icon.className = 'fas fa-eye';
        }
    },
    
    /**
     * Enable other tabs after authentication
     */
    enableTabs() {
        const tabs = ['agent-tab', 'chat-tab', 'conversations-tab', 'agent-config-tab'];
        tabs.forEach(tabId => {
            const tab = document.getElementById(tabId);
            if (tab) {
                tab.classList.remove('disabled');
                tab.removeAttribute('aria-disabled');
            }
        });
    },
    
    /**
     * Disable other tabs when not authenticated
     */
    disableTabs() {
        const tabs = ['agent-tab', 'chat-tab', 'conversations-tab', 'agent-config-tab'];
        tabs.forEach(tabId => {
            const tab = document.getElementById(tabId);
            if (tab) {
                tab.classList.add('disabled');
                tab.setAttribute('aria-disabled', 'true');
            }
        });
    },
    
    /**
     * Get current user profile
     */
    getCurrentUser() {
        const userProfile = localStorage.getItem('user_profile');
        return userProfile ? JSON.parse(userProfile) : null;
    },
    
    /**
     * Check if user is authenticated
     */
    isAuthenticated() {
        return Utils.isAuthenticated() && this.getCurrentUser() !== null;
    }
};

// Export for use in other modules
window.AuthManager = AuthManager;
