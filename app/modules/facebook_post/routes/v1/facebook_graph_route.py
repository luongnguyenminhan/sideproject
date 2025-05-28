from fastapi import APIRouter, Depends, Query

from app.core.base_model import APIResponse
from app.enums.base_enums import BaseErrorCode
from app.exceptions.handlers import handle_exceptions
from app.middleware.translation_manager import _
from app.modules.facebook_post.repository.facebook_repo import FacebookRepo


route = APIRouter(prefix='/facebook-graph', tags=['Facebook Graph API'])


@route.get('/page-info', response_model=APIResponse)
@handle_exceptions
async def get_page_info_with_posts(
	limit: int = Query(5, ge=1, le=25, description='Number of posts to fetch'),
	repo: FacebookRepo = Depends(),
):
	"""
	Get Facebook page information including posts (cached for 24 hours)

	Args:
	    limit: Number of posts to include (1-25, default: 5)

	Returns:
	    FacebookPageResponse: Page information with posts (from cache or API)
	"""
	page_info = await repo.get_page_info_with_posts(limit=limit)

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('operation_successful'),
		data=page_info,
	)
