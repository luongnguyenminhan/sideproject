from fastapi import APIRouter, Depends, Header, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.base_model import APIResponse
from app.core.config import FERNET_KEY
from app.core.database import get_db
from app.middleware.translation_manager import _
from app.modules.cv_extraction.schemas.cv import (
	ProcessCVRequest,
	CVRegenRequest,
	CVRegenResponse,
)
from app.modules.cv_extraction.repository.cv_repo import CVRepo
from app.modules.cv_generation.services.cv_generation_service import CVGenerationService
from app.utils.minio.minio_handler import MinioHandler
import uuid


route = APIRouter(prefix='/cv', tags=['CV'])


@route.get('/')
async def get_user_info():
	"""
	Lấy thông tin người dùng hiện tại.
	"""
	return {'message': 'User information retrieved successfully.'}


@route.post('/process', response_model=APIResponse)
async def process_cv(
	request: ProcessCVRequest,
	cv_repo: CVRepo = Depends(CVRepo),
):
	"""
	Xử lý file CV từ URL.
	"""

	# Validate that URL is provided
	if not request.cv_file_url:
		return APIResponse(
			error_code=1,
			message=_('cv_file_url_required'),
			data=None,
		)

	return await cv_repo.process_cv(request)


@route.post('/regen', response_model=APIResponse)
async def regen_cv(
	request: CVRegenRequest,
	cv_repo: CVRepo = Depends(CVRepo),
	db: Session = Depends(get_db),
):
	"""
	Extract CV và regenerate thành PDF file, lưu trên MinIO

	Workflow:
	1. Extract CV data từ URL/file
	2. Generate LaTeX template bằng AI
	3. Compile LaTeX thành PDF
	4. Upload PDF lên MinIO storage
	5. Return PDF download URL
	"""
	try:
		print(f'🔄 Starting CV regen for URL: {request.cv_file_url}')

		# Validate input
		if not request.cv_file_url:
			return APIResponse(error_code=1, message=_('cv_file_url_required'), data=None)

		# Step 1: Extract CV data
		print('📄 Extracting CV data...')
		process_request = ProcessCVRequest(cv_file_url=request.cv_file_url)
		extraction_result = await cv_repo.process_cv(process_request)

		if extraction_result.error_code != 0 or not extraction_result.data:
			return APIResponse(
				error_code=extraction_result.error_code,
				message=f'CV extraction failed: {extraction_result.message}',
				data=None,
			)

		cv_data = extraction_result.data
		print('✅ CV extraction completed')

		# Step 2: Generate CV PDF using CV generation service
		print('🤖 Generating CV PDF...')
		cv_gen_service = CVGenerationService(db=db)

		generation_result = await cv_gen_service.generate_cv_pdf(
			cv_data=cv_data,
			template_type=request.template_type or 'modern',
			custom_prompt=request.custom_prompt,
			color_theme=request.color_theme or 'blue',
			filename=f'cv_{uuid.uuid4().hex[:8]}',
		)

		if not generation_result.success:
			return APIResponse(
				error_code=1,
				message=f'CV generation failed: {generation_result.message}',
				data=CVRegenResponse(
					success=False,
					message=generation_result.message,
					cv_analysis=cv_data,
				),
			)

		print('✅ CV PDF generation completed')

		# Step 3: Upload PDF to MinIO if not already uploaded
		minio_handler = MinioHandler()
		pdf_download_url = generation_result.pdf_file_url

		if not pdf_download_url and generation_result.latex_source:
			print('☁️ Uploading PDF to MinIO...')
			try:
				# Find PDF file path (from generation service)
				pdf_path = None
				if hasattr(generation_result, 'pdf_path'):
					pdf_path = generation_result.pdf_path
				else:
					# Try to find PDF in temp_cvs directory
					import os

					temp_dir = 'temp_cvs'
					for file in os.listdir(temp_dir):
						if file.endswith('.pdf'):
							pdf_path = os.path.join(temp_dir, file)
							break

				if pdf_path and os.path.exists(pdf_path):
					bucket_name = 'cv-generated'
					object_name = f'pdfs/{uuid.uuid4().hex[:8]}.pdf'

					# Upload PDF to MinIO
					await minio_handler.upload_file(
						bucket_name=bucket_name,
						object_name=object_name,
						file_path=pdf_path,
						content_type='application/pdf',
					)

					# Get download URL
					pdf_download_url = await minio_handler.get_presigned_url(
						bucket_name=bucket_name,
						object_name=object_name,
						expires_in=3600,  # 1 hour
					)

					print(f'✅ PDF uploaded to MinIO: {object_name}')

			except Exception as e:
				print(f'⚠️ Failed to upload to MinIO: {str(e)}')
				# Continue without MinIO upload

		# Step 4: Prepare response
		response = CVRegenResponse(
			success=True,
			message='CV regenerated successfully',
			cv_analysis=cv_data,
			pdf_file_url=generation_result.pdf_file_url,
			pdf_download_url=pdf_download_url,
			file_size=generation_result.file_size,
			generation_time=generation_result.generation_time,
			job_id=getattr(generation_result, 'job_id', None),
		)

		print('🎉 CV regen completed successfully')

		return APIResponse(error_code=0, message='CV regenerated successfully', data=response)

	except Exception as e:
		print(f'❌ CV regen failed: {str(e)}')
		return APIResponse(
			error_code=1,
			message=f'CV regeneration failed: {str(e)}',
			data=CVRegenResponse(success=False, message=str(e)),
		)


