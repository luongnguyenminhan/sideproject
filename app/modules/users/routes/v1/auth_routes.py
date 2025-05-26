"""
Authentication API Routes for Google OAuth

This module handles Google OAuth authentication endpoints
"""

import requests
from authlib.integrations.starlette_client import OAuthError
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.core.base_model import APIResponse
from app.core.config import FRONTEND_ERROR_URL, FRONTEND_SUCCESS_URL
from app.enums.base_enums import BaseErrorCode
from app.exceptions.exception import CustomHTTPException
from app.exceptions.handlers import handle_exceptions
from app.http.oauth2 import get_current_user
from app.middleware.translation_manager import _
from app.modules.users.repository.authen_repo import AuthenRepo
from app.modules.users.schemas.users import (
    GoogleDirectLoginRequest,
    GoogleLoginResponse,
    GoogleRevokeTokenRequest,
    OAuthUserInfo,
    UserResponse,
)
from app.utils.oauth_utils import (
    check_granted_scopes,
    generate_auth_success_page,
    generate_google_login_page,
    get_google_oauth_url,
    get_google_token,
    revoke_google_token,
)
import logging

route = APIRouter(prefix='/auth', tags=['Authentication'])
logger = logging.getLogger(__name__)


@route.get('/google/login', response_class=HTMLResponse)
@handle_exceptions
async def google_login(request: Request, login_hint: str | None = None):
    """Render a page with Google login button

    This endpoint returns an HTML page with a Google login button that will
    initiate the OAuth flow when clicked.

    Args:
            request (Request): The FastAPI request object
            login_hint (str, optional): Email hint for the Google login page

    Returns:
            HTMLResponse: HTML page with the Google login button
    """
    # Define scopes we want to request
    scopes = ['openid', 'email', 'profile', 'https://www.googleapis.com/auth/calendar']

    # Generate and return the HTML page with Google login button
    return await generate_google_login_page(request, scopes=scopes, login_hint=login_hint)


@route.get('/google/auth', response_class=RedirectResponse)
@handle_exceptions
async def google_auth_redirect(request: Request, login_hint: str | None = None):
    """Direct redirect to Google OAuth login (alternative to button page)

    This endpoint directly redirects to Google OAuth consent screen.
    Useful for API integrations or when HTML rendering is not needed.

    Args:
            request (Request): The FastAPI request object
            login_hint (str, optional): Email hint for the Google login page

    Returns:
            RedirectResponse: Redirect to Google OAuth consent screen
    """
    # Define scopes we want to request
    scopes = ['openid', 'email', 'profile', 'https://www.googleapis.com/auth/calendar']

    # Return the redirect response to Google OAuth
    return await get_google_oauth_url(request, scopes=scopes, login_hint=login_hint)


@route.post('/google/direct-login', response_model=GoogleLoginResponse)
@handle_exceptions
async def google_direct_login(token_data: GoogleDirectLoginRequest, request: Request, repo: AuthenRepo = Depends()):
    """Direct login with Google token (for mobile apps)

    This endpoint allows direct login with a Google token without the OAuth redirect flow

    Args:
        token_data (GoogleDirectLoginRequest): The token data from the mobile client
        request (Request): The FastAPI request object
        repo (AuthenRepo): The authentication repository

    Returns:
        GoogleLoginResponse: User information with tokens
    """
    try:
        # Convert the Pydantic model to dict for processing
        token_dict = token_data.model_dump(exclude_unset=True)

        # Extract token from request to get user info
        access_token = token_data.access_token

        # Create a request to Google's userinfo endpoint
        headers = {'Authorization': f'Bearer {access_token}'}
        user_info_response = requests.get('https://www.googleapis.com/oauth2/v3/userinfo', headers=headers)

        if user_info_response.status_code != 200:
            raise CustomHTTPException(
                message=_('google_user_info_error'),
            )

        user_info = user_info_response.json()

        # Extract granted scopes if available
        granted_scopes = token_data.scope.split(' ') if token_data.scope else []

        # Create OAuth user info object with granted scopes
        oauth_user = OAuthUserInfo(
            email=user_info.get('email'),
            name=user_info.get('name'),
            picture=user_info.get('picture'),
            given_name=user_info.get('given_name'),
            family_name=user_info.get('family_name'),
            locale=user_info.get('locale'),
            sub=user_info.get('sub'),
            granted_scopes=granted_scopes,
        )

        # Login or register with Google credentials
        result = await repo.login_with_google(oauth_user)

        # Check which features are enabled based on granted scopes
        features = check_granted_scopes({'granted_scopes': granted_scopes})

        # Add features to the result
        result['enabled_features'] = features

        response = UserResponse.model_validate(result)

        return GoogleLoginResponse(
            error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
            message=_('login_success'),
            data=response,
        )
    except Exception:
        raise CustomHTTPException(
            message=_('google_login_failed'),
        )


