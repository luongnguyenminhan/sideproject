# Google OAuth Authentication Test Suite

This directory contains static HTML, CSS, and JavaScript files to test the simplified Google OAuth authentication flow.

## Files

- **`index.html`** - Main test page with authentication interface
- **`styles.css`** - Modern styling for the test interface  
- **`auth-test.js`** - JavaScript test suite for OAuth functionality
- **`README.md`** - This documentation file

## Features

### Authentication Testing
- **Google OAuth Login** - Test the `/auth/google/login` endpoint
- **Direct Google Auth** - Test the `/auth/google/auth` endpoint  
- **Token Revocation** - Test the `/auth/google/revoke` endpoint
- **User Info Display** - Show authenticated user information

### API Endpoint Testing
- Test individual endpoints through the interface
- View formatted API responses
- Handle both JSON and HTML responses

### Activity Logging
- Real-time logging of authentication actions
- Color-coded log entries (info, success, error)
- Scrollable log history with timestamps

### Token Management
- JWT token parsing and validation
- Token expiry checking
- Secure token storage in localStorage

## Usage

### 1. Serve the Static Files

You can serve these files in several ways:

#### Option A: Using your FastAPI application
Add a static file route to your FastAPI app to serve these files:

```python
from fastapi.staticfiles import StaticFiles

app.mount("/static", StaticFiles(directory="app/static"), name="static")
```

Then access: `http://localhost:8000/static/index.html`

#### Option B: Using Python's built-in server
```bash
cd app/static
python -m http.server 8080
```

Then access: `http://localhost:8080`

#### Option C: Using Node.js http-server
```bash
cd app/static
npx http-server -p 8080
```

### 2. Test the Authentication Flow

1. **Open the test page** in your browser
2. **Click "Sign in with Google"** to test the full OAuth flow
3. **Use "Direct Google Auth"** to test direct OAuth redirection
4. **Monitor the logs** for detailed activity information
5. **Test API endpoints** using the endpoint testing section

### 3. OAuth Callback Testing

The test suite automatically handles OAuth callbacks:
- Detects authorization codes in URL parameters
- Handles error responses from Google OAuth
- Processes JWT tokens returned from your backend

### 4. Console Testing

The browser console provides additional utilities:

```javascript
// Check current authentication status
authTestSuite.checkAuthStatus()

// Clear all authentication data
authTestSuite.clearAuthData()

// Parse a JWT token
OAuthUtils.parseJWT('your-jwt-token-here')

// Check if token is expired
OAuthUtils.isTokenExpired('your-jwt-token-here')

// Get detailed token information
OAuthUtils.formatTokenInfo('your-jwt-token-here')
```

## Expected Authentication Flow

1. **User clicks login** → Redirects to `/auth/google/login`
2. **Google OAuth consent** → User authorizes your application
3. **Callback handling** → Google redirects to `/auth/google/callback`
4. **Token generation** → Your backend creates JWT token
5. **User authenticated** → Token stored and user info displayed

## Troubleshooting

### Common Issues

**OAuth Redirect URI Mismatch**
- Ensure your Google OAuth app has the correct redirect URI configured
- Check that the callback URL matches your backend endpoint

**CORS Errors**
- Make sure your FastAPI app has CORS properly configured
- The static files should be served from the same domain as your API

**Token Issues**
- Check browser console for JWT parsing errors
- Verify token format and signature

### Debug Information

The test suite provides extensive logging:
- All authentication attempts
- API response details
- Token parsing results
- Error messages with context

## Security Notes

- Tokens are stored in localStorage for testing purposes only
- In production, consider using secure HTTP-only cookies
- Always validate tokens on the backend
- Implement proper token refresh mechanisms

## Customization

You can customize the test suite by:
- Modifying the `baseURL` in `auth-test.js` for different environments
- Adding new endpoint tests in the dropdown
- Extending the logging functionality
- Adding custom authentication flows

## Dependencies

- Modern web browser with ES6+ support
- Google Fonts (Inter) - loaded from CDN
- No external JavaScript libraries required
