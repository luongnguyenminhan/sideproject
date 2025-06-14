from fastapi import APIRouter, Depends, Query, Path
from typing import Optional

from app.core.base_model import APIResponse, PagingInfo
from app.enums.base_enums import BaseErrorCode
from app.exceptions.exception import CustomHTTPException
from app.exceptions.handlers import handle_exceptions
from app.http.oauth2 import get_current_user
from app.middleware.auth_middleware import verify_token
from app.middleware.translation_manager import _
from app.modules.groups.repository.group_repo import GroupRepo
from app.modules.groups.schemas.groups import (
    GroupCreate, 
    GroupUpdate, 
    GroupResponse, 
    GroupMemberResponse,
    GroupRequestResponse,
    InviteMemberRequest,
    JoinGroupRequest,
    ApproveRequestRequest,
    UpdateNicknameRequest,
    GroupMemberFilter,
    GroupRequestFilter,
    BulkInviteRequest,
    SearchGroupRequest
)

route = APIRouter(prefix='/groups', tags=['Groups'], dependencies=[Depends(verify_token)])

# Group CRUD Operations
@route.post('/', response_model=APIResponse)
@handle_exceptions
async def create_group(
    group_data: GroupCreate,
    current_user_payload: dict = Depends(get_current_user),
    repo: GroupRepo = Depends()
):
    """
    Create a new group
    
    The authenticated user will automatically be set as the group leader.
    """
    user_id = current_user_payload.get('user_id')
    group = repo.create_group(group_data, user_id)
    
    if not group:
        raise CustomHTTPException(message=_('failed_to_create_group'))
    
    return APIResponse(
        error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
        message=_('group_created_successfully'),
        data=GroupResponse.model_validate(group)
    )

@route.get('/', response_model=APIResponse)
@handle_exceptions
async def get_user_groups(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
    current_user_payload: dict = Depends(get_current_user),
    repo: GroupRepo = Depends()
):
    """
    Get groups for the current user
    
    Returns all groups where the current user is a member
    """
    user_id = current_user_payload.get('user_id')
    groups = repo.get_user_groups(user_id)
    
    # Simple pagination logic (can be improved with proper DB pagination)
    total = len(groups)
    start = (page - 1) * page_size
    end = start + page_size
    paginated_groups = groups[start:end] if start < total else []
    total_pages = (total + page_size - 1) // page_size
    
    return APIResponse(
        error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
        message=_('operation_successful'),
        data={
            "items": [GroupResponse.model_validate(group) for group in paginated_groups],
            "paging": {
                "total": total,
                "total_pages": total_pages,
                "page": page,
                "page_size": page_size
            }
        }
    )

@route.get('/{group_id}', response_model=APIResponse)
@handle_exceptions
async def get_group_detail(
    group_id: str = Path(..., title="Group ID"),
    current_user_payload: dict = Depends(get_current_user),
    repo: GroupRepo = Depends()
):
    """
    Get group details by ID
    
    Returns detailed information about a specific group
    """
    user_id = current_user_payload.get('user_id')
    group = repo.get_group_by_id(group_id)
    
    # Check if user is a member of the group
    if not repo.member_dal.is_member(group_id, user_id):
        raise CustomHTTPException(message=_('not_a_member_of_group'))
    
    return APIResponse(
        error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
        message=_('operation_successful'),
        data=GroupResponse.model_validate(group)
    )

@route.put('/{group_id}', response_model=APIResponse)
@handle_exceptions
async def update_group(
    group_data: GroupUpdate,
    group_id: str = Path(..., title="Group ID"),
    current_user_payload: dict = Depends(get_current_user),
    repo: GroupRepo = Depends()
):
    """
    Update group information
    
    Only group leaders can update group information
    """
    user_id = current_user_payload.get('user_id')
    updated_group = repo.update_group(group_id, group_data, user_id)
    
    return APIResponse(
        error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
        message=_('group_updated_successfully'),
        data=GroupResponse.model_validate(updated_group)
    )

@route.delete('/{group_id}', response_model=APIResponse)
@handle_exceptions
async def delete_group(
    group_id: str = Path(..., title="Group ID"),
    current_user_payload: dict = Depends(get_current_user),
    repo: GroupRepo = Depends()
):
    """
    Delete a group
    
    Only the original group leader can delete the group
    """
    user_id = current_user_payload.get('user_id')
    result = repo.delete_group(group_id, user_id)
    
    return APIResponse(
        error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
        message=_('group_deleted_successfully')
    )

# Member Management
@route.get('/{group_id}/members', response_model=APIResponse)
@handle_exceptions
async def get_group_members(
    group_id: str = Path(..., title="Group ID"),
    role: Optional[str] = Query(None, description="Filter by role"),
    search: Optional[str] = Query(None, description="Search by name or nickname"),
    current_user_payload: dict = Depends(get_current_user),
    repo: GroupRepo = Depends()
):
    """
    Get members of a group
    
    Returns all members in a group with optional filtering
    """
    user_id = current_user_payload.get('user_id')
    
    # Check if user is a member of the group
    if not repo.member_dal.is_member(group_id, user_id):
        raise CustomHTTPException(message=_('not_a_member_of_group'))
    
    filters = GroupMemberFilter(role=role, search=search) if role or search else None
    members = repo.get_group_members(group_id, filters)
    
    return APIResponse(
        error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
        message=_('operation_successful'),
        data=[GroupMemberResponse.model_validate(member) for member in members]
    )

