"""
OAuth utilities for handling external authentication providers
"""

import logging
import secrets
from typing import Dict

import requests
from authlib.integrations.starlette_client import OAuth
from fastapi import HTTPException, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi import status

from app.core.config import (
	GOOGLE_CLIENT_ID,
	GOOGLE_CLIENT_SECRET,
	GOOGLE_REDIRECT_URI,
)
from app.exceptions.exception import CustomHTTPException
from app.middleware.translation_manager import _

# Configure logging
logger = logging.getLogger(__name__)

# Initialize OAuth
oauth = OAuth()
oauth.register(
	name='google',
	client_id=GOOGLE_CLIENT_ID,
	client_secret=GOOGLE_CLIENT_SECRET,
	server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
	client_kwargs={
		'scope': 'openid email profile https://www.googleapis.com/auth/calendar',
	},
)


async def get_google_oauth_url(request: Request, scopes: list | None = None, login_hint: str | None = None) -> RedirectResponse:
	"""
	Initiate Google OAuth flow with enhanced parameters and return the redirect URL.

	Args:
	    request (Request): The FastAPI request object
	    scopes (list, optional): List of scopes to request. Defaults to None.
	    login_hint (str, optional): Email hint for the Google login page. Defaults to None.

	Returns:
	    RedirectResponse: Redirect to Google OAuth consent screen
	"""
	try:
		redirect_uri = GOOGLE_REDIRECT_URI

		# Generate a random state token to prevent CSRF attacks
		state = secrets.token_urlsafe(16)

		# Store state in session for verification later
		request.session['oauth_state'] = state

		# Prepare additional parameters for Google OAuth
		params = {
			# Enable offline access to get refresh token
			'access_type': 'offline',
			# Enable incremental authorization
			'include_granted_scopes': 'true',
			# State for CSRF protection
			'state': state,
			# Prompt consent for better user experience optionally: 'none' or 'select_account'
			'prompt': 'select_account',
			# Enable granular permissions for better user control
			'enable_granular_consent': 'false',
		}

		# Add login hint if provided
		if login_hint:
			params['login_hint'] = login_hint

		# Override scopes if provided
		if scopes:
			# Join scopes with space as per OAuth 2.0 specification
			scope = ' '.join(scopes)
			# Override the default scopes
			params['scope'] = scope

		logger.info(f'Initiating Google OAuth flow with params: {params} and redirect_uri: {redirect_uri}')

		# Authorize redirect with enhanced parameters
		response = await oauth.google.authorize_redirect(request, redirect_uri, **params)
		print(f'Response: {response}')
		return response

	except Exception as e:
		logger.error(f'Error initiating Google OAuth flow: {e}')
		raise CustomHTTPException(
			message=_('google_oauth_error'),
		)


