"""API routes for group management"""

from typing import Dict, Any, Optional
import json

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.orm import Session

from app.core.base_model import APIResponse, PaginatedResponse, Pagination, PagingInfo
from app.core.database import get_db
from app.enums.base_enums import BaseErrorCode
from app.exceptions.handlers import handle_exceptions
from app.http.oauth2 import get_current_user
from app.middleware.auth_middleware import verify_token
from app.middleware.translation_manager import _
from app.modules.groups.models.group_member import (
	GroupMember,
	GroupMemberRole,
	GroupMemberJoinStatus,
)
from app.modules.groups.repository.group_repo import GroupRepo
from app.modules.groups.schemas import (
	GroupCreate,
	GroupUpdate,
	GroupResponse,
	GroupMemberResponse,
	GroupInviteRequest,
	GroupMemberActionRequest,
	GroupWithMembersResponse,
	SearchGroupRequest,
	GroupWithMembershipStatusResponse,  # Kept for backward compatibility
	GroupWithMembershipDetailsResponse,  # Added new schema for improved response
)

route = APIRouter(prefix='/groups', tags=['Groups'], dependencies=[Depends(verify_token)])


@route.post('', response_model=APIResponse)
@handle_exceptions
async def create_group(
	group_data: GroupCreate,
	db: Session = Depends(get_db),
	current_user: Dict[str, Any] = Depends(get_current_user),
):
	"""Create a new group"""
	user_id = current_user.get('user_id')
	print(f'Current user: {current_user}')
	print(f'[DEBUG] Creating group for user: {user_id}')
	print(f'[DEBUG] Group data: name={group_data.name}, is_public={group_data.is_public}')

	group_repo = GroupRepo(db)

	created_group = group_repo.create_group(
		name=group_data.name,
		description=group_data.description,
		is_public=group_data.is_public,
		user_id=user_id,
	)
	print(f'[DEBUG] Group created successfully: {created_group.id}')

	response_data = GroupResponse.model_validate(created_group)
	print(f'[DEBUG] Returning response for group: {response_data.id}')

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('group_created_successfully'),
		data=response_data,
	)


@route.get('/search', response_model=APIResponse)
@handle_exceptions
async def search_groups(
	page: int = Query(1, ge=1),
	page_size: int = Query(10, ge=1),
	filters_json: str | None = Query(None, description='JSON string of filters'),
	include_public: bool = Query(False, description='Whether to include public groups in the search'),  # Added include_public
	db: Session = Depends(get_db),
	current_user: Dict[str, Any] = Depends(get_current_user),
):
	"""Search groups with dynamic filtering and pagination

	Supports dynamic filtering through the filters_json parameter:

	Example with structured filters:
	GET /groups/search?page=1&page_size=10&filters_json=[{"field":"name","operator":"contains","value":"Team"}]

	To filter by public status:
	GET /groups/search?filters_json=[{"field":"is_public","operator":"eq","value":true}]

	To include public groups (if applicable to your search logic, can be a filter):
	GET /groups/search?include_public=true

	Response includes detailed membership information for the current user:
	- member_id: The ID of the membership record (useful for actions like respond to invite)
	- join_status: The user's join status (ACCEPTED, PENDING, REJECTED, etc.)
	- member_role: The user's role in the group (LEADER, MEMBER)

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
	    page: Page number for pagination
	    page_size: Number of items per page
	    filters_json: JSON string of filter criteria
	    include_public: Whether to include public groups in results
	    db: Database session
	    current_user: Current authenticated user

	Returns:
	    APIResponse: Response object containing paginated list of groups with membership details
	"""
	user_id = current_user.get('user_id')
	print(f'[DEBUG] Search groups for user_id: {user_id}')
	print(f'[DEBUG] Search parameters - page: {page}, page_size: {page_size}')

	group_repo = GroupRepo(db)

	filters = []
	if filters_json:
		print(f'[DEBUG] Raw filters_json: {filters_json}')
		try:
			filters = json.loads(filters_json)
			if not isinstance(filters, list):
				print(f'[DEBUG] filters_json is not a list, setting to empty list')
				filters = []
			else:
				print(f'[DEBUG] Parsed filters: {filters}')
		except json.JSONDecodeError:
			print(f'[DEBUG] JSON decode error for filters_json')
			filters = []
		except Exception as e:
			print(f'[DEBUG] Exception processing filters_json: {str(e)}')
			filters = []
	else:
		print(f'[DEBUG] No filters provided')

	request = SearchGroupRequest(
		page=page,
		page_size=page_size,
		filters=filters,
	)
	print(f'[DEBUG] Search request: {request.model_dump()}')

	# Add include_public to the search_params if it's not part of SearchGroupRequest model
	search_params = request.model_dump()
	search_params['include_public'] = include_public

	result = group_repo.search_groups(user_id, search_params)  # Pass updated search_params
	print(f'[DEBUG] Search result - total count: {result.total_count}, total pages: {result.total_pages}')

	items = [GroupWithMembershipDetailsResponse.model_validate(group) for group in result.items]
	print(f'[DEBUG] Found {len(items)} groups matching search criteria')

	# Log the first few items with their membership details for debugging
	for item in items[:3]:  # Only log first 3 for brevity
		print(f"[DEBUG] Group {item.id}: '{item.name}', Member ID: {item.member_id}, Role: {item.member_role}, Status: {item.join_status}")

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('groups_retrieved_successfully'),
		data=PaginatedResponse(
			items=items,
			paging=PagingInfo(
				total=result.total_count,
				total_pages=result.total_pages,
				page=page,
				page_size=page_size,
			),
		),
	)


