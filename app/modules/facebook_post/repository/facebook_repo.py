import httpx
from fastapi import Depends
from typing import Optional
import hashlib

from app.core.config import get_settings
from app.core.base_repo import BaseRepo
from app.modules.facebook_post.schemas.facebook_schema import FacebookPageInfo, FacebookPost
from app.exceptions.exception import CustomHTTPException, NotFoundException
from app.middleware.translation_manager import _
from app.utils.redis_client import redis_client
import logging


class FacebookRepo(BaseRepo):
    """Facebook Graph API Repository with Redis caching"""
    
    def __init__(self):
        super().__init__()
        self.settings = get_settings()
        self.base_url = self.settings.FACEBOOK_GRAPH_BASE_URL
        self.access_token = self.settings.FACEBOOK_ACCESS_TOKEN
        self.page_id = self.settings.FACEBOOK_PAGE_ID
        self.cache_ttl = 86400  # 24 hours in seconds
    
    def _generate_cache_key(self, endpoint: str, **params) -> str:
        """
        Generate a unique cache key for the request
        
        Args:
            endpoint: API endpoint
            **params: Request parameters
            
        Returns:
            Cache key string
        """
        # Create a unique key based on endpoint and parameters
        key_data = f"facebook_api:{endpoint}:{self.page_id}"
        for key, value in sorted(params.items()):
            key_data += f":{key}={value}"
        
        # Hash the key to ensure consistent length and avoid special characters
        return hashlib.md5(key_data.encode()).hexdigest()
    
    logger = logging.getLogger(__name__)

    async def get_page_info_with_posts(self, limit: int = 5) -> FacebookPageInfo:
        """
        Fetch Facebook page information with posts (with Redis caching)
        
        Args:
            limit: Number of posts to fetch (default: 5)
            
        Returns:
            FacebookPageInfo: Page information with posts
            
        Raises:
            CustomHTTPException: When API call fails
            NotFoundException: When page not found
        """
        print(f"\033[94mINFO: Fetching Facebook page info with {limit} posts for page_id: {self.page_id}\033[0m")
        
        # Generate cache key
        cache_key = self._generate_cache_key("page_info_with_posts", limit=limit)
        print(f"\033[96mDEBUG: Generated cache key: {cache_key}\033[0m")
        
        # Try to get from cache first
        cached_data = await redis_client.get(cache_key)
        if cached_data:
            print(f"\033[92mINFO: Found cached data, returning from cache\033[0m")
            try:
                return FacebookPageInfo.model_validate(cached_data)
            except Exception as e:
                print(f"\033[93mWARNING: Failed to validate cached data: {e}\033[0m")
                await redis_client.delete(cache_key)
        
        # If not in cache, fetch from API
        print(f"\033[94mINFO: No valid cache found, fetching from Facebook API\033[0m")
        try:
            fields = f"name,about,emails,website,single_line_address,posts.limit({limit}){{message,full_picture,created_time,reactions.summary(true)}}"
            
            url = f"{self.base_url}/{self.page_id}"
            params = {
                "fields": fields,
                "access_token": self.access_token
            }
            
            print(f"\033[96mDEBUG: Making request to: {url}\033[0m")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                
                print(f"\033[96mDEBUG: Facebook API response status: {response.status_code}\033[0m")
                
                if response.status_code == 404:
                    print(f"\033[91mERROR: Facebook page not found: {self.page_id}\033[0m")
                    raise NotFoundException(_('facebook_page_not_found'))
                
                if response.status_code != 200:
                    print(f"\033[91mERROR: Facebook API error: {response.status_code}\033[0m")
                    raise CustomHTTPException(
                        message=_('facebook_api_error'),
                        status_code=response.status_code
                    )
                
                data = response.json()
                page_info = FacebookPageInfo.model_validate(data)
                
                # Cache the successful response for 24 hours
                await redis_client.set(cache_key, data, ttl=self.cache_ttl)
                print(f"\033[92mINFO: Successfully cached page info for {self.cache_ttl} seconds\033[0m")
                
                return page_info
                
        except httpx.TimeoutException:
            print(f"\033[91mERROR: Facebook API request timeout\033[0m")
            raise CustomHTTPException(
                message=_('facebook_api_timeout')
            )
        except httpx.RequestError as e:
            print(f"\033[91mERROR: Facebook API connection error: {e}\033[0m")
            raise CustomHTTPException(
                message=_('facebook_api_connection_error')
            )
        except Exception as e:
            if isinstance(e, (CustomHTTPException, NotFoundException)):
                raise e
            print(f"\033[91mERROR: Unexpected error in Facebook API call: {e}\033[0m")
            raise CustomHTTPException(
                message=_('facebook_api_unexpected_error')
            )