@route.post('/{group_id}/invite', response_model=APIResponse)
@handle_exceptions
async def invite_member(
    invite_data: InviteMemberRequest,
    group_id: str = Path(..., title="Group ID"),
    current_user_payload: dict = Depends(get_current_user),
    repo: GroupRepo = Depends()
):
    """
    Invite a user to join the group
    
    Only group leaders can invite new members
    """
    user_id = current_user_payload.get('user_id')
    invitation = repo.invite_member(group_id, invite_data, user_id)
    
    return APIResponse(
        error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
        message=_('invitation_sent_successfully'),
        data=GroupRequestResponse.model_validate(invitation)
    )

@route.post('/{group_id}/join', response_model=APIResponse)
@handle_exceptions
async def request_to_join(
    join_data: JoinGroupRequest,
    group_id: str = Path(..., title="Group ID"),
    current_user_payload: dict = Depends(get_current_user),
    repo: GroupRepo = Depends()
):
    """
    Request to join a group
    
    Send a join request to a group
    """
    user_id = current_user_payload.get('user_id')
    join_request = repo.request_join(group_id, join_data, user_id)
    
    return APIResponse(
        error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
        message=_('join_request_sent_successfully'),
        data=GroupRequestResponse.model_validate(join_request)
    )

@route.post('/requests/{request_id}/approve', response_model=APIResponse)
@handle_exceptions
async def approve_group_request(
    approve_data: ApproveRequestRequest,
    request_id: str = Path(..., title="Request ID"),
    current_user_payload: dict = Depends(get_current_user),
    repo: GroupRepo = Depends()
):
    """
    Approve a group join/invite request
    
    For join requests, only group leaders can approve.
    For invitations, only the invited user can accept.
    """
    user_id = current_user_payload.get('user_id')
    new_member = repo.approve_request(request_id, approve_data, user_id)
    
    return APIResponse(
        error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
        message=_('request_approved_successfully'),
        data=GroupMemberResponse.model_validate(new_member)
    )

@route.post('/requests/{request_id}/reject', response_model=APIResponse)
@handle_exceptions
async def reject_group_request(
    request_id: str = Path(..., title="Request ID"),
    current_user_payload: dict = Depends(get_current_user),
    repo: GroupRepo = Depends()
):
    """
    Reject a group join/invite request
    
    For join requests, only group leaders can reject.
    For invitations, only the invited user can reject.
    """
    user_id = current_user_payload.get('user_id')
    repo.reject_request(request_id, user_id)
    
    return APIResponse(
        error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
        message=_('request_rejected_successfully')
    )

@route.post('/requests/{request_id}/cancel', response_model=APIResponse)
@handle_exceptions
async def cancel_group_request(
    request_id: str = Path(..., title="Request ID"),
    current_user_payload: dict = Depends(get_current_user),
    repo: GroupRepo = Depends()
):
    """
    Cancel a group request
    
    Users can only cancel their own requests
    """
    user_id = current_user_payload.get('user_id')
    repo.cancel_request(request_id, user_id)
    
    return APIResponse(
        error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
        message=_('request_cancelled_successfully')
    )

@route.post('/{group_id}/leave', response_model=APIResponse)
@handle_exceptions
async def leave_group(
    group_id: str = Path(..., title="Group ID"),
    current_user_payload: dict = Depends(get_current_user),
    repo: GroupRepo = Depends()
):
    """
    Leave a group
    
    Members can leave a group. Leaders can't leave if they're the last leader.
    """
    user_id = current_user_payload.get('user_id')
    repo.leave_group(group_id, user_id)
    
    return APIResponse(
        error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
        message=_('left_group_successfully')
    )

@route.post('/{group_id}/members/{member_id}/kick', response_model=APIResponse)
@handle_exceptions
async def kick_member(
    group_id: str = Path(..., title="Group ID"),
    member_id: str = Path(..., title="Member User ID"),
    current_user_payload: dict = Depends(get_current_user),
    repo: GroupRepo = Depends()
):
    """
    Kick a member from the group
    
    Only group leaders can kick members.
    Leaders cannot kick other leaders or themselves.
    """
    user_id = current_user_payload.get('user_id')
    repo.kick_member(group_id, member_id, user_id)
    
    return APIResponse(
        error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
        message=_('member_kicked_successfully')
    )

@route.post('/{group_id}/members/{member_id}/promote', response_model=APIResponse)
@handle_exceptions
async def promote_to_leader(
    group_id: str = Path(..., title="Group ID"),
    member_id: str = Path(..., title="Member User ID"),
    current_user_payload: dict = Depends(get_current_user),
    repo: GroupRepo = Depends()
):
    """
    Promote a member to leader
    
    Only existing leaders can promote members to leader status
    """
    user_id = current_user_payload.get('user_id')
    repo.promote_to_leader(group_id, member_id, user_id)
    
    return APIResponse(
        error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
        message=_('member_promoted_to_leader_successfully')
    )

