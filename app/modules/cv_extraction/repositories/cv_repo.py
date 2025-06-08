import aiohttp
import aiofiles
import uuid
import os
from app.core.base_model import APIResponse
from app.middleware.translation_manager import _
from app.modules.cv_extraction.repositories.cv_agent import CVAnalyzer
from app.modules.cv_extraction.schemas.cv import ProcessCVRequest
from app.utils.pdf import (
	PDFToTextConverter,
)


class CVRepository:
	async def process_cv(self, request: ProcessCVRequest) -> APIResponse:
		print('[DEBUG] Starting process_cv method with request:', request)
		# DOWNLOAD CV FROM URL
		print(f'[DEBUG] Attempting to download CV from URL: {request.cv_file_url}')
		file_path = await self._download_file(request.cv_file_url)
		if not file_path:
			print('[DEBUG] Download failed, returning error response')
			return APIResponse(
				error_code=1,
				message=_('failed_to_download_file'),
				data=None,
			)

		print(f'[DEBUG] File downloaded successfully to: {file_path}')
		extracted_text = None
		file_extension = 'pdf'
		print(f'[DEBUG] Detected file extension: {file_extension}')
		converter = None

		try:
			if file_extension == 'pdf':
				print('[DEBUG] Processing PDF file')
				converter = PDFToTextConverter(file_path=file_path)
				print('[DEBUG] Initialized PDFToTextConverter')
				extracted_text = converter.extract_text()
				print(f'[DEBUG] PDF text extraction complete, extracted {len(extracted_text)} characters')
			else:
				print(f'[DEBUG] Unsupported file type detected: {file_extension}')
				if os.path.exists(file_path):
					print(f'[DEBUG] Removing unsupported file: {file_path}')
					os.remove(file_path)
				return APIResponse(
					error_code=1,
					message=_('unsupported_cv_file_type'),
					data=None,
				)

		except Exception as e:
			print(f'[DEBUG] Exception during text extraction: {str(e)}')
			print(f'[DEBUG] Exception type: {type(e).__name__}')
			return APIResponse(
				error_code=1,
				message=_('error_extracting_cv_content'),
				data=None,
			)
		finally:
			print('[DEBUG] Entering finally block for cleanup')
			if isinstance(converter, PDFToTextConverter):
				print('[DEBUG] Closing PDF converter')
				converter.close()
			if os.path.exists(file_path):
				print(f'[DEBUG] Removing temporary file: {file_path}')
				os.remove(file_path)

		print('[DEBUG] Process completed successfully')
		print(f'[DEBUG] Extracted text length: {len(extracted_text) if extracted_text else 0}')
		if not extracted_text:
			print('[DEBUG] No text extracted, returning error response')
			return APIResponse(
				error_code=1,
				message=_('no_text_extracted'),
				data=None,
			)

		cv_analyzer = CVAnalyzer()
		print('[DEBUG] Initialized CVAnalyzer')
		try:
			print('[DEBUG] Starting CV analysis')
			print(f'[DEBUG] Extracted text: {extracted_text}')
			result = await cv_analyzer.analyze_cv_content(extracted_text['text'])
			print(f'[DEBUG] CV analysis result: {result}')
		except Exception as e:
			print(f'[DEBUG] Exception during CV analysis: {str(e)}')
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
				'extracted_text': extracted_text['text'],
				'cv_analysis_result': result,
			},
		)

	async def _download_file(self, url: str) -> str | None:
		temp_dir = 'temp_cvs'
		if not os.path.exists(temp_dir):
			os.makedirs(temp_dir)
			print(f'Created temporary directory: {temp_dir}')

		# Extract file extension from the URL
		file_extension = 'pdf'
		if file_extension not in ['pdf', 'docx', 'txt']:
			# Print a message about invalid file type
			print(f'Invalid file type: {file_extension} for URL: {url}')
			return None

		file_name = f'cv_{uuid.uuid4()}.{file_extension}'
		file_path = os.path.join(temp_dir, file_name)
		print(f'Attempting to download file from {url} to {file_path}')

		try:
			async with aiohttp.ClientSession() as session:
				async with session.get(url, ssl=False) as response:  # Thêm ssl=False để bỏ qua SSL verification
					print(f'Response: {response}')
					if response.status == 200:
						print(f'Download successful (Status: {response.status})')
						async with aiofiles.open(file_path, 'wb') as f:
							await f.write(await response.read())
						print(f'File saved to {file_path}')
						return file_path
					else:
						print(f'Failed to download file from {url}, status: {response.status}')
						return None

		except Exception as e:
			print(f'Error downloading file from {url}: {e}')
			return None
