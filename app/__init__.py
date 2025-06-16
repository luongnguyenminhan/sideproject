"""Main init"""

import os
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import SECRET_KEY, print_all_config
from app.exceptions.handlers import setup_exception_handlers
from app.middleware.localization_middleware import LocalizationMiddleware
from app.middleware.translation_manager import _
from app.modules import route as api_routers
from app.modules.agent.events import register_agent_event_handlers


def custom_openapi(app: FastAPI):
	"""Create custom openapi schema"""
	api_version = os.getenv('API_VERSION', '1.0.0')
	openapi_schema = get_openapi(
		title=f'{_("api_title")}',
		version=api_version,
		description=_('api_description'),
		routes=app.routes,
	)
	# Add Bearer token authentication to Swagger UI
	openapi_schema['components']['securitySchemes'] = {'Bearer': {'type': 'http', 'scheme': 'bearer', 'bearerFormat': 'JWT'}}
	openapi_schema['security'] = [{'Bearer': []}]

	# Store the modified schema
	app.openapi_schema = openapi_schema
	return openapi_schema


def create_app():
	"""Create main app"""
	print_all_config()  # Print config at startup
	app = FastAPI()

	# Register middlewares in correct order (from outermost to innermost)
	app.add_middleware(
		CORSMiddleware,
		allow_origins=['*'],
		allow_credentials=True,
		allow_methods=['*'],
		allow_headers=['*'],
	)

	# SessionMiddleware must be added before any middleware that uses the session
	app.add_middleware(
		SessionMiddleware,
		secret_key=SECRET_KEY,
		session_cookie='cgsem_session',  # Consistent cookie name
		same_site='lax',  # Allow cross-site requests while maintaining security
	)

	app.add_middleware(LocalizationMiddleware)

	# Add OAuth debug middleware in development
	@app.middleware('http')
	async def debug_oauth_middleware(request, call_next):
		# Debug sessions for OAuth state issues
		if 'google' in request.url.path:
			print(f'[OAuth Debug] Path: {request.url.path}')
			try:
				print(f'[OAuth Debug] Session before: {request.session}')
			except:
				print('[OAuth Debug] No session available')
			print(f'[OAuth Debug] Cookies: {request.cookies}')
		response = await call_next(request)
		if 'google' in request.url.path:
			try:
				print(f'[OAuth Debug] Session after: {request.session}')
			except:
				print('[OAuth Debug] No session available after')
		return response

	app.include_router(api_routers, prefix='/api')
	custom_openapi(app)
	setup_exception_handlers(app)

	# Register event handlers
	try:
		register_agent_event_handlers()
		logger = logging.getLogger(__name__)
		logger.info('Event handlers registered successfully')
	except Exception as e:
		logger = logging.getLogger(__name__)
		logger.error(f'Failed to register event handlers: {e}')

	return app
