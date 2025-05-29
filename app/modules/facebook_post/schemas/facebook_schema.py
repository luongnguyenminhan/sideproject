from typing import List, Optional
from datetime import datetime
from pydantic import Field, ConfigDict

from app.core.base_model import ResponseSchema, APIResponse


class ReactionSummary(ResponseSchema):
	"""Facebook reaction summary"""

	total_count: int = Field(..., description='Total number of reactions')
	viewer_reaction: Optional[str] = Field(None, description="Current user's reaction")


class PagingCursors(ResponseSchema):
	"""Facebook paging cursors"""

	before: Optional[str] = Field(None, description='Before cursor')
	after: Optional[str] = Field(None, description='After cursor')


class PagingInfo(ResponseSchema):
	"""Facebook paging information"""

	cursors: Optional[PagingCursors] = Field(None, description='Paging cursors')
	next: Optional[str] = Field(None, description='Next page URL')


class Reactions(ResponseSchema):
	"""Facebook reactions"""

	data: List[dict] = Field(default_factory=list, description='Reaction data')
	paging: Optional[PagingInfo] = Field(None, description='Paging information')
	summary: Optional[ReactionSummary] = Field(None, description='Reaction summary')


class FacebookPost(ResponseSchema):
	"""Facebook post model"""

	id: str = Field(..., description='Post ID')
	message: Optional[str] = Field(None, description='Post message')
	full_picture: Optional[str] = Field(None, description='Full picture URL')
	created_time: datetime = Field(..., description='Post creation time')
	reactions: Optional[Reactions] = Field(None, description='Post reactions')


class FacebookPosts(ResponseSchema):
	"""Facebook posts collection"""

	data: List[FacebookPost] = Field(default_factory=list, description='List of posts')
	paging: Optional[PagingInfo] = Field(None, description='Paging information')


class FacebookPageInfo(ResponseSchema):
	"""Facebook page information"""

	id: str = Field(..., description='Page ID')
	name: str = Field(..., description='Page name')
	picture: Optional[dict] = Field(None, description='Page picture information')
	followers_count: Optional[int] = Field(None, description='Number of followers')
	about: Optional[str] = Field(None, description='Page about information')
	emails: Optional[List[str]] = Field(default_factory=list, description='Page emails')
	website: Optional[str] = Field(None, description='Page website')
	single_line_address: Optional[str] = Field(None, description='Page address')
	posts: Optional[FacebookPosts] = Field(None, description='Page posts')


class FacebookPageResponse(APIResponse):
	"""Facebook page API response"""

	data: Optional[FacebookPageInfo] = Field(None, description='Facebook page data')


class FacebookPostsResponse(APIResponse):
	"""Facebook posts API response"""

	data: Optional[List[FacebookPost]] = Field(None, description='Facebook posts data')