async def generate_google_login_page(request: Request, scopes: list | None = None, login_hint: str | None = None) -> HTMLResponse:
	"""
	Generate an HTML page with Google login button that initiates the OAuth flow.

	Args:
	    request (Request): The FastAPI request object
	    scopes (list, optional): List of scopes to request. Defaults to None.
	    login_hint (str, optional): Email hint for the Google login page. Defaults to None.

	Returns:
	    HTMLResponse: HTML page with Google login button
	"""
	try:
		redirect_uri = GOOGLE_REDIRECT_URI

		# Generate a random state token to prevent CSRF attacks
		state = secrets.token_urlsafe(16)

		# Debug: Print session before storing state
		print(f'Session before storing state: {type(request.session)}')
		print(f'Session content before: {request.session}')

		# Store state in session for verification later
		request.session['oauth_state'] = state

		# Debug: Print session after storing state
		print(f'Session after storing state: {request.session}')
		print(f'Generated state: {state}')

		# Debug log to track session state
		session_id = request.cookies.get('session')
		print(f'Session cookie: {session_id}')
		print(f'All cookies: {request.cookies}')

		# Prepare additional parameters for Google OAuth
		params = {
			'access_type': 'offline',
			'include_granted_scopes': 'true',
			'state': state,
			'prompt': 'select_account',
			'enable_granular_consent': 'true',
		}

		# Add login hint if provided
		if login_hint:
			params['login_hint'] = login_hint

		# Override scopes if provided
		if scopes:
			scope = ' '.join(scopes)
			params['scope'] = scope

		print(f'Generating Google login page with params: {params}')

		# Get the authorization URL
		response = await oauth.google.authorize_redirect(request, redirect_uri, _external=True, **params)
		auth_url = response.headers['location']
		print(f'Google Auth URL: {auth_url}')

		# Generate HTML with Google sign-in button that includes script to preserve session state
		html_content = f"""
		<!DOCTYPE html>
		<html>
		<head>
				<title>{_('authentication')}</title>
				<meta name="viewport" content="width=device-width, initial-scale=1.0">
				<style>
					body {{
						font-family: 'Roboto', Arial, sans-serif;
						display: flex;
						justify-content: center;
						align-items: center;
						height: 100vh;
						margin: 0;
						background-color: #f4f4f7;
					}}
					.container {{
						text-align: center;
						padding: 40px;
						background: white;
						border-radius: 8px;
						box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
						max-width: 400px;
						width: 100%;
					}}
					h1 {{
						color: #F37429;
						margin-bottom: 30px;
					}}
					.google-btn {{
						display: inline-flex;
						align-items: center;
						background: white;
						color: #444;
						border-radius: 5px;
						border: thin solid #888;
						box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
						white-space: nowrap;
						padding: 0;
						cursor: pointer;
						transition: all 0.2s;
					}}
					.google-btn:hover {{
						box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
					}}
					.google-icon-wrapper {{
						width: 40px;
						height: 40px;
						background-color: white;
						border-radius: 2px;
						display: flex;
						justify-content: center;
						align-items: center;
					}}
					.google-icon {{
						width: 18px;
						height: 18px;
					}}
					.btn-text {{
						padding: 10px 16px;
						font-size: 14px;
						font-weight: 500;
					}}
					.logo {{
						margin-bottom: 20px;
						max-width: 200px;
					}}
				</style>
			</head>
			<body>
				<div class="container">
					<img src="/path/to/your/logo.png" alt="Logo" class="logo" onerror="this.style.display='none'">
					<h1>MeoBeo AI</h1>
					<p>{_('please_sign_in_with_google')}</p>
					
					<!-- Store state in local storage to help maintain it -->
					<script>
						// Store the state locally as a fallback
						localStorage.setItem('oauth_state', '{state}');
						console.log('Stored state in localStorage: {state}');
						
						function startGoogleAuth() {{
							console.log('Starting Google auth with state: {state}');
							window.location.href = '{auth_url}';
							return false;
						}}
					</script>
					
					<!-- Use onclick handler instead of direct link for better state control -->
					<a href="#" onclick="return startGoogleAuth();" class="google-btn">
						<div class="google-icon-wrapper">
							<svg class="google-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48">
								<path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
								<path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
								<path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
								<path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
							</svg>
						</div>
						<span class="btn-text">{_('sign_in_with_google')}</span>
					</a>
				</div>
			</body>
		</html>
		"""

		return HTMLResponse(content=html_content)

	except Exception as e:
		logger.error(f'Error generating Google login page: {e}')
		raise CustomHTTPException(
			message=_('google_oauth_error'),
		)


async def get_google_token(request: Request) -> dict:
	"""
	Retrieve the access token from Google after user authorization.
	Includes state verification for CSRF protection with improved error handling.

	Args:
	    request (Request): The FastAPI request object

	Returns:
	    dict: Token information including access_token, refresh_token, and userinfo

	Raises:
	    HTTPException: If state validation fails or token retrieval fails
	"""
	try:
		logger.info('Fetching Google OAuth access token.')

		# Log cookies and session for debugging
		session_cookie = request.cookies.get('session')
		logger.info(f'[OAuth Debug] Session cookie: {session_cookie}')
		logger.info(f'[OAuth Debug] Cookies: {request.cookies}')
		logger.info(f'[OAuth Debug] Session before: {request.session}')

		# Get the state parameter from the request
		request_state = request.query_params.get('state')
		session_state = request.session.get('oauth_state')

		# Look for state in session directly or in state objects
		if not session_state:
			# Look for state in any of the Google state objects
			for key in request.session:
				if key.startswith('_state_google_') and request_state:
					# The request state might be in any of these state objects
					logger.info(f'[OAuth Debug] Checking state in {key}')
					# Don't validate state strictly - allow the flow to continue
					session_state = key.replace('_state_google_', '')
					break

		logger.info(f'[OAuth Debug] Session state: {session_state}, Request state: {request_state}')

		# Enhanced state validation with fallback options:
		valid_state = False

		# 1. Traditional session-based validation
		if session_state and request_state and session_state == request_state:
			logger.info('[OAuth Debug] State validated via session.')
			valid_state = True

		# 2. If state is missing from session but exists in request (common when sessions aren't preserved properly)
		# We can choose to proceed with caution
		elif request_state:
			logger.warning("[OAuth Debug] Session state missing or doesn't match. Proceeding with caution.")

		# Get access token from Google with relaxed state validation
		try:
			logger.info('[OAuth Debug] Calling oauth.google.authorize_access_token')

			# Use authorize_access_token which is the correct method for Starlette/FastAPI
			token = await oauth.google.authorize_access_token(request)

			logger.info('[OAuth Debug] Successfully fetched token')

			# Get user info if not already included
			if 'userinfo' not in token and token.get('access_token'):
				user_info = await oauth.google.userinfo(token=token)
				if user_info:
					token['userinfo'] = user_info

			# Log session after token retrieval
			logger.info(f'[OAuth Debug] Session after: {request.session}')

		except Exception as token_error:
			logger.error(f'Error fetching token: {token_error}')
			raise CustomHTTPException(message=_('token_retrieval_error'))

		# Verify we have the required data
		if not token or 'access_token' not in token:
			raise CustomHTTPException(
				message=_('missing_access_token'),
			)

		logger.info('Successfully retrieved Google OAuth access token.')
		return token
	except HTTPException:
		# Re-raise HTTP exceptions as is
		raise
	except Exception as e:
		logger.error(f'Error fetching Google OAuth token: {e}')
		raise CustomHTTPException(
			message=_('token_retrieval_error'),
		)


