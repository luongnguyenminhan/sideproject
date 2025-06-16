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
		# DOWNLOAD CV FROM URL
		file_path = await self._download_file(request.cv_file_url)
		if not file_path:
			return APIResponse(
				error_code=1,
				message=_('failed_to_download_file'),
				data=None,
			)

		extracted_text = None
		file_extension = 'pdf'
		converter = None

		try:
			if file_extension == 'pdf':
				converter = PDFToTextConverter(file_path=file_path)
				extracted_text = converter.extract_text()
			else:
				if os.path.exists(file_path):
					os.remove(file_path)
				return APIResponse(
					error_code=1,
					message=_('unsupported_cv_file_type'),
					data=None,
				)

		except Exception as e:
			return APIResponse(
				error_code=1,
				message=_('error_extracting_cv_content'),
				data=None,
			)
		finally:
			if isinstance(converter, PDFToTextConverter):
				converter.close()
			if os.path.exists(file_path):
				os.remove(file_path)

		if not extracted_text:
			return APIResponse(
				error_code=1,
				message=_('no_text_extracted'),
				data=None,
			)

		cv_analyzer = CVAnalyzer()
		try:
			result = await cv_analyzer.analyze_cv_content(extracted_text['text'])
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
				'extracted_text': extracted_text['text'],
				'cv_analysis_result': result,
			},
		)

	async def _download_file(self, url: str) -> str | None:
		temp_dir = 'temp_cvs'
		if not os.path.exists(temp_dir):
			os.makedirs(temp_dir)

		# Extract file extension from the URL
		file_extension = 'pdf'
		if file_extension not in ['pdf', 'docx', 'txt']:
			# Print a message about invalid file type
			return None

		file_name = f'cv_{uuid.uuid4()}.{file_extension}'
		file_path = os.path.join(temp_dir, file_name)

		try:
			async with aiohttp.ClientSession() as session:
				async with session.get(url, ssl=False) as response:  # Thêm ssl=False để bỏ qua SSL verification
					if response.status == 200:
						async with aiofiles.open(file_path, 'wb') as f:
							await f.write(await response.read())
						return file_path
					else:
						return None

		except Exception as e:
			return None
