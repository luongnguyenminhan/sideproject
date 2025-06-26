import aiohttp
import uuid
from app.core.base_model import APIResponse
from app.middleware.translation_manager import _
from app.modules.cv_extraction.schemas.cv import ProcessCVRequest


class CVRepository:
	async def process_cv(self, request: ProcessCVRequest) -> APIResponse:
		# DOWNLOAD CV FROM URL
		file_content, filename = await self._download_file_content(request.cv_file_url)
		if not file_content:
			return APIResponse(
				error_code=1,
				message=_('failed_to_download_file'),
				data=None,
			)

		# SEND FILE TO N8N API FOR ANALYSIS
		try:
			result = await self._send_file_content_to_api(file_content, filename)
			if not result:
				return APIResponse(
					error_code=1,
					message=_('error_analyzing_cv'),
					data=None,
				)
		except Exception as e:
			return APIResponse(
				error_code=1,
				message=_('error_analyzing_cv'),
				data=None,
			)

		return APIResponse(
			error_code=0,
			message=_('cv_processed_successfully'),
			data={
				'cv_file_url': request.cv_file_url,
				'cv_analysis_result': result,
			},
		)

	async def process_cv_binary(self, request: ProcessCVRequest, file_content: bytes, filename: str) -> APIResponse:
		"""Process CV from binary file content"""
		print('[process_cv_binary] Start processing binary file content.')

		try:
			# SEND FILE TO N8N API FOR ANALYSIS directly
			print(f'[process_cv_binary] Sending file to N8N API for analysis: {filename}')
			result = await self._send_file_content_to_api(file_content, filename)
			if not result:
				print('[process_cv_binary] Error analyzing CV: result is None')
				return APIResponse(
					error_code=1,
					message=_('error_analyzing_cv'),
					data=None,
				)

			print('[process_cv_binary] CV processed successfully.')
			return APIResponse(
				error_code=0,
				message=_('cv_processed_successfully'),
				data={
					'filename': filename,
					'cv_analysis_result': result,
				},
			)

		except Exception as e:
			print(f'[process_cv_binary] Exception occurred: {str(e)}')
			return APIResponse(
				error_code=1,
				message=_('error_analyzing_cv'),
				data=None,
			)

	async def _download_file_content(self, url: str) -> tuple[bytes | None, str]:
		"""Download file content directly to memory without saving to disk"""
		try:
			# Try to get extension from URL
			url_lower = url.lower()
			if '.pdf' in url_lower:
				file_extension = 'pdf'
			elif '.docx' in url_lower:
				file_extension = 'docx'
			elif '.txt' in url_lower:
				file_extension = 'txt'
			else:
				file_extension = 'pdf'  # Default to PDF
		except:
			file_extension = 'pdf'  # Default fallback

		if file_extension not in ['pdf', 'docx', 'txt']:
			return None, ''

		# Generate filename for API
		filename = f'cv_{uuid.uuid4()}.{file_extension}'

		try:
			async with aiohttp.ClientSession() as session:
				async with session.get(url, ssl=False) as response:
					if response.status == 200:
						file_content = await response.read()
						return file_content, filename
					else:
						return None, ''

		except Exception as e:
			print(f'[_download_file_content] Error downloading file: {str(e)}')
			return None, ''

	async def _send_file_content_to_api(self, file_content: bytes, filename: str) -> dict | None:
		"""Send file binary data to N8N API for CV analysis"""
		api_url = 'https://n8n.wc504.io.vn/webhook/888a07e8-25d6-4671-a36c-939a52740f31'
		headers = {'X-Header-Authentication': 'n8ncvextraction'}

		try:
			# Determine content type based on file extension
			file_extension = filename.split('.')[-1].lower()
			content_type_map = {
				'pdf': 'application/pdf',
				'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
				'txt': 'text/plain',
			}
			content_type = content_type_map.get(file_extension, 'application/octet-stream')

			# Create form data with the file
			data = aiohttp.FormData()
			data.add_field('data', file_content, filename=filename, content_type=content_type)
			print(f'[CVRepository] Sending file to N8N API: {filename}')

			async with aiohttp.ClientSession() as session:
				async with session.post(api_url, headers=headers, data=data, ssl=False) as response:
					print(f'[CVRepository] N8N API response status: {response.status}')
					if response.status == 200:
						result = await response.json()[0]
						return result
					else:
						print(f'[CVRepository] N8N API error: {response.status}')
						return None

		except Exception as e:
			print(f'[CVRepository] Error sending file to N8N API: {str(e)}')
			return None
