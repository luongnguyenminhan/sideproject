"""Handlers exeption validation"""

import json

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.base_model import APIResponse
from app.enums.base_enums import BaseErrorCode
from app.exceptions.exception import (
	CustomHTTPException,
	ForbiddenException,
	NotFoundException,
	UnauthorizedException,
	ValidationException,
)


async def custom_forbidden_exception_handler(request: Request, exc: ForbiddenException):
	"""custom_http_exception_handler"""
	print(f'OMG! An HTTP error!: {repr(exc)}')
	response_data = APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_FAIL,
		message=exc.message,
		description=None,
		data=None,
	)
	return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content=response_data.model_dump())


async def custom_unauthorized_exception_handler(request: Request, exc: UnauthorizedException):
	"""custom_http_exception_handler"""
	print(f'OMG! An HTTP error!: {repr(exc)}')
	response_data = APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_FAIL,
		message=exc.message,
		description=None,
		data=None,
	)
	return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content=response_data.model_dump())


async def custom_not_found_exception_handler(request: Request, exc: NotFoundException):
	"""custom_http_exception_handler"""
	print(f'OMG! An HTTP error!: {repr(exc)}')
	response_data = APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_FAIL,
		message=exc.message,
		description=None,
		data=None,
	)
	return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=response_data.model_dump())


async def custom_validation_exception_handler(request: Request, exc: ValidationException):
	"""custom_http_exception_handler"""
	print(f'OMG! An HTTP error!: {repr(exc)}')
	response_data = APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_FAIL,
		message=exc.message,
		description=None,
		data=None,
	)
	return JSONResponse(
		status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
		content=response_data.model_dump(),
	)


async def custom_exception_handler(request: Request, exc: Exception):
	"""custom_http_exception_handler"""
	print(f'OMG! An HTTP error!: {repr(exc)}')
	response_data = APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_FAIL,
		message=str(exc),  # Changed to str(exc) for better error message handling
		description=None,
		data=None,
	)
	return JSONResponse(
		status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
		content=response_data.model_dump(),
	)


async def custom_http_exception_handler(request: Request, exc: CustomHTTPException):
	"""custom_http_exception_handler"""
	print(f'OMG! An HTTP error!: {repr(exc)}')
	response_data = APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_FAIL,
		message=str(exc),  # Changed to str(exc) for better error message handling
		description=None,
		data=None,
	)
	return JSONResponse(
		status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
		content=response_data.model_dump(),
	)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
	"""Xử lý lỗi validation"""
	print(f'OMG! The client sent invalid data!: {exc}')
	response_data = APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_FAIL,
		message=str(exc),  # Changed to str(exc) for better error message handling
		description=json.dumps(exc.errors()),
		data=None,
	)
	return JSONResponse(
		status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
		content=response_data.model_dump(),
	)


def handle_exceptions(func):
	"""Decorator to handle common exceptions in API routes"""
	from functools import wraps

	@wraps(func)
	async def wrapper(*args, **kwargs):
		try:
			return await func(*args, **kwargs)
		except CustomHTTPException as ex:
			print(f'OMG! An HTTP asdasderror!: {repr(ex)}')
			response_data = APIResponse(
				error_code=BaseErrorCode.ERROR_CODE_FAIL,
				message=str(ex).split(': ')[-1],  # Changed to str(ex) for better error message handling
				description=None,
				data=None,
			)
			return JSONResponse(
				status_code=status.HTTP_200_OK,
				content=response_data.model_dump(),
			)
		except Exception as ex:
			print(f'OMG! An HTTP error!: {repr(ex)}')
			return JSONResponse(
				status_code=200,
				content={
					'error_code': BaseErrorCode.ERROR_CODE_FAIL,
					'message': str(ex),  # Changed to str(ex) for better error message handling
					'description': None,
					'data': None,
				},
			)

	return wrapper


def setup_exception_handlers(app: FastAPI):
	"""Đăng ký các exception handlers vào ứng dụng FastAPI"""
	app.add_exception_handler(RequestValidationError, validation_exception_handler)
	app.add_exception_handler(CustomHTTPException, custom_http_exception_handler)
	app.add_exception_handler(ForbiddenException, custom_forbidden_exception_handler)
	app.add_exception_handler(UnauthorizedException, custom_unauthorized_exception_handler)
	app.add_exception_handler(NotFoundException, custom_not_found_exception_handler)
	app.add_exception_handler(ValidationException, custom_validation_exception_handler)

	# app.add_exception_handler(Exception, custom_exception_handler)
