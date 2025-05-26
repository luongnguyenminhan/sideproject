"""Tag API Routes"""

import json

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.base_model import APIResponse, PaginatedResponse, PagingInfo
from app.core.database import get_db
from app.enums.base_enums import BaseErrorCode
from app.exceptions.handlers import handle_exceptions
from app.http.oauth2 import get_current_user
from app.middleware.auth_middleware import verify_token
from app.middleware.translation_manager import _
from app.modules.meeting_tags.repository.tag_repo import TagRepo
from app.modules.meeting_tags.schemas.tag_schemas import (
	SearchTagRequest,
	SearchTagResponse,
	TagCreate,
	TagResponse,
	TagUpdate,
)

route = APIRouter(prefix='/tags', tags=['Tags'], dependencies=[Depends(verify_token)])


@route.get('/', response_model=SearchTagResponse)
@handle_exceptions
async def search_tags_get(
	page: int = Query(1, ge=1),
	page_size: int = Query(10, ge=1),
	filters_json: str | None = Query(None, description='JSON string of filters'),
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Search tags with dynamic filtering and pagination

	Supports dynamic filtering through the filters_json parameter:

	Example with structured filters:
	GET /tags/search?page=1&page_size=10&filters_json=[{"field":"name","operator":"contains","value":"important"}]

	To filter by system tags:
	GET /tags/search?filters_json=[{"field":"is_system","operator":"eq","value":true}]

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

	Args:
	    page: Page number
	    page_size: Items per page
	    filters_json: JSON string of filters for dynamic filtering

	Returns:
	    List of tags with pagination info
	"""

	# Parse filters from JSON
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

	# Create request
	request = SearchTagRequest(page=page, page_size=page_size, filters=filters)

	# Search tags
	tag_repo = TagRepo(db)
	result = tag_repo.search_tags(current_user_payload['user_id'], request.model_dump())

	# Prepare response
	tags = [TagResponse.model_validate(tag.to_dict()) for tag in result.items]

	return SearchTagResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('search_successful'),
		data=PaginatedResponse(
			items=tags,
			paging=PagingInfo(
				total=result.total_count,
				total_pages=result.total_pages,
				page=page,
				page_size=page_size,
			),
		),
	)


@route.get('/{tag_id}', response_model=APIResponse)
@handle_exceptions
async def get_tag(
	tag_id: str,
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Get a specific tag by ID

	Args:
	    tag_id: Tag ID

	Returns:
	    Tag details
	"""
	tag_repo = TagRepo(db)
	tag = tag_repo.get_tag_by_id(tag_id, current_user_payload['user_id'])

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('get_tag_success'),
		data=tag,
	)


@route.post('/', response_model=APIResponse)
@handle_exceptions
async def create_tag(
	tag_data: TagCreate,
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Create a new tag

	Args:
	    tag_data: Tag data

	Returns:
	    Created tag details
	"""
	tag_repo = TagRepo(db)
	tag = tag_repo.create_tag(current_user_payload['user_id'], tag_data.model_dump())

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('create_tag_success'),
		data=tag,
	)


@route.put('/{tag_id}', response_model=APIResponse)
@handle_exceptions
async def update_tag(
	tag_id: str,
	tag_data: TagUpdate,
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Update an existing tag

	Args:
	    tag_id: Tag ID
	    tag_data: Updated tag data

	Returns:
	    Updated tag details
	"""
	tag_repo = TagRepo(db)
	tag = tag_repo.update_tag(tag_id, current_user_payload['user_id'], tag_data.model_dump())

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('update_tag_success'),
		data=tag,
	)


@route.delete('/{tag_id}', response_model=APIResponse)
@handle_exceptions
async def delete_tag(
	tag_id: str,
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Delete a tag

	Args:
	    tag_id: Tag ID

	Returns:
	    Success message
	"""
	tag_repo = TagRepo(db)
	result = tag_repo.delete_tag(tag_id, current_user_payload['user_id'])

	if result:
		return APIResponse(
			error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
			message=_('tag_deleted_successfully'),
			data={'success': True},
		)
	else:
		return APIResponse(
			error_code=BaseErrorCode.ERROR_CODE_FAIL,
			message=_('delete_tag_failed'),
			data={'success': False},
		)


@route.get('/{tag_id}/meetings', response_model=APIResponse)
@handle_exceptions
async def get_tag_meetings(
	tag_id: str,
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Get all meetings associated with a tag

	Args:
	    tag_id: Tag ID

	Returns:
	    List of meeting IDs
	"""
	tag_repo = TagRepo(db)
	meeting_ids = tag_repo.get_tag_meetings(tag_id, current_user_payload['user_id'])

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('get_tag_meetings_success'),
		data=meeting_ids,
	)


@route.post('/search', response_model=SearchTagResponse)
@handle_exceptions
async def search_tags(
	search_request: SearchTagRequest,
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Search user's tags with filtering and pagination

	Args:
	    search_request: Search parameters and filters

	Returns:
	    List of matching tags with pagination info
	"""
	tag_repo = TagRepo(db)
	search_params = search_request.model_dump(exclude_unset=True)

	result = tag_repo.search_tags(current_user_payload['user_id'], search_params)

	tags = [TagResponse.model_validate(tag.to_dict()) for tag in result.items]

	return SearchTagResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('search_successful'),
		data=PaginatedResponse(
			items=tags,
			paging=PagingInfo(
				total=result.total_count,
				total_pages=result.total_pages,
				page=result.page,
				page_size=result.page_size,
			),
		),
	)
