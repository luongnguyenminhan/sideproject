import aiohttp
import aiofiles  # type: ignore
import uuid
import os
from app.core.base_model import APIResponse
from app.middleware.translation_manager import _
from app.modules.cv_extraction.schemas.cv import ProcessCVRequest


class CVRepository:
    async def process_cv(self, request: ProcessCVRequest) -> APIResponse:
        # DOWNLOAD CV FROM URL
        file_path = await self._download_file(request.cv_file_url)
        if not file_path:
            return APIResponse(
                error_code=1,
                message=_("failed_to_download_file"),
                data=None,
            )

        # SEND FILE TO N8N API FOR ANALYSIS
        try:
            result = await self._send_file_to_api(file_path)
            if not result:
                return APIResponse(
                    error_code=1,
                    message=_("error_analyzing_cv"),
                    data=None,
                )
        except Exception as e:
            return APIResponse(
                error_code=1,
                message=_("error_analyzing_cv"),
                data=None,
            )
        finally:
            # Clean up the downloaded file
            if os.path.exists(file_path):
                os.remove(file_path)

        return APIResponse(
            error_code=0,
            message=_("cv_processed_successfully"),
            data={
                "cv_file_url": request.cv_file_url,
                "cv_analysis_result": result,
            },
        )

    async def process_cv_binary(
        self, request: ProcessCVRequest, file_content: bytes, filename: str
    ) -> APIResponse:
        """Process CV from binary file content"""
        # Save binary content to temporary file
        temp_dir = "temp_cvs"
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        # Generate unique filename
        file_extension = filename.split(".")[-1].lower()
        unique_filename = f"cv_{uuid.uuid4()}.{file_extension}"
        file_path = os.path.join(temp_dir, unique_filename)

        try:
            # Write binary content to file
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(file_content)

            # SEND FILE TO N8N API FOR ANALYSIS
            result = await self._send_file_to_api(file_path)
            if not result:
                return APIResponse(
                    error_code=1,
                    message=_("error_analyzing_cv"),
                    data=None,
                )

            return APIResponse(
                error_code=0,
                message=_("cv_processed_successfully"),
                data={
                    "filename": filename,
                    "cv_analysis_result": result,
                },
            )

        except Exception as e:
            return APIResponse(
                error_code=1,
                message=_("error_analyzing_cv"),
                data=None,
            )
        finally:
            # Clean up the temporary file
            if os.path.exists(file_path):
                os.remove(file_path)

    async def _download_file(self, url: str) -> str | None:
        temp_dir = "temp_cvs"
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        # Extract file extension from the URL
        try:
            # Try to get extension from URL
            url_lower = url.lower()
            if ".pdf" in url_lower:
                file_extension = "pdf"
            elif ".docx" in url_lower:
                file_extension = "docx"
            elif ".txt" in url_lower:
                file_extension = "txt"
            else:
                file_extension = "pdf"  # Default to PDF
        except:
            file_extension = "pdf"  # Default fallback

        if file_extension not in ["pdf", "docx", "txt"]:
            return None

        file_name = f"cv_{uuid.uuid4()}.{file_extension}"
        file_path = os.path.join(temp_dir, file_name)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, ssl=False
                ) as response:  # Thêm ssl=False để bỏ qua SSL verification
                    if response.status == 200:
                        async with aiofiles.open(file_path, "wb") as f:
                            await f.write(await response.read())
                        return file_path
                    else:
                        return None

        except Exception as e:
            return None

    async def _send_file_to_api(self, file_path: str) -> dict | None:
        """Send file binary data to N8N API for CV analysis"""
        api_url = "https://n8n.wc504.io.vn/webhook/888a07e8-25d6-4671-a36c-939a52740f31"
        headers = {"X-Header-Authentication": "n8ncvextraction"}

        try:
            async with aiofiles.open(file_path, "rb") as f:
                file_data = await f.read()

            # Get filename from path
            filename = os.path.basename(file_path)

            # Determine content type based on file extension
            file_extension = filename.split(".")[-1].lower()
            content_type_map = {
                "pdf": "application/pdf",
                "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "txt": "text/plain",
            }
            content_type = content_type_map.get(
                file_extension, "application/octet-stream"
            )

            # Create form data with the file
            data = aiohttp.FormData()
            data.add_field(
                "file", file_data, filename=filename, content_type=content_type
            )

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    api_url, headers=headers, data=data, ssl=False
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result
                    else:
                        return None

        except Exception as e:
            return None