@route.get('/google/callback')
@handle_exceptions
async def google_callback(request: Request, repo: AuthenRepo = Depends()):
    """Handle Google OAuth callback after user authorization

    This endpoint processes the OAuth callback from Google and creates/logs in the user,
    then returns an HTML page that communicates with the opener window
    """
    try:
        # Enhanced logging for debugging the callback
        logger.info('Google callback received')
        logger.info(f'Query params: {request.query_params}')
        logger.info(f'Session data: {request.session}')
        logger.info(f'Cookies: {request.cookies}')

        # Get token from Google - this includes state verification for CSRF protection
        try:
            token = await get_google_token(request)
            user_info = token.get('userinfo')
            logger.info(f'Successfully retrieved token and user info: {user_info.get("email") if user_info else "No email"}')
        except Exception as token_error:
            logger.error(f'Error retrieving token: {token_error}')
            error_message = str(token_error)
            if 'state' in error_message.lower():
                error_message = _('session_expired_or_invalid')

            # Return error HTML that will communicate with parent window
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>{_('authentication_failed')}</title>
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
                </style>
                <script>
                    window.onload = function() {{
                        if (window.opener) {{
                            window.opener.postMessage({{
                                type: 'GOOGLE_AUTH_ERROR',
                                error: '{error_message}',
                                timestamp: Date.now()
                            }}, '*');
                            setTimeout(function() {{ window.close(); }}, 2000);
                        }}
                    }};
                </script>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>{_('authentication_failed')}</h1>
                    </div>
                    <div class="content">
                        <p>{error_message}</p>
                        <p>{_('window_close_automatically')}</p>
                    </div>
                </div>
            </body>
            </html>
            """
            return HTMLResponse(content=html_content)

        if not user_info or not user_info.get('email'):
            error_message = _('missing_email_google')
            logger.error('Error: Missing email from Google user info')

            # Return error HTML that will communicate with parent window
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>{_('authentication_failed')}</title>
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
                </style>
                <script>
                    window.onload = function() {{
                        if (window.opener) {{
                            window.opener.postMessage({{
                                type: 'GOOGLE_AUTH_ERROR',
                                error: '{error_message}',
                                timestamp: Date.now()
                            }}, '*');
                            setTimeout(function() {{ window.close(); }}, 2000);
                        }}
                    }};
                </script>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>{_('authentication_failed')}</h1>
                    </div>
                    <div class="content">
                        <p>{error_message}</p>
                        <p>{_('window_close_automatically')}</p>
                    </div>
                </div>
            </body>
            </html>
            """
            return HTMLResponse(content=html_content)

        # Create OAuth user info
        oauth_user = OAuthUserInfo(
            email=user_info.get('email'),
            name=user_info.get('name'),
            picture=user_info.get('picture'),
            given_name=user_info.get('given_name'),
            family_name=user_info.get('family_name'),
            locale=user_info.get('locale'),
            sub=user_info.get('sub'),
            granted_scopes=token.get('scope', '').split(' ') if isinstance(token.get('scope', ''), str) else token.get('scope', []),
        )

        # Login or register with Google credentials
        result = await repo.login_with_google(oauth_user)

        # Check if this is a new user
        is_new_user = result.get('is_new_user', False)

        # Generate success HTML that will communicate with parent window
        return await generate_auth_success_page(
            user=result,
            is_new_user=is_new_user,
            frontend_success_url=FRONTEND_SUCCESS_URL,
            granted_scopes=oauth_user.granted_scopes,
        )

    except Exception as ex:
        # Log the error
        logger.error(f"Error in Google OAuth callback: {ex}")
        
        # Return error page that will close itself
        return HTMLResponse(
            content=f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>{_('authentication_failed')}</title>
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
                </style>
                <script>
                    window.onload = function() {{
                        if (window.opener) {{
                            window.opener.postMessage({{
                                type: 'GOOGLE_AUTH_ERROR',
                                error: '{str(ex)}',
                                timestamp: Date.now()
                            }}, '*');
                            setTimeout(function() {{ window.close(); }}, 2000);
                        }}
                    }};
                </script>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>{_('authentication_failed')}</h1>
                    </div>
                    <div class="content">
                        <p>{_('google_login_failed')}</p>
                        <p>{_('window_close_automatically')}</p>
                    </div>
                </div>
            </body>
            </html>
            """
        )


@route.post('/google/revoke', response_model=APIResponse)
@handle_exceptions
async def revoke_google_access(
    token_request: GoogleRevokeTokenRequest,
    repo: AuthenRepo = Depends(),
    current_user_payload: dict = Depends(get_current_user),
):
    """Revoke Google OAuth access token

    This endpoint revokes the Google OAuth token to remove application access.

    Args:
        token_request (GoogleRevokeTokenRequest): Token to revoke
        repo (AuthenRepo): Authentication repository
        current_user_payload (dict): Current user info from JWT

    Returns:
        APIResponse: Success response
    """
    # Revoke the token
    revoke_success = await revoke_google_token(token_request.token)

    # Log the token revocation
    if revoke_success:
        await repo.log_oauth_token_revocation(current_user_payload['user_id'])

    return APIResponse(
        error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
        message=_('google_token_revoked'),
        data=None,
    )
