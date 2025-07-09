"""
N8N API Client for Question Composer
Client để gọi N8N API thay vì local question composer module
"""

import logging
import httpx
import aiohttp
import uuid
import time
from typing import Dict, Any, Optional, Union
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class N8NAPIClient:
    """Unified client for N8N API calls (questions generation and CV analysis)"""

    def __init__(self):
        self.base_url = "https://n8n.wc504.io.vn"
        self.question_webhook_endpoint = (
            "/webhook/888a07e8-25d6-4671-a36c-939a52740f31/ask"
        )
        self.cv_webhook_endpoint = "/webhook/888a07e8-25d6-4671-a36c-939a52740f31"
        self.chat_webhook_endpoint = (
            "/webhook/786eb3d9-73e7-406e-acd9-3e4dfcb67e87/chat"
        )
        self.timeout = 30.0

    async def call_chat_workflow(
        self,
        conversation_id: str,
        user_message: str,
        user_id: str,
        authorization_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Call N8N chat workflow API

        Args:
            conversation_id: ID của conversation
            user_message: Tin nhắn người dùng
            user_id: ID người dùng
            authorization_token: Token xác thực

        Returns:
            Response từ N8N chat workflow
        """
        logger.info(
            f"🚀 [N8NAPIClient] Calling N8N chat workflow for conversation: {conversation_id}"
        )

        url = f"{self.base_url}{self.chat_webhook_endpoint}"
        start_time = time.time()

        # Prepare request body
        request_body = {
            "content": user_message,
            "conversation_id": conversation_id,
            "user_id": user_id,
        }

        # Prepare headers
        headers = {"Content-Type": "application/json"}

        if authorization_token:
            headers["Authorization"] = f"Bearer {authorization_token}"
            logger.info(f"🔑 [N8NAPIClient] Authorization token provided")
        else:
            logger.warning(f"⚠️ [N8NAPIClient] No authorization token provided")

        try:
            logger.info(f"📤 [N8NAPIClient] Sending chat request to: {url}")
            logger.info(f"📝 [N8NAPIClient] Request body: {request_body}")

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=request_body, headers=headers)

            response_time_ms = int((time.time() - start_time) * 1000)
            logger.info(
                f"📥 [N8NAPIClient] Chat workflow response status: {response.status_code}"
            )

            if response.status_code == 200:
                logger.info(f"🪵 [N8NAPIClient] Raw response text: {response}")
                response_data = response.json()
                logger.info(f"✅ [N8NAPIClient] Chat workflow successful")

                # N8N trả về format: [{"output": "content"}]
                if isinstance(response_data, list) and len(response_data) > 0:
                    output_content = response_data[0].get("output", "")

                    return {
                        "content": output_content,
                        "model_used": "n8n-chat-workflow",
                        "usage": {
                            "prompt_tokens": len(user_message.split()),
                            "completion_tokens": len(output_content.split()),
                            "total_tokens": len(user_message.split())
                            + len(output_content.split()),
                        },
                        "response_time_ms": response_time_ms,
                    }
                else:
                    logger.error(
                        f"❌ [N8NAPIClient] Unexpected response format: {response_data}"
                    )
                    raise HTTPException(
                        status_code=500,
                        detail="N8N Chat workflow returned unexpected format",
                    )
            else:
                logger.error(
                    f"❌ [N8NAPIClient] Chat workflow failed with status: {response.status_code}"
                )
                logger.error(f"❌ [N8NAPIClient] Response text: {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"N8N Chat workflow API call failed: {response.text}",
                )

        except httpx.TimeoutException:
            logger.error(
                f"⏰ [N8NAPIClient] Chat workflow timeout after {self.timeout}s"
            )
            raise HTTPException(
                status_code=408, detail="N8N Chat workflow API request timeout"
            )
        except httpx.RequestError as e:
            logger.error(f"🌐 [N8NAPIClient] Chat workflow network error: {str(e)}")
            raise HTTPException(
                status_code=503, detail=f"N8N Chat workflow API network error: {str(e)}"
            )
        except Exception as e:
            logger.error(
                f"💥 [N8NAPIClient] Chat workflow unexpected error: {str(e)}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=500,
                detail=f"N8N Chat workflow API unexpected error: {str(e)}",
            )

    async def process_survey_response(
        self,
        session_id: str,
        survey_summary: str,
        authorization_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Call N8N API to process survey response and generate insights

        Args:
            session_id: ID của conversation/session
            survey_summary: Tổng hợp câu hỏi và câu trả lời dưới dạng text
            authorization_token: Token từ user header

        Returns:
            Response từ N8N API (insights, recommendations, etc.)
        """
        logger.info(
            f"🚀 [N8NAPIClient] Processing survey response for session: {session_id}"
        )

        url = f"{self.base_url}{self.question_webhook_endpoint}"

        # Prepare request body - include survey summary for analysis
        request_body = {
            "sessionId": session_id,
            "type": "survey_response_analysis",
            "surveySummary": survey_summary,
        }

        # Prepare headers
        headers = {"Content-Type": "application/json"}

        if authorization_token:
            headers["Authorization"] = f"Bearer {authorization_token}"
            headers["X-Header-Authentication"] = "n8ncvextraction"
            logger.info(f"🔑 [N8NAPIClient] Authorization token provided")
        else:
            logger.warning(f"⚠️ [N8NAPIClient] No authorization token provided")

        try:
            logger.info(f"📤 [N8NAPIClient] Sending survey analysis request to: {url}")
            logger.info(
                f"📝 [N8NAPIClient] Request body keys: {list(request_body.keys())}"
            )

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=request_body, headers=headers)

            logger.info(
                f"📥 [N8NAPIClient] Survey analysis response status: {response.status_code}"
            )

            if response.status_code == 200:
                response_data = response.json()
                logger.info(f"✅ [N8NAPIClient] Survey analysis successful")
                logger.info(
                    f'📊 [N8NAPIClient] Response keys: {list(response_data.keys()) if isinstance(response_data, dict) else "Non-dict response"}'
                )
                return response_data
            else:
                logger.error(
                    f"❌ [N8NAPIClient] Survey analysis failed with status: {response.status_code}"
                )
                logger.error(f"❌ [N8NAPIClient] Response text: {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"N8N Survey Analysis API call failed: {response.text}",
                )

        except httpx.TimeoutException:
            logger.error(
                f"⏰ [N8NAPIClient] Survey analysis timeout after {self.timeout}s"
            )
            raise HTTPException(
                status_code=408, detail="N8N Survey Analysis API request timeout"
            )
        except httpx.RequestError as e:
            logger.error(f"🌐 [N8NAPIClient] Survey analysis network error: {str(e)}")
            raise HTTPException(
                status_code=503,
                detail=f"N8N Survey Analysis API network error: {str(e)}",
            )
        except Exception as e:
            logger.error(
                f"💥 [N8NAPIClient] Survey analysis unexpected error: {str(e)}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=500,
                detail=f"N8N Survey Analysis API unexpected error: {str(e)}",
            )

    async def generate_questions(
        self,
        session_id: str,
        authorization_token: Optional[str] = None,
        custom_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Call N8N API to generate questions

        Args:
            session_id: ID của conversation/session (mapped to sessionId in request)
            authorization_token: Token từ user header

        Returns:
            Response từ N8N API
        """
        logger.info(f"🚀 [N8NAPIClient] Calling N8N API for session: {session_id}")

        url = f"{self.base_url}{self.question_webhook_endpoint}"

        # Prepare request body - use sessionId as specified by user
        request_body = {"sessionId": session_id, "customPrompt": custom_prompt}

        # Prepare headers
        headers = {"Content-Type": "application/json"}

        if authorization_token:
            headers["Authorization"] = f"Bearer {authorization_token}"
            headers["X-Header-Authentication"] = "n8ncvextraction"
            logger.info(f"🔑 [N8NAPIClient] Authorization token provided")
        else:
            logger.warning(f"⚠️ [N8NAPIClient] No authorization token provided")

        try:
            logger.info(f"📤 [N8NAPIClient] Sending request to: {url}")
            logger.info(f"📝 [N8NAPIClient] Request body: {request_body}")

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=request_body, headers=headers)

            logger.info(f"📥 [N8NAPIClient] Response status: {response.status_code}")

            if response.status_code == 200:
                response_data = response.json()
                logger.info(f"✅ [N8NAPIClient] API call successful")
                logger.info(
                    f'📊 [N8NAPIClient] Response keys: {list(response_data.keys()) if isinstance(response_data, dict) else "Non-dict response"}'
                )
                return response_data
            else:
                logger.error(
                    f"❌ [N8NAPIClient] API call failed with status: {response.status_code}"
                )
                logger.error(f"❌ [N8NAPIClient] Response text: {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"N8N API call failed: {response.text}",
                )

        except httpx.TimeoutException:
            logger.error(f"⏰ [N8NAPIClient] Request timeout after {self.timeout}s")
            raise HTTPException(status_code=408, detail="N8N API request timeout")
        except httpx.RequestError as e:
            logger.error(f"🌐 [N8NAPIClient] Network error: {str(e)}")
            raise HTTPException(
                status_code=503, detail=f"N8N API network error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"💥 [N8NAPIClient] Unexpected error: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500, detail=f"N8N API unexpected error: {str(e)}"
            )

    async def analyze_cv(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Call N8N API to analyze CV content

        Args:
            file_content: Binary content of the CV file
            filename: Original filename

        Returns:
            CV analysis result from N8N API
        """
        logger.info(f"🚀 [N8NAPIClient] Calling N8N CV API for file: {filename}")

        url = f"{self.base_url}{self.cv_webhook_endpoint}"

        # Prepare headers with authentication
        headers = {"X-Header-Authentication": "n8ncvextraction"}

        # Determine content type based on file extension
        file_extension = filename.split(".")[-1].lower()
        content_type_map = {
            "pdf": "application/pdf",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "txt": "text/plain",
        }
        content_type = content_type_map.get(file_extension, "application/octet-stream")

        try:
            logger.info(f"📤 [N8NAPIClient] Sending CV file to: {url}")

            # Create form data with the file
            data = aiohttp.FormData()
            data.add_field(
                "data", file_content, filename=filename, content_type=content_type
            )

            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as session:
                async with session.post(
                    url, headers=headers, data=data, ssl=False
                ) as response:
                    logger.info(
                        f"📥 [N8NAPIClient] CV API response status: {response.status}"
                    )

                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"✅ [N8NAPIClient] CV analysis successful")
                        # N8N CV API returns array, get first element
                        return (
                            result[0]
                            if isinstance(result, list) and len(result) > 0
                            else result
                        )
                    else:
                        error_text = await response.text()
                        logger.error(
                            f"❌ [N8NAPIClient] CV API failed with status: {response.status}"
                        )
                        logger.error(
                            f"❌ [N8NAPIClient] CV API error response: {error_text}"
                        )
                        raise HTTPException(
                            status_code=response.status,
                            detail=f"N8N CV API failed: {error_text}",
                        )

        except aiohttp.ClientTimeout:
            logger.error(f"⏰ [N8NAPIClient] CV API timeout after {self.timeout}s")
            raise HTTPException(status_code=408, detail="N8N CV API request timeout")
        except aiohttp.ClientError as e:
            logger.error(f"🌐 [N8NAPIClient] CV API network error: {str(e)}")
            raise HTTPException(
                status_code=503, detail=f"N8N CV API network error: {str(e)}"
            )
        except Exception as e:
            logger.error(
                f"💥 [N8NAPIClient] CV API unexpected error: {str(e)}", exc_info=True
            )
            raise HTTPException(
                status_code=500, detail=f"N8N CV API unexpected error: {str(e)}"
            )

    async def download_file_content(self, url: str) -> tuple[bytes | None, str]:
        """
        Download file content from URL

        Args:
            url: File URL to download

        Returns:
            Tuple of (file_content, filename) or (None, "") if failed
        """
        logger.info(f"📥 [N8NAPIClient] Downloading file from URL: {url}")

        try:
            # Determine file extension from URL
            url_lower = url.lower()
            if ".pdf" in url_lower:
                file_extension = "pdf"
            elif ".docx" in url_lower:
                file_extension = "docx"
            elif ".txt" in url_lower:
                file_extension = "txt"
            else:
                file_extension = "pdf"  # Default to PDF

            if file_extension not in ["pdf", "docx", "txt"]:
                logger.error(
                    f"❌ [N8NAPIClient] Unsupported file extension: {file_extension}"
                )
                return None, ""

            # Generate filename
            filename = f"cv_{uuid.uuid4()}.{file_extension}"

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)

                if response.status_code == 200:
                    logger.info(
                        f"✅ [N8NAPIClient] File downloaded successfully: {filename}"
                    )
                    return response.content, filename
                else:
                    logger.error(
                        f"❌ [N8NAPIClient] Failed to download file: {response.status_code}"
                    )
                    return None, ""

        except Exception as e:
            logger.error(
                f"💥 [N8NAPIClient] Error downloading file: {str(e)}", exc_info=True
            )
            return None, ""


# Singleton instance
n8n_client = N8NAPIClient()