@route.put('/{group_id}/members/{member_id}/nickname', response_model=APIResponse)
@handle_exceptions
async def update_member_nickname(
    nickname_data: UpdateNicknameRequest,
    group_id: str = Path(..., title="Group ID"),
    member_id: str = Path(..., title="Member User ID"),
    current_user_payload: dict = Depends(get_current_user),
    repo: GroupRepo = Depends()
):
    """
    Update a member's nickname in the group
    
    Users can update their own nicknames
    """
    user_id = current_user_payload.get('user_id')
    
    # Check if updating own nickname or has permission
    if user_id != member_id and not repo.member_dal.is_leader(group_id, user_id):
        raise CustomHTTPException(message=_('cannot_update_other_members_nickname'))
    
    updated_member = repo.update_nickname(group_id, member_id, nickname_data)
    
    return APIResponse(
        error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
        message=_('nickname_updated_successfully'),
        data=GroupMemberResponse.model_validate(updated_member)
    )

@route.get('/{group_id}/requests', response_model=APIResponse)
@handle_exceptions
async def get_group_requests(
    group_id: str = Path(..., title="Group ID"),
    request_type: Optional[str] = Query(None, description="Filter by request type"),
    current_user_payload: dict = Depends(get_current_user),
    repo: GroupRepo = Depends()
):
    """
    Get all pending requests for a group
    
    Only group leaders can see pending requests
    """
    user_id = current_user_payload.get('user_id')
    
    # Check if user is a leader of the group
    if not repo.member_dal.is_leader(group_id, user_id):
        raise CustomHTTPException(message=_('only_leaders_can_view_requests'))
    
    filters = GroupRequestFilter(request_type=request_type) if request_type else None
    requests = repo.get_pending_requests(group_id, filters)
    
    return APIResponse(
        error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
        message=_('operation_successful'),
        data=[GroupRequestResponse.model_validate(req) for req in requests]
    )

@route.get('/requests/me', response_model=APIResponse)
@handle_exceptions
async def get_my_pending_requests(
    request_type: Optional[str] = Query(None, description="Filter by request type"),
    current_user_payload: dict = Depends(get_current_user),
    repo: GroupRepo = Depends()
):
    """
    Get all pending requests for the current user
    
    Returns all group invitations and join requests for the current user
    """
    user_id = current_user_payload.get('user_id')
    filters = GroupRequestFilter(request_type=request_type) if request_type else None
    requests = repo.get_user_pending_requests(user_id, filters)
    
    return APIResponse(
        error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
        message=_('operation_successful'),
        data=[GroupRequestResponse.model_validate(req) for req in requests]
    )

@route.post('/{group_id}/bulk-invite', response_model=APIResponse)
@handle_exceptions
async def bulk_invite_members(
    bulk_data: BulkInviteRequest,
    group_id: str = Path(..., title="Group ID"),
    current_user_payload: dict = Depends(get_current_user),
    repo: GroupRepo = Depends()
):
    """
    Bulk invite multiple users to a group
    
    Only group leaders can invite members
    """
    user_id = current_user_payload.get('user_id')
    result = repo.bulk_invite_members(group_id, bulk_data, user_id)
    
    return APIResponse(
        error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
        message=_('bulk_invitation_completed'),
        data={
            "successful_invites": [GroupRequestResponse.model_validate(req) for req in result.get('successful_invites', [])],
            "successful_count": result.get('successful_count', 0),
            "failed_count": result.get('failed_count', 0),
            "failed_invites": result.get('failed_invites', [])
        }
    )

@route.get('/{group_id}/stats', response_model=APIResponse)
@handle_exceptions
async def get_group_stats(
    group_id: str = Path(..., title="Group ID"),
    current_user_payload: dict = Depends(get_current_user),
    repo: GroupRepo = Depends()
):
    """
    Get group statistics
    
    Returns statistics about the group such as member counts
    """
    user_id = current_user_payload.get('user_id')
    
    # Check if user is a member of the group
    if not repo.member_dal.is_member(group_id, user_id):
        raise CustomHTTPException(message=_('not_a_member_of_group'))
    
    stats = repo.get_group_stats(group_id)
    
    return APIResponse(
        error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
        message=_('operation_successful'),
        data=stats
    )

@route.post('/search', response_model=APIResponse)
@handle_exceptions
async def search_groups(
    search_request: SearchGroupRequest,
    current_user_payload: dict = Depends(get_current_user),
    repo: GroupRepo = Depends()
):
    """
    Search for groups
    
    Search for groups based on provided criteria
    """
    result = repo.search_groups(search_request)
    
    return APIResponse(
        error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
        message=_('operation_successful'),
        data={
            "items": [GroupResponse.model_validate(group) for group in result.items],
            "paging": {
                "page": result.page,
                "page_size": result.page_size,
                "total": result.total,
                "total_pages": result.total_pages
            }
        }
    )