@route.post('/process-file', response_model=APIResponse)
async def process_cv_binary(
	file: UploadFile = File(...),
	cv_repo: CVRepo = Depends(CVRepo),
):
	"""
	Xử lý file CV từ binary upload.
	"""

	print('[process_cv_binary] Start processing uploaded file.')

	# Validate file type
	print(f'[process_cv_binary] Uploaded filename: {file.filename}')
	if not file.filename or not file.filename.lower().endswith(('.pdf', '.docx', '.txt')):
		print('[process_cv_binary] Unsupported file type.')
		return APIResponse(
			error_code=1,
			message=_('unsupported_file_type'),
			data=None,
		)

	# Read file content
	try:
		print('[process_cv_binary] Reading file content...')
		file_content = await file.read()
		print(f'[process_cv_binary] File content length: {len(file_content)} bytes')
	except Exception as e:
		print(f'[process_cv_binary] Failed to read file: {str(e)}')
		return APIResponse(
			error_code=1,
			message=_('failed_to_read_file'),
			data=None,
		)

	# Create request object without URL but with file data
	print('[process_cv_binary] Creating ProcessCVRequest object.')
	request = ProcessCVRequest()

	print('[process_cv_binary] Calling cv_repo.process_cv_binary...')
	result = await cv_repo.process_cv_binary(request, file_content, file.filename)
	print('[process_cv_binary] Finished processing file.')
	return result


@route.post('/regen-file', response_model=APIResponse)
async def regen_cv_from_file(
	file: UploadFile = File(...),
	template_type: str = 'modern',
	color_theme: str = 'blue',
	custom_prompt: str = None,
	cv_repo: CVRepo = Depends(CVRepo),
	db: Session = Depends(get_db),
):
	"""
	Upload file CV và regenerate thành PDF

	Workflow tương tự regen_cv nhưng nhận file upload thay vì URL
	"""
	try:
		print(f'🔄 Starting CV regen from uploaded file: {file.filename}')

		# Validate file
		if not file.filename or not file.filename.lower().endswith(('.pdf', '.docx', '.txt')):
			return APIResponse(error_code=1, message=_('unsupported_file_type'), data=None)

		# Read file content
		file_content = await file.read()

		# Step 1: Extract CV from file
		print('📄 Extracting CV data from file...')
		process_request = ProcessCVRequest()
		extraction_result = await cv_repo.process_cv_binary(process_request, file_content, file.filename)

		if extraction_result.error_code != 0 or not extraction_result.data:
			return APIResponse(
				error_code=extraction_result.error_code,
				message=f'CV extraction failed: {extraction_result.message}',
				data=None,
			)

		cv_data = extraction_result.data
		print('✅ CV extraction from file completed')

		# Step 2-4: Same as regen_cv
		cv_gen_service = CVGenerationService(db=db)

		generation_result = await cv_gen_service.generate_cv_pdf(
			cv_data=cv_data,
			template_type=template_type,
			custom_prompt=custom_prompt,
			color_theme=color_theme,
			filename=f'cv_from_file_{uuid.uuid4().hex[:8]}',
		)

		if not generation_result.success:
			return APIResponse(
				error_code=1,
				message=f'CV generation failed: {generation_result.message}',
				data=CVRegenResponse(
					success=False,
					message=generation_result.message,
					cv_analysis=cv_data,
				),
			)

		# Upload to MinIO if needed (same logic as regen_cv)
		minio_handler = MinioHandler()
		pdf_download_url = generation_result.pdf_file_url

		if not pdf_download_url:
			try:
				import os

				temp_dir = 'temp_cvs'
				pdf_path = None
				for file_name in os.listdir(temp_dir):
					if file_name.endswith('.pdf'):
						pdf_path = os.path.join(temp_dir, file_name)
						break

				if pdf_path and os.path.exists(pdf_path):
					bucket_name = 'cv-generated'
					object_name = f'pdfs/{uuid.uuid4().hex[:8]}.pdf'

					await minio_handler.upload_file(
						bucket_name=bucket_name,
						object_name=object_name,
						file_path=pdf_path,
						content_type='application/pdf',
					)

					pdf_download_url = await minio_handler.get_presigned_url(
						bucket_name=bucket_name,
						object_name=object_name,
						expires_in=3600,
					)
			except Exception as e:
				print(f'⚠️ Failed to upload to MinIO: {str(e)}')

		response = CVRegenResponse(
			success=True,
			message='CV regenerated from file successfully',
			cv_analysis=cv_data,
			pdf_file_url=generation_result.pdf_file_url,
			pdf_download_url=pdf_download_url,
			file_size=generation_result.file_size,
			generation_time=generation_result.generation_time,
		)

		return APIResponse(error_code=0, message='CV regenerated from file successfully', data=response)

	except Exception as e:
		print(f'❌ CV regen from file failed: {str(e)}')
		return APIResponse(
			error_code=1,
			message=f'CV regeneration from file failed: {str(e)}',
			data=CVRegenResponse(success=False, message=str(e)),
		)
