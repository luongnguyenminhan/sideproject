from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.middleware.translation_manager import set_language


class LocalizationMiddleware(BaseHTTPMiddleware):
	async def dispatch(self, request: Request, call_next):
		await set_language(request)
		response = await call_next(request)
		return response