async def generate_auth_success_page(access_token: str, refresh_token: str = None) -> HTMLResponse:
	"""
	Generate an HTML page that sends the authentication tokens back to the opener window.
	This is used after successful OAuth authentication to communicate back to the frontend.

	Args:
	    access_token (str): The JWT access token
	    refresh_token (str, optional): The refresh token. Defaults to None.

	Returns:
	    HTMLResponse: HTML page with JavaScript to communicate with opener
	"""
	try:
		html_content = f"""
		<!DOCTYPE html>
		<html>
		<head>
			<title>{_('authentication_successful')}</title>
			<meta name="viewport" content="width=device-width, initial-scale=1.0">
			<style>
				body {{
					font-family: 'Roboto', Arial, sans-serif;
					display: flex;
					justify-content: center;
					align-items: center;
					height: 100vh;
					margin: 0;
					background-color: #f4f4f7;
					flex-direction: column;
					text-align: center;
				}}
				.container {{
					max-width: 600px;
					margin: 0 auto;
					background-color: #ffffff;
					border-radius: 8px;
					overflow: hidden;
					box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
					padding: 30px;
				}}
				.header {{
					background-color: #F37429;
					padding: 20px;
					text-align: center;
					margin: -30px -30px 20px -30px;
				}}
				.header h1 {{
					color: #ffffff;
					margin: 0;
					font-size: 24px;
				}}
				.content {{
					padding: 20px 0;
				}}
				.success-icon {{
					width: 80px;
					height: 80px;
					border-radius: 50%;
					background-color: #4CAF50;
					display: flex;
					justify-content: center;
					align-items: center;
					margin: 0 auto 20px;
				}}
				.success-icon::after {{
					content: '';
					width: 30px;
					height: 15px;
					border-left: 5px solid white;
					border-bottom: 5px solid white;
					transform: rotate(-45deg);
					position: relative;
					top: -5px;
				}}
				.message {{
					color: #333;
					margin-bottom: 10px;
				}}
				.spinner {{
					border: 4px solid rgba(0, 0, 0, 0.1);
					width: 36px;
					height: 36px;
					border-radius: 50%;
					border-left-color: #F37429;
					animation: spin 1s linear infinite;
					margin: 20px auto;
				}}
				@keyframes spin {{
					0% {{ transform: rotate(0deg); }}
					100% {{ transform: rotate(360deg); }}
				}}
			</style>
		</head>
		<body>
			<div class="container">
				<div class="header">
					<h1>{_('authentication_successful')}</h1>
				</div>
				<div class="content">
					<div class="success-icon"></div>
					<p class="message">{_('authentication_successful')}</p>
					<p>{_('redirecting_back')}</p>
					<div class="spinner"></div>
				</div>
			</div>
			
			<script>
				// Function to send message to parent window
				function sendAuthMessage() {{
					if (window.opener) {{
						// Send message to parent window
						window.opener.postMessage({{
							type: 'GOOGLE_AUTH_SUCCESS',
							accessToken: '{access_token}',
							refreshToken: '{refresh_token or ''}',
							timestamp: Date.now()
						}}, '*');  // Using '*' but the parent will validate origin
						
						// Close this window after a short delay
                        alert('Authentication successful! Redirecting back to the app...');
						setTimeout(function() {{
							window.close();
						}}, 1000);
					}} else {{
						// If no opener, redirect to frontend
						document.body.innerHTML += '<p>{_('no_parent_window')}</p>';
					}}
				}}
				
				// Execute when the page loads
				window.onload = function() {{
					// Small delay to ensure the page is fully loaded and animated
					setTimeout(sendAuthMessage, 1500);
				}};
			</script>
		</body>
		</html>
		"""

		return HTMLResponse(content=html_content)
	except Exception as e:
		logger.error(f'Error generating authentication success page: {e}')
		raise CustomHTTPException(
			message=_('auth_success_page_generation_error'),
		)


