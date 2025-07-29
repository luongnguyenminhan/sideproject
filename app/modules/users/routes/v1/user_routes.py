import json

from fastapi import APIRouter, Depends, Query

from app.core.base_model import APIResponse, PagingInfo
from app.enums.base_enums import BaseErrorCode
from app.exceptions.exception import CustomHTTPException
from app.exceptions.handlers import handle_exceptions
from app.http.oauth2 import get_current_user
from app.middleware.auth_middleware import verify_token
from app.middleware.translation_manager import _
from app.modules.users.repository.user_repo import UserRepo
from app.modules.users.schemas.users import (
	CountUsersResponse,
	PaginatedResponse,
	SearchUserRequest,
	SearchUserResponse,
	UserResponse,
)

route = APIRouter(prefix='/users', tags=['Users'], dependencies=[Depends(verify_token)])


@route.get('/', response_model=APIResponse)
@handle_exceptions
async def search_users(
	page: int = Query(1, ge=1),
	page_size: int = Query(10, ge=1),
	filters_json: str | None = Query(None, description='JSON string of filters'),
	current_user_payload: dict = Depends(get_current_user),
	repo: UserRepo = Depends(),
):
	"""
	Get all users with pagination and dynamic filtering

	Supports two ways of filtering:
	1. Using a JSON string of filters with field, operator, and value
	2. Using direct query parameters for simpler filters (backwards compatibility)

	Example with structured filters:
	GET /users/?page=1&page_size=10&filters_json=[{"field":"username","operator":"contains","value":"john"}]
	Available operators:
	- eq: Equal
	- ne: Not equal
	- lt: Less than
	- lte: Less than or equal
	- gt: Greater than
	- gte: Greater than or equal
	- contains: String contains
	- startswith: String starts with
	- endswith: String ends with
	- in_list: Value is in a list
	- not_in: Value is not in a list
	- is_null: Field is null
	- is_not_null: Field is not null
	"""
	filters = []
	if filters_json:
		try:
			filters = json.loads(filters_json)
			if not isinstance(filters, list):
				filters = []
		except json.JSONDecodeError:
			filters = []
		except Exception:
			filters = []

	request = SearchUserRequest(page=page, page_size=page_size, filters=filters)
	result = repo.search_users(request)
	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('operation_successful'),
		data=PaginatedResponse[UserResponse](
			items=[UserResponse.model_validate(user) for user in result.items],
			paging=PagingInfo(
				total=result.total_count,
				total_pages=result.total_pages,
				page=result.page,
				page_size=result.page_size,
			),
		),
	)


@route.get('/me', response_model=APIResponse)
@handle_exceptions
async def get_current_user_profile(current_user_payload: dict = Depends(get_current_user), repo: UserRepo = Depends()):
	"""
	Get the profile of the currently authenticated user

	This endpoint returns the full profile information of the authenticated user
	based on their access token.
	"""
	user_id = current_user_payload.get('user_id')
	user = repo.get_user_by_id(user_id)

	if not user:
		raise CustomHTTPException(message=_('user_not_found'))

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('operation_successful'),
		data=UserResponse.model_validate(user),
	)


@route.put('/me', response_model=APIResponse)
@handle_exceptions
async def update_current_user_profile(
	user_data: dict,
	current_user_payload: dict = Depends(get_current_user),
	repo: UserRepo = Depends(),
):
	"""
	Update the profile of the currently authenticated user

	This endpoint allows the authenticated user to update their profile information.
	"""
	user_id = current_user_payload.get('user_id')
	updated_user_data = user_data
	updated_user = repo.update_user(user_id, updated_user_data)
	if not updated_user:
		raise CustomHTTPException(message=_('user_not_found'))

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('operation_successful'),
		data=UserResponse.model_validate(updated_user),
	)


@route.get('/count', response_model=APIResponse)
@handle_exceptions
async def count_users(
	filters_json: str | None = Query(None, description='JSON string of filters'),
	current_user_payload: dict = Depends(get_current_user),
	repo: UserRepo = Depends(),
):
	"""
	Count total number of users with optional filtering

	Supports filtering using a JSON string of filters with field, operator, and value.
	
	Example with structured filters:
	GET /users/count?filters_json=[{"field":"role","operator":"eq","value":"user"}]
	
	Available operators:
	- eq: Equal
	- ne: Not equal  
	- lt: Less than
	- lte: Less than or equal
	- gt: Greater than
	- gte: Greater than or equal
	- contains: String contains
	- startswith: String starts with
	- endswith: String ends with
	- in_list: Value is in a list
	- not_in: Value is not in a list
	- is_null: Field is null
	- is_not_null: Field is not null
	"""
	filters = []
	if filters_json:
		try:
			filters = json.loads(filters_json)
			if not isinstance(filters, list):
				filters = []
		except json.JSONDecodeError:
			filters = []
		except Exception:
			filters = []

	filter_params = {'filters': filters} if filters else {}
	total_count = repo.count_users(filter_params)
	
	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('operation_successful'),
		data=CountUsersResponse(total_count=total_count),
	)