@route.get('/{group_id}', response_model=APIResponse)
@handle_exceptions
async def get_group(
	group_id: str = Path(..., description='Group ID'),
	include_members: bool = Query(False, description='Include group members'),
	db: Session = Depends(get_db),
	current_user: Dict[str, Any] = Depends(get_current_user),
):
	"""Get a specific group by ID"""
	user_id = current_user.get('user_id')
	print(f'[DEBUG] Fetching group ID: {group_id} for user: {user_id}')
	group_repo = GroupRepo(db)

	group = group_repo.get_group_by_id(group_id, user_id)
	print(f'[DEBUG] Retrieved group: {group.id}, name: {group.name}')
	group_data = GroupResponse.model_validate(group)
	print(f'[DEBUG] Validated group data: {group_data}')

	# Create response_data without using ** unpacking
	response_data = GroupWithMembersResponse(
		id=group_data.id,
		name=group_data.name,
		description=group_data.description,
		is_public=group_data.is_public,
		create_date=group_data.create_date,
		created_by=group_data.created_by,
		update_date=group_data.update_date,
		is_active=group_data.is_active,  # Added is_active field
	)

	if include_members:
		print(f'[DEBUG] Including members for group: {group_id}')
		members_pagination: Pagination[GroupMemberResponse] = group_repo.list_members(
			group_id=group_id,
			user_id=user_id,
			search_params={
				'field': 'join_status',
				'operator': 'eq',
				'value': GroupMemberJoinStatus.ACCEPTED,
			},
		)
		print(f'[DEBUG] Found {members_pagination.items} members with ACCEPTED status')

		member_responses = [GroupMemberResponse.model_validate(member) for member in members_pagination.items]
		response_data.members = member_responses
		print(f'[DEBUG] Members added to response: {members_pagination}')

	print(f'[DEBUG] Returning group response for {group_id}')
	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('group_retrieved_successfully'),
		data=response_data,
	)


@route.put('/{group_id}', response_model=APIResponse)
@handle_exceptions
async def update_group(
	group_data: GroupUpdate,
	group_id: str = Path(..., description='Group ID'),
	db: Session = Depends(get_db),
	current_user: Dict[str, Any] = Depends(get_current_user),
):
	"""Update a group"""
	user_id = current_user.get('user_id')
	print(f'[DEBUG] Updating group ID: {group_id} for user: {user_id}')
	print(f'[DEBUG] Update data: {group_data.model_dump(exclude_unset=True)}')

	group_repo = GroupRepo(db)

	updated_group = group_repo.update_group(
		group_id=group_id,
		update_data=group_data.model_dump(exclude_unset=True),
		user_id=user_id,
	)
	response_data = GroupResponse.model_validate(updated_group)

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('group_updated_successfully'),
		data=response_data,
	)


@route.delete('/{group_id}', response_model=APIResponse)
@handle_exceptions
async def delete_group(
	group_id: str = Path(..., description='Group ID'),
	db: Session = Depends(get_db),
	current_user: Dict[str, Any] = Depends(get_current_user),
):
	"""Delete a group"""
	user_id = current_user.get('user_id')
	print(f'[DEBUG] Deleting group ID: {group_id} for user: {user_id}')

	group_repo = GroupRepo(db)
	print(f'[DEBUG] Validating user permissions for group deletion')

	result = group_repo.delete_group(group_id, user_id)
	print(f'[DEBUG] Group deleted successfully: {result}')

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('group_deleted_successfully'),
	)


@route.post('/{group_id}/members/invite', response_model=APIResponse)
@handle_exceptions
async def invite_member(
	invite_data: GroupInviteRequest,
	group_id: str = Path(..., description='Group ID'),
	db: Session = Depends(get_db),
	current_user: Dict[str, Any] = Depends(get_current_user),
):
	"""Invite a user to join a group"""
	user_id = current_user.get('user_id')
	group_repo = GroupRepo(db)

	invited_member = group_repo.invite_member(
		group_id=group_id,
		email=invite_data.email,
		role=invite_data.role,
		invited_by=user_id,
	)

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('invitation_sent_successfully'),
		data=GroupMemberResponse.model_validate(invited_member).model_dump(),
	)