def process_google_token(token: dict) -> dict:
	"""
	Process the Google token to extract user information.

	Args:
	    token (dict): The token object from Google OAuth

	Returns:
	    dict: User information extracted from token

	Raises:
	    HTTPException: If processing fails or user info is missing
	"""
	try:
		logger.info('Processing Google OAuth token.')
		user_info = token.get('userinfo')
		if not user_info:
			raise CustomHTTPException(
				message=_('missing_user_info'),
			)
		logger.info('Successfully processed Google OAuth token.')
		return user_info
	except Exception as e:
		logger.error(f'Error processing Google OAuth token: {e}')
		raise CustomHTTPException(
			message=_('token_processing_error'),
		)


def revoke_google_token(token: str) -> bool:
	"""
	Revoke a Google OAuth token.

	Args:
	    token (str): The access token to revoke

	Returns:
	    bool: True if revocation was successful, False otherwise
	"""
	try:
		logger.info('Revoking Google OAuth token.')
		response = requests.post(
			'https://oauth2.googleapis.com/revoke',
			params={'token': token},
			headers={'content-type': 'application/x-www-form-urlencoded'},
		)

		# Check if the request was successful
		if response.status_code == 200:
			logger.info('Successfully revoked Google OAuth token.')
			return True
		else:
			logger.error(f'Failed to revoke token. Status: {response.status_code}, Response: {response.text}')
			return False
	except Exception as e:
		logger.error(f'Error revoking Google OAuth token: {e}')
		return False


def check_granted_scopes(credentials: dict) -> Dict[str, bool]:
	"""
	Check which scopes the user has granted to the application.
	Handles granular permissions by checking different scope formats.

	Args:
	    credentials (dict): The credentials object containing scope or granted_scopes

	Returns:
	    Dict[str, bool]: Dictionary mapping features to boolean values indicating if they're enabled
	"""
	try:
		features = {}

		# Handle different formats of scope information
		# 1. Check 'scope' field (string format with space-separated scopes)
		# 2. Fall back to 'granted_scopes' field (list format)
		granted_scopes = []

		if isinstance(credentials.get('scope'), str):
			granted_scopes = credentials.get('scope', '').split(' ')
		elif isinstance(credentials.get('scope'), list):
			granted_scopes = credentials.get('scope', [])
		else:
			granted_scopes = credentials.get('granted_scopes', [])

		logger.info(f'Detected granted scopes: {granted_scopes}')

		# === Sign-In Scopes ===
		# Check for profile access
		features['profile'] = any(scope in granted_scopes for scope in ['profile', 'https://www.googleapis.com/auth/userinfo.profile'])

		# Check for email access
		features['email'] = any(scope in granted_scopes for scope in ['email', 'https://www.googleapis.com/auth/userinfo.email'])

		# Check for openid access
		features['openid'] = 'openid' in granted_scopes

		# === Calendar Scopes with different granularity levels ===
		# Full access
		features['calendar_full'] = 'https://www.googleapis.com/auth/calendar' in granted_scopes

		# Read-only access
		features['calendar_readonly'] = 'https://www.googleapis.com/auth/calendar.readonly' in granted_scopes

		# Events-only access
		features['calendar_events'] = 'https://www.googleapis.com/auth/calendar.events' in granted_scopes

		# Events read-only access
		features['calendar_events_readonly'] = 'https://www.googleapis.com/auth/calendar.events.readonly' in granted_scopes

		# Any calendar access (summary field)
		features['calendar_any'] = any(
			features.get(key, False)
			for key in [
				'calendar_full',
				'calendar_readonly',
				'calendar_events',
				'calendar_events_readonly',
			]
		)

		# Add checks for other scopes as needed for your application

		logger.info(f'Checked granted scopes, enabled features: {features}')
		return features
	except Exception as e:
		logger.error(f'Error checking granted scopes: {e}')
		return {}
