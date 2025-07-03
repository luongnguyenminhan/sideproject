import time
import asyncio
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.modules.cv_generation.services.ai_template_service import AITemplateService
from app.modules.cv_generation.services.html_generator import HTMLGeneratorService
from app.modules.cv_extraction.schemas.cv import ProcessCVResponse
from app.modules.cv_generation.schemas.cv_generation_response import (
    CVGenerationResponse,
)
from app.modules.cv_generation.repository.cv_generation_repo import (
    CVGenerationRepository,
)
from app.utils.minio.minio_handler import MinioHandler
import os
import logging
import json

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class CVGenerationService:
    """Main service cho CV generation workflow với database tracking"""

    def __init__(self, db: Session = None):
        self.ai_service = AITemplateService()
        self.html_service = HTMLGeneratorService()
        self.minio_handler = MinioHandler()
        self.db = db
        if db:
            self.repo = CVGenerationRepository(db)

    async def generate_cv_pdf(
        self,
        cv_data: ProcessCVResponse,
        template_type: str = "modern",
        custom_prompt: Optional[str] = None,
        color_theme: str = "blue",
        filename: Optional[str] = None,
        user_id: Optional[str] = None,
        cv_extraction_id: Optional[str] = None,
    ) -> CVGenerationResponse:
        """
        Main workflow tạo CV PDF với database tracking

        Args:
            cv_data: CV data từ extraction module
            template_type: Loại template
            custom_prompt: Custom prompt cho AI
            color_theme: Màu theme
            filename: Tên file output
            user_id: ID của user (optional)
            cv_extraction_id: ID từ cv_extraction (optional)

        Returns:
            CVGenerationResponse
        """
        start_time = time.time()
        job = None

        # Comprehensive logging at start
        logger.info("🚀 =================CV GENERATION SERVICE START=================")
        logger.info(f"📊 Parameters:")
        logger.info(f"   - template_type: {template_type}")
        logger.info(f"   - color_theme: {color_theme}")
        logger.info(f'   - custom_prompt: {"Yes" if custom_prompt else "No"}')
        logger.info(f"   - filename: {filename}")
        logger.info(f"   - user_id: {user_id}")
        logger.info(f"   - cv_extraction_id: {cv_extraction_id}")

        # Log CV data summary
        try:
            if cv_data:
                cv_summary = {
                    "type": type(cv_data).__name__,
                    "has_personal_info": bool(getattr(cv_data, "personal_info", None)),
                    "has_experience": bool(getattr(cv_data, "work_experience", None)),
                    "has_education": bool(getattr(cv_data, "education", None)),
                    "has_skills": bool(getattr(cv_data, "skills", None)),
                }
                logger.info(f"📄 CV Data Summary: {json.dumps(cv_summary, indent=2)}")
            else:
                logger.warning("❌ No CV data provided!")
        except Exception as e:
            logger.warning(f"⚠️ Could not analyze CV data: {e}")

        try:
            # Tạo job record trong database nếu có db session
            if self.repo:
                logger.info("💾 Creating database job record...")
                generation_config = {
                    "template_type": template_type,
                    "color_theme": color_theme,
                    "custom_prompt": custom_prompt,
                    "filename": filename,
                }

                # Convert CV data to dict for storage
                cv_data_snapshot = cv_data.dict() if cv_data else None

                job = self.repo.create_job(
                    template_type=template_type,
                    color_theme=color_theme,
                    user_id=user_id,
                    cv_extraction_id=cv_extraction_id,
                    custom_prompt=custom_prompt,
                    generation_config=generation_config,
                    cv_data_snapshot=cv_data_snapshot,
                )

                # Start processing
                self.repo.start_processing(job.job_id)

                logger.info(f"✅ Started CV generation job: {job.job_id}")
                print(f"🚀 Started CV generation job: {job.job_id}")
            else:
                logger.info("📊 No database session - running without job tracking")

            # Step 1: Tạo HTML template bằng AI
            logger.info("🤖 ========== STEP 1: AI HTML GENERATION ==========")
            print("🤖 Generating HTML template with AI...")
            if job:
                self.repo.update_progress(
                    job.job_id, 30.0, "Generating HTML with AI..."
                )

            ai_result = await self.ai_service.generate_html_template(
                cv_data=cv_data,
                template_type=template_type,
                custom_prompt=custom_prompt,
                color_theme=color_theme,
            )

            html_source = ai_result["html_source"]
            token_usage = ai_result["token_usage"]

            # Log AI result
            logger.info(f"✅ AI generation completed:")
            logger.info(
                f"   - HTML length: {len(html_source) if html_source else 0} characters"
            )
            logger.info(f"   - Token usage: {token_usage}")
            logger.info(
                f'   - HTML preview (first 300 chars): {html_source[:300] if html_source else "None"}...'
            )

            # Step 2: Validate HTML source
            logger.info("📋 ========== STEP 2: HTML VALIDATION ==========")
            print("✅ Validating HTML source...")
            if job:
                self.repo.update_progress(
                    job.job_id, 50.0, "Validating HTML source..."
                )

            validation_result = self.html_service.validate_html_source(html_source)
            logger.info(f"📊 Validation result: {validation_result}")

            if not validation_result["valid"]:
                error_msg = f'HTML validation failed: {validation_result["error"]}'
                logger.error(f"❌ Validation failed: {error_msg}")
                if job:
                    self.repo.fail_job(job.job_id, error_msg)

                return CVGenerationResponse(
                    success=False,
                    message=error_msg,
                    html_source=html_source,
                    llm_token_usage=token_usage,
                )

            logger.info("✅ HTML validation passed!")

            # Step 3: Convert HTML to PDF
            logger.info("📄 ========== STEP 3: HTML TO PDF CONVERSION ==========")
            print("📄 Converting HTML to PDF...")
            if job:
                self.repo.update_progress(job.job_id, 70.0, "Converting HTML to PDF...")

            compilation_result = await self.html_service.compile_html_to_pdf(
                html_source=html_source,
                filename=filename or (job.job_id if job else None),
            )

            logger.info(f"📊 Compilation result summary:")
            logger.info(f'   - Success: {compilation_result.get("success", False)}')
            logger.info(f'   - PDF path: {compilation_result.get("pdf_path", "None")}')
            logger.info(
                f'   - File size: {compilation_result.get("file_size", 0)} bytes'
            )
            if compilation_result.get("error"):
                logger.error(f'   - Error: {compilation_result["error"]}')

            if not compilation_result["success"]:
                error_msg = f'HTML to PDF conversion failed: {compilation_result["error"]}'
                logger.error(f"❌ Conversion failed: {error_msg}")
                if job:
                    self.repo.fail_job(job.job_id, error_msg)

                return CVGenerationResponse(
                    success=False,
                    message=error_msg,
                    html_source=html_source,
                    llm_token_usage=token_usage,
                )

            logger.info("✅ HTML to PDF conversion completed successfully!")

            # Step 4: Upload PDF to MinIO (optional)
            logger.info("☁️ ========== STEP 4: STORAGE UPLOAD ==========")
            pdf_file_url = None
            if job:
                self.repo.update_progress(job.job_id, 90.0, "Uploading to storage...")

            try:
                print("☁️ Uploading PDF to storage...")
                logger.info(
                    f'📤 Uploading PDF to MinIO: {compilation_result["pdf_filename"]}'
                )
                pdf_file_url = await self._upload_pdf_to_storage(
                    compilation_result["pdf_path"], compilation_result["pdf_filename"]
                )
                logger.info(f"✅ Upload successful: {pdf_file_url}")
            except Exception as e:
                logger.warning(f"⚠️ Storage upload failed: {e}")
                print(f"Warning: Could not upload to storage: {e}")
                # Continue without storage upload

            generation_time = time.time() - start_time
            logger.info(f"⏱️ Total generation time: {generation_time:.2f} seconds")

            # Step 5: Complete job in database
            logger.info("💾 ========== STEP 5: DATABASE UPDATE ==========")
            if job:
                llm_usage = {
                    "model_used": "gemini-1.5-flash",
                    "input_tokens": token_usage.input_tokens,
                    "output_tokens": token_usage.output_tokens,
                    "total_tokens": token_usage.total_tokens,
                    "cost_usd": token_usage.price_usd,
                }

                logger.info(f"📊 Updating job with final results: {job.job_id}")
                self.repo.complete_job(
                    job_id=job.job_id,
                    latex_source=latex_source,
                    pdf_file_path=compilation_result["pdf_path"],
                    pdf_file_url=pdf_file_url,
                    file_size=compilation_result["file_size"],
                    generation_time=generation_time,
                    llm_usage=llm_usage,
                )

                logger.info(f"✅ Job completed successfully: {job.job_id}")
                print(f"✅ Completed CV generation job: {job.job_id}")

            # Final response
            response = CVGenerationResponse(
                success=True,
                message="CV generated successfully",
                pdf_file_url=pdf_file_url,
                html_source=html_source,
                file_size=compilation_result["file_size"],
                generation_time=generation_time,
                template_used=template_type,
                llm_token_usage=token_usage,
            )

            logger.info("🎉 ================= CV GENERATION SUCCESS =================")
            logger.info(f"📊 Final Response Summary:")
            logger.info(f"   - Success: {response.success}")
            logger.info(f"   - File size: {response.file_size} bytes")
            logger.info(f"   - Generation time: {response.generation_time:.2f}s")
            logger.info(f'   - PDF URL: {"Yes" if response.pdf_file_url else "No"}')
            logger.info(f"   - Template: {response.template_used}")

            return response

        except Exception as e:
            generation_time = time.time() - start_time
            error_msg = f"CV generation failed: {str(e)}"

            logger.error("❌ ================= CV GENERATION FAILED =================")
            logger.error(f"💥 Error: {error_msg}")
            logger.error(f"⏱️ Failed after: {generation_time:.2f} seconds")
            logger.error(f"🔍 Exception type: {type(e).__name__}")
            logger.error(f'� Job ID: {job.job_id if job else "No job"}')

            # Mark job as failed
            if job:
                logger.info(f"📝 Marking job as failed: {job.job_id}")
                self.repo.fail_job(job.job_id, error_msg)
                print(f"❌ Failed CV generation job: {job.job_id} - {error_msg}")

            return CVGenerationResponse(
                success=False, message=error_msg, generation_time=generation_time
            )

    async def _upload_pdf_to_storage(self, pdf_path: str, filename: str) -> str:
        """Upload PDF to MinIO storage"""
        try:
            bucket_name = "generated-cvs"
            object_name = f"cv-pdfs/{filename}"

            # Upload file
            await self.minio_handler.upload_file(
                bucket_name=bucket_name, object_name=object_name, file_path=pdf_path
            )

            # Get presigned URL
            file_url = await self.minio_handler.get_presigned_url(
                bucket_name=bucket_name,
                object_name=object_name,
                expires_in=3600,  # 1 hour
            )

            return file_url

        except Exception as e:
            raise Exception(f"Storage upload failed: {str(e)}")

    async def generate_cv_preview(
        self,
        cv_data: ProcessCVResponse,
        template_type: str = "modern",
        color_theme: str = "blue",
    ) -> Dict[str, Any]:
        """
        Tạo preview CV (HTML hoặc image)

        Args:
            cv_data: CV data
            template_type: Loại template
            color_theme: Màu theme

        Returns:
            Dict chứa preview info
        """
        try:
            # Tạo HTML template trực tiếp
            ai_result = await self.ai_service.generate_html_template(
                cv_data=cv_data, template_type=template_type, color_theme=color_theme
            )

            html_source = ai_result["html_source"]

            # HTML đã sẵn sàng để preview
            return {
                "success": True,
                "preview_html": html_source,
                "html_source": html_source,
                "template_type": template_type,
                "color_theme": color_theme,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _convert_latex_to_html_preview(
        self, latex_source: str, cv_data: ProcessCVResponse
    ) -> str:
        """Convert LaTeX to HTML preview (simplified)"""
        try:
            # Simplified HTML preview based on CV data
            # This is a basic implementation, có thể enhance later

            html_template = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>CV Preview</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; }
                    .header { text-align: center; margin-bottom: 30px; }
                    .section { margin-bottom: 20px; }
                    .section-title { font-weight: bold; font-size: 18px; margin-bottom: 10px; border-bottom: 2px solid #3498DB; }
                    .item { margin-bottom: 15px; }
                    .item-title { font-weight: bold; }
                    .item-subtitle { color: #666; }
                    .skills { display: flex; flex-wrap: wrap; gap: 10px; }
                    .skill { background: #f0f0f0; padding: 5px 10px; border-radius: 5px; }
                </style>
            </head>
            <body>
            """

            if cv_data.cv_analysis_result:
                analysis = cv_data.cv_analysis_result

                # Personal Information
                if analysis.personal_information:
                    pi = analysis.personal_information
                    html_template += f"""
                    <div class="header">
                        <h1>{pi.full_name or 'N/A'}</h1>
                        <p>{pi.email or ''} | {pi.phone_number or ''}</p>
                        <p>{pi.address or ''}</p>
                    </div>
                    """

                # Summary
                if analysis.cv_summary:
                    html_template += f"""
                    <div class="section">
                        <div class="section-title">Summary</div>
                        <p>{analysis.cv_summary}</p>
                    </div>
                    """

                # Work Experience
                if (
                    analysis.work_experience_history
                    and analysis.work_experience_history.items
                ):
                    html_template += """
                    <div class="section">
                        <div class="section-title">Work Experience</div>
                    """
                    for exp in analysis.work_experience_history.items:
                        html_template += f"""
                        <div class="item">
                            <div class="item-title">{exp.job_title or 'N/A'} - {exp.company_name or 'N/A'}</div>
                            <div class="item-subtitle">{exp.start_date or ''} - {exp.end_date or 'Present'}</div>
                            <ul>
                        """
                        if exp.responsibilities_achievements:
                            for resp in exp.responsibilities_achievements:
                                html_template += f"<li>{resp}</li>"
                        html_template += """
                            </ul>
                        </div>
                        """
                    html_template += "</div>"

                # Education
                if analysis.education_history and analysis.education_history.items:
                    html_template += """
                    <div class="section">
                        <div class="section-title">Education</div>
                    """
                    for edu in analysis.education_history.items:
                        html_template += f"""
                        <div class="item">
                            <div class="item-title">{edu.degree_name or 'N/A'} - {edu.institution_name or 'N/A'}</div>
                            <div class="item-subtitle">{edu.graduation_date or ''}</div>
                        </div>
                        """
                    html_template += "</div>"

                # Skills
                if analysis.skills_summary and analysis.skills_summary.items:
                    html_template += """
                    <div class="section">
                        <div class="section-title">Skills</div>
                        <div class="skills">
                    """
                    for skill in analysis.skills_summary.items:
                        html_template += (
                            f'<div class="skill">{skill.skill_name or "N/A"}</div>'
                        )
                    html_template += """
                        </div>
                    </div>
                    """

            html_template += """
            </body>
            </html>
            """

            return html_template

        except Exception as e:
            return f"<html><body><h1>Preview Error</h1><p>{str(e)}</p></body></html>"

    async def get_available_templates(self) -> Dict[str, Any]:
        """Get danh sách templates có sẵn"""
        try:
            templates = [
                {
                    "template_id": "modern",
                    "template_name": "Modern CV",
                    "template_type": "modern",
                    "description": "Modern 2-column layout with sidebar and accent colors",
                    "color_themes": [
                        "blue",
                        "green",
                        "red",
                        "purple",
                        "orange",
                        "teal",
                    ],
                    "features": [
                        "2-column layout",
                        "Icon support",
                        "Color themes",
                        "Professional fonts",
                    ],
                },
                {
                    "template_id": "classic",
                    "template_name": "Classic CV",
                    "template_type": "classic",
                    "description": "Traditional 1-column layout, professional and minimal",
                    "color_themes": ["black", "blue", "green"],
                    "features": [
                        "1-column layout",
                        "Traditional design",
                        "Minimal colors",
                        "Academic style",
                    ],
                },
                {
                    "template_id": "creative",
                    "template_name": "Creative CV",
                    "template_type": "creative",
                    "description": "Creative design with graphics and visual elements",
                    "color_themes": ["blue", "green", "purple", "orange"],
                    "features": [
                        "Creative layout",
                        "Graphics elements",
                        "Visual skills bars",
                        "Modern fonts",
                    ],
                },
            ]

            return {"templates": templates, "total_count": len(templates)}

        except Exception as e:
            return {"templates": [], "total_count": 0, "error": str(e)}

    def get_html_system_info(self) -> Dict[str, Any]:
        """Get thông tin về HTML to PDF conversion system"""
        return self.html_service.get_weasyprint_info()

    def cleanup_temp_files(self):
        """Cleanup temporary files"""
        self.latex_service.cleanup_temp_files()

    # Database operations (nếu có repository)
    def get_user_jobs(self, user_id: str, limit: int = 50) -> List[Any]:
        """Lấy jobs của user"""
        if not self.repo:
            return []
        return self.repo.get_user_jobs(user_id, limit)

    def get_job_status(self, job_id: str) -> Optional[Any]:
        """Lấy status của job"""
        if not self.repo:
            return None
        return self.repo.get_job_by_id(job_id)

    def get_user_statistics(self, user_id: str) -> Dict[str, Any]:
        """Lấy thống kê của user"""
        if not self.repo:
            return {}
        return self.repo.get_user_statistics(user_id)
