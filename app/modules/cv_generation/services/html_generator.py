import logging
import os
import subprocess
import tempfile
import uuid
from typing import Dict, Any, Optional
import shutil

logger = logging.getLogger(__name__)


class HTMLGeneratorService:
    """Service xử lý compile HTML thành PDF sử dụng weasyprint"""

    def __init__(self):
        """Initialize HTML generator"""
        self.temp_dir = os.path.join(os.getcwd(), "temp_cvs")
        self.output_dir = self.temp_dir

        # Debug mode check
        self.debug_mode = os.getenv("CV_DEBUG_MODE", "false").lower() == "true"
        if self.debug_mode:
            self.debug_dir = os.path.join(
                os.getcwd(), "debug_html"
            )  # HTML debug directory
            os.makedirs(self.debug_dir, exist_ok=True)
            logger.info("🐛 HTML Debug Mode: ENABLED")

        # Ensure directories exist
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)

    async def compile_html_to_pdf(
        self, html_source: str, filename: Optional[str] = None, cleanup: bool = True
    ) -> Dict[str, Any]:
        """
        Compile HTML source thành PDF using weasyprint

        Args:
            html_source: Source HTML code
            filename: Tên file output (optional)
            cleanup: Có cleanup temp files không

        Returns:
            Dict chứa thông tin file PDF
        """
        try:
            # Tạo unique filename nếu không có
            if not filename:
                filename = f"cv_{uuid.uuid4().hex[:8]}"

            # Tạo paths
            html_filename = f"{filename}.html"
            pdf_filename = f"{filename}.pdf"

            # Tạo temp directory cho compilation
            compile_dir = os.path.join(self.temp_dir, f"compile_{uuid.uuid4().hex[:8]}")
            os.makedirs(compile_dir, exist_ok=True)

            html_path = os.path.join(compile_dir, html_filename)
            pdf_path = os.path.join(compile_dir, pdf_filename)

            # ============ DEBUG MODE - REMOVE IN PRODUCTION ============
            # DEBUG: Save HTML source to debug folder for inspection
            if self.debug_mode:
                debug_filename = f"debug_{filename}_{uuid.uuid4().hex[:4]}.html"
                debug_path = os.path.join(self.debug_dir, debug_filename)
                with open(debug_path, "w", encoding="utf-8") as f:
                    f.write(html_source)
                logger.info(f"🐛 DEBUG: HTML source saved to {debug_path}")
            # ============ END DEBUG MODE ============

            # Clean HTML source
            html_source_clean = self._clean_html(html_source)

            # ============ DEBUG MODE - REMOVE IN PRODUCTION ============
            # DEBUG: Save cleaned HTML source for comparison
            if self.debug_mode:
                debug_clean_filename = (
                    f"debug_{filename}_CLEAN_{uuid.uuid4().hex[:4]}.html"
                )
                debug_clean_path = os.path.join(self.debug_dir, debug_clean_filename)
                with open(debug_clean_path, "w", encoding="utf-8") as f:
                    f.write(html_source_clean)
                logger.info(
                    f"🐛 DEBUG: Cleaned HTML source saved to {debug_clean_path}"
                )
            # ============ END DEBUG MODE ============

            # Write HTML source to file
            try:
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(html_source_clean)
                logger.info(f"✅ HTML source written to: {html_path}")
            except Exception as e:
                logger.error(f"❌ Error writing HTML file: {e}")
                raise

            # Convert HTML to PDF using weasyprint
            conversion_result = await self._convert_html_to_pdf(html_path, pdf_path)

            if not conversion_result["success"]:
                raise Exception(
                    f'HTML to PDF conversion failed: {conversion_result["error"]}'
                )

            # Copy PDF to output directory
            output_pdf_path = os.path.join(self.output_dir, pdf_filename)
            shutil.copy2(pdf_path, output_pdf_path)

            # Get file info
            file_size = os.path.getsize(output_pdf_path)

            # Cleanup temp directory nếu requested
            if cleanup:
                shutil.rmtree(compile_dir, ignore_errors=True)

            return {
                "success": True,
                "pdf_path": output_pdf_path,
                "pdf_filename": pdf_filename,
                "file_size": file_size,
                "html_source": html_source,
                "conversion_log": conversion_result.get("log", ""),
            }

        except Exception as e:
            logger.error(f"❌ HTML to PDF conversion failed: {e}")
            return {"success": False, "error": str(e), "pdf_path": None, "file_size": 0}

    def _clean_html(self, html_source: str) -> str:
        """
        Clean HTML source for better PDF conversion
        """
        try:
            logger.info("🧹 Cleaning HTML source...")

            # Basic cleaning
            html_clean = html_source.strip()

            # Ensure proper doctype
            if not html_clean.startswith("<!DOCTYPE html>"):
                if html_clean.startswith("<html"):
                    html_clean = "<!DOCTYPE html>\n" + html_clean

            # Add viewport meta if missing (for responsive design)
            if '<meta name="viewport"' not in html_clean:
                head_end = html_clean.find("</head>")
                if head_end != -1:
                    meta_viewport = '\n<meta name="viewport" content="width=device-width, initial-scale=1.0">'
                    html_clean = (
                        html_clean[:head_end] + meta_viewport + html_clean[head_end:]
                    )

            # Add print styles if missing
            if "@media print" not in html_clean:
                print_styles = """
<style type="text/css" media="print">
    @page {
        size: A4;
        margin: 0.5in;
    }
    body {
        font-size: 12pt;
        line-height: 1.4;
    }
    .no-print {
        display: none !important;
    }
</style>
"""
                head_end = html_clean.find("</head>")
                if head_end != -1:
                    html_clean = (
                        html_clean[:head_end] + print_styles + html_clean[head_end:]
                    )

            logger.info("✅ HTML cleaning completed")
            return html_clean

        except Exception as e:
            logger.error(f"❌ Error cleaning HTML: {e}")
            return html_source  # Return original if cleaning fails

    async def _convert_html_to_pdf(
        self, html_path: str, pdf_path: str
    ) -> Dict[str, Any]:
        """Convert HTML file to PDF using weasyprint"""
        logger.info(f"🔄 Converting HTML to PDF: {html_path} -> {pdf_path}")

        try:
            # Check if weasyprint is available
            logger.info("🔍 Checking weasyprint availability...")
            try:
                import weasyprint

                logger.info("✅ weasyprint module found")
            except ImportError:
                logger.error("❌ weasyprint module not found")
                return {
                    "success": False,
                    "error": "weasyprint not installed. Please install weasyprint package.",
                }

            # Convert using weasyprint
            try:
                logger.info("🚀 Starting weasyprint conversion...")

                # Use weasyprint Python API
                weasyprint.HTML(filename=html_path).write_pdf(pdf_path)

                logger.info("✅ weasyprint conversion completed successfully")
                return {"success": True, "log": "HTML to PDF conversion successful"}

            except Exception as e:
                logger.error(f"❌ weasyprint conversion failed: {e}")

                # ============ DEBUG MODE - REMOVE IN PRODUCTION ============
                # DEBUG: Save conversion error log
                if hasattr(self, "debug_mode") and self.debug_mode:
                    log_filename = f"conversion_error_{uuid.uuid4().hex[:8]}.log"
                    log_path = os.path.join(self.debug_dir, log_filename)
                    with open(log_path, "w", encoding="utf-8") as f:
                        f.write(f"=== HTML TO PDF CONVERSION ERROR ===\n")
                        f.write(f"Error: {str(e)}\n")
                        f.write(f"HTML path: {html_path}\n")
                        f.write(f"PDF path: {pdf_path}\n")
                    logger.info(f"🐛 DEBUG: Conversion error log saved to {log_path}")
                # ============ END DEBUG MODE ============

                return {
                    "success": False,
                    "error": f"weasyprint conversion failed: {str(e)}",
                    "log": str(e),
                }

        except Exception as e:
            logger.error(f"❌ Unexpected error during HTML to PDF conversion: {e}")
            return {"success": False, "error": str(e)}

    def validate_html_source(self, html_source: str) -> Dict[str, Any]:
        """Validate HTML source code"""
        try:
            # Basic validation
            if not html_source.strip():
                return {"valid": False, "error": "Empty HTML source"}

            # Check for required elements
            required_elements = ["<html", "<body", "</body>", "</html>"]

            for element in required_elements:
                if element not in html_source:
                    return {
                        "valid": False,
                        "error": f"Missing required HTML element: {element}",
                    }

            # Check for basic structure
            if html_source.count("<body") != html_source.count("</body>"):
                return {"valid": False, "error": "Mismatched body tags"}

            if html_source.count("<html") != html_source.count("</html>"):
                return {"valid": False, "error": "Mismatched html tags"}

            logger.info("✅ HTML validation passed")
            return {"valid": True, "message": "HTML source is valid"}

        except Exception as e:
            logger.error(f"❌ Error validating HTML: {e}")
            return {"valid": False, "error": f"Validation error: {str(e)}"}

    def get_weasyprint_info(self) -> Dict[str, Any]:
        """Get weasyprint system info"""
        try:
            info = {"weasyprint_available": False, "version": None, "dependencies": {}}

            # Check weasyprint availability
            try:
                import weasyprint

                info["weasyprint_available"] = True
                info["version"] = weasyprint.__version__
                logger.info(f"✅ weasyprint version: {weasyprint.__version__}")
            except ImportError:
                logger.warning("⚠️ weasyprint not available")

            # Check dependencies
            dependencies = [
                "PIL",
                "cairocffi",
                "cffi",
                "cssselect2",
                "html5lib",
                "tinycss2",
            ]
            for dep in dependencies:
                try:
                    __import__(dep)
                    info["dependencies"][dep] = "✅ Available"
                except ImportError:
                    info["dependencies"][dep] = "❌ Missing"

            return info

        except Exception as e:
            logger.error(f"❌ Error getting weasyprint info: {e}")
            return {"error": str(e), "weasyprint_available": False}

    def cleanup_temp_files(self):
        """Cleanup temporary files"""
        try:
            if os.path.exists(self.temp_dir):
                for file in os.listdir(self.temp_dir):
                    file_path = os.path.join(self.temp_dir, file)
                    if os.path.isfile(file_path):
                        # Keep files newer than 1 hour
                        file_age = os.path.getctime(file_path)
                        current_time = os.path.getctime(self.temp_dir)
                        if current_time - file_age > 3600:  # 1 hour
                            os.remove(file_path)
                            logger.info(f"🗑️ Cleaned up old temp file: {file}")
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path, ignore_errors=True)
        except Exception as e:
            logger.warning(f"⚠️ Error during cleanup: {e}")

    def __del__(self):
        """Cleanup on object destruction"""
        try:
            self.cleanup_temp_files()
        except:
            pass
