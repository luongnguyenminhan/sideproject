"""
Service for extracting text content from different file types for indexing
"""

import io
import logging
from typing import Dict, Any
import docx

from app.utils.pdf import PDFToTextConverter

logger = logging.getLogger(__name__)


class FileExtractionService:
    """Service để extract text từ các loại file khác nhau"""

    def __init__(self):
        self.supported_types = {
            "application/pdf": self.extract_pdf_text,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": self.extract_docx_text,
            "text/plain": self.extract_text_file,
            "text/markdown": self.extract_text_file,
            "application/msword": self.extract_doc_text,
        }

    def extract_text_from_file(
        self, file_content: bytes, file_type: str, file_name: str
    ) -> Dict[str, Any]:
        """
        Extract text từ file content theo file type

        Args:
            file_content: Nội dung file dạng bytes
            file_type: MIME type của file
            file_name: Tên file gốc

        Returns:
            Dict chứa extracted text và metadata
        """
        try:
            logger.info(
                f"[FileExtractionService] Extracting text from {file_name}, type: {file_type}"
            )

            # Check if file type is supported first
            if not self.is_supported_file_type(file_type):
                return {
                    "content": "",
                    "file_name": file_name,
                    "file_type": file_type,
                    "char_count": 0,
                    "extraction_success": False,
                    "extraction_error": f"Unsupported file type: {file_type}",
                }

            # Extract text based on file type
            text_content = ""
            if file_type in self.supported_types:
                extraction_method = self.supported_types[file_type]
                text_content = extraction_method(file_content)
            else:
                # Use the improved file content extractor from utils as fallback
                try:
                    from app.utils.file_extraction import FileContentExtractor

                    text_content, error_message = (
                        FileContentExtractor.extract_text_content(
                            file_content, file_type, file_name
                        )
                    )
                    if text_content is None:
                        raise Exception(
                            error_message or f"Extraction failed for {file_type}"
                        )
                except ImportError:
                    # If utils file extraction is not available, use basic extraction
                    if file_type.startswith("text/"):
                        text_content = self.extract_text_file(file_content)
                    else:
                        raise Exception(
                            f"No extraction method available for {file_type}"
                        )

            if text_content and text_content.strip():
                return {
                    "content": text_content,
                    "file_name": file_name,
                    "file_type": file_type,
                    "char_count": len(text_content),
                    "extraction_success": True,
                    "extraction_error": None,
                }
            else:
                return {
                    "content": "",
                    "file_name": file_name,
                    "file_type": file_type,
                    "char_count": 0,
                    "extraction_success": False,
                    "extraction_error": "No content extracted from file",
                }

        except Exception as e:
            logger.error(
                f"[FileExtractionService] Error extracting text from {file_name}: {str(e)}"
            )
            return {
                "content": "",
                "file_name": file_name,
                "file_type": file_type,
                "char_count": 0,
                "extraction_success": False,
                "extraction_error": str(e),
            }

    def extract_pdf_text(self, file_content: bytes) -> str:
        """Extract text từ PDF file"""
        try:
            import io

            pdf_file = io.BytesIO(file_content)

            # Use the PDFToTextConverter from utils
            results = PDFToTextConverter.extract_text_from_file(pdf_file)

            return results.get("text", "")

        except Exception as e:
            logger.error(f"[FileExtractionService] Error extracting PDF: {str(e)}")
            raise

    def extract_docx_text(self, file_content: bytes) -> str:
        """Extract text từ DOCX file"""
        try:
            docx_file = io.BytesIO(file_content)
            doc = docx.Document(docx_file)

            text_parts = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_parts.append(paragraph.text)

            return "\n".join(text_parts)

        except Exception as e:
            logger.error(f"[FileExtractionService] Error extracting DOCX: {str(e)}")
            raise

    def extract_text_file(self, file_content: bytes) -> str:
        """Extract text từ plain text file"""
        try:
            # Try different encodings
            encodings = ["utf-8", "utf-16", "latin-1", "cp1252"]

            for encoding in encodings:
                try:
                    return file_content.decode(encoding)
                except UnicodeDecodeError:
                    continue

            # If all encodings fail, use utf-8 with error handling
            return file_content.decode("utf-8", errors="ignore")

        except Exception as e:
            logger.error(
                f"[FileExtractionService] Error extracting text file: {str(e)}"
            )
            raise

    def extract_doc_text(self, file_content: bytes) -> str:
        """Extract text từ legacy DOC file (placeholder)"""
        # For now, return empty string as DOC extraction is complex
        logger.warning("[FileExtractionService] DOC extraction not fully implemented")
        return ""

    def is_supported_file_type(self, file_type: str) -> bool:
        """Check if file type is supported for text extraction"""
        return file_type in self.supported_types


# Create singleton instance
file_extraction_service = FileExtractionService()