@route.get('/{group_id}/members/invite', response_model=APIResponse)
@handle_exceptions
async def get_invitation_status(
	group_id: str = Path(..., description='Group ID'),
	db: Session = Depends(get_db),
	current_user: Dict[str, Any] = Depends(get_current_user),
	page: int = Query(1, ge=1, description='Page number'),
	page_size: int = Query(10, ge=1, le=100, description='Items per page'),
	filters_json: str | None = Query(None, description='JSON string of filters for invitation status'),
):
	"""Get the invitation status for a user in a group"""
	user_id = current_user.get('user_id')
	group_repo = GroupRepo(db)

	print(f'[DEBUG] Fetching invitation status for user ID: {user_id} in group ID: {group_id}')
	print(f'[DEBUG] Filters JSON: {filters_json}')
	filters = []
	if filters_json:
		filters = json.loads(filters_json)
		if not isinstance(filters, list):
			filters = []
	else:
		filters = []
	print(f'[DEBUG] Parsed filters: {filters}')
	request = SearchGroupRequest(
		page=page,
		page_size=page_size,
		filters=filters,
	)
	print(f'[DEBUG] Search request for invitation status: {request.model_dump()}')
	############################################################################
	# Fetch the invitation status for the user in the group
	############################################################################

	invitation_status: Pagination[GroupMember] = group_repo.get_invitation_status(group_id, user_id, request.model_dump())

	print(f'[DEBUG] Invitation status retrieved: {invitation_status.total_count} invitations found')
	items = [GroupMemberResponse.model_validate(member).model_dump() for member in invitation_status.items]
	print(f'[DEBUG] Invitation status items: {len(items)}')
	return_data = PaginatedResponse(
		items=items,
		paging=PagingInfo(
			total=invitation_status.total_count,
			total_pages=invitation_status.total_pages,
			page=page,
			page_size=page_size,
		),
	)
	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('invitation_status_retrieved_successfully'),
		data=return_data,
	)


@route.get('/{group_id}/members', response_model=APIResponse)
@handle_exceptions
async def list_group_members(
	group_id: str = Path(..., description='Group ID'),
	role: Optional[GroupMemberRole] = Query(None, description='Filter by role'),
	join_status: Optional[GroupMemberJoinStatus] = Query(None, description='Filter by join status'),
	page: int = Query(1, ge=1, description='Page number'),
	page_size: int = Query(10, ge=1, le=100, description='Items per page'),
	db: Session = Depends(get_db),
	current_user: Dict[str, Any] = Depends(get_current_user),
):
	"""List members of a group"""
	user_id = current_user.get('user_id')
	group_repo = GroupRepo(db)

	search_params = []
	if role:
		search_params.append({
			'field': 'role',
			'operator': 'eq',
			'value': role,
		})
	if join_status:
		search_params.append({
			'field': 'join_status',
			'operator': 'eq',
			'value': join_status,
		})

	request = SearchGroupRequest(
		page=page,
		page_size=page_size,
		filters=search_params,
	)

	members_pagination = group_repo.list_members(group_id, user_id, request.model_dump())

	items = [GroupMemberResponse.model_validate(member).model_dump() for member in members_pagination.items]

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('members_retrieved_successfully'),
		data=PaginatedResponse(
			items=items,
			paging=PagingInfo(
				total=members_pagination.total_count,
				total_pages=members_pagination.total_pages,
				page=page,
				page_size=page_size,
			),
		),
	)


@route.post(
	'/{group_id}/members/{member_id}/respond',
	response_model=APIResponse,
)
@handle_exceptions
async def respond_to_invitation(
	action_data: GroupMemberActionRequest,
	member_id: str = Path(..., description='Member ID'),
	db: Session = Depends(get_db),
	current_user: Dict[str, Any] = Depends(get_current_user),
):
	"""Respond to a group invitation (accept or reject)"""
	user_id = current_user.get('user_id')
	group_repo = GroupRepo(db)

	updated_member = group_repo.respond_to_invite(member_id=member_id, user_id=user_id, action=action_data.action)

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('invitation_response_successful'),
		data=GroupMemberResponse.model_validate(updated_member).model_dump(),
	)


@route.delete('/{group_id}/members/{member_user_id}', response_model=APIResponse)
@handle_exceptions
async def remove_member(
	group_id: str = Path(..., description='Group ID'),
	member_user_id: str = Path(..., description='User ID of the member to remove'),
	db: Session = Depends(get_db),
	current_user: Dict[str, Any] = Depends(get_current_user),
):
	"""Remove a member from a group"""
	user_id = current_user.get('user_id')
	group_repo = GroupRepo(db)

	group_repo.remove_member(group_id=group_id, member_user_id=member_user_id, removed_by_user_id=user_id)

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('member_removed_successfully'),
	)
