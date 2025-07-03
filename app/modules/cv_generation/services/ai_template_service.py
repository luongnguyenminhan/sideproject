from typing import Optional, Dict, Any
import os
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage
from app.modules.cv_extraction.schemas.cv import ProcessCVResponse, LLMTokenUsage
import json

logger = logging.getLogger(__name__)


class AITemplateService:
    """Service xử lý tạo LaTeX template sử dụng Google Gemini AI"""

    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0.3,
            google_api_key=os.getenv("GOOGLE_API_KEY"),
        )

    async def generate_html_template(
        self,
        cv_data: ProcessCVResponse,
        template_type: str = "modern",
        custom_prompt: Optional[str] = None,
        color_theme: str = "blue",
    ) -> Dict[str, Any]:
        """
        Tạo HTML template từ CV data

        Args:
            cv_data: Data CV từ extraction module
            template_type: Loại template (modern, classic, creative)
            custom_prompt: Custom prompt từ user
            color_theme: Màu theme

        Returns:
            Dict chứa html source và token usage
        """
        try:
            # Tạo system prompt
            system_prompt = self._create_system_prompt(template_type, color_theme)

            # Tạo human prompt với CV data
            human_prompt = self._create_human_prompt(cv_data, custom_prompt)

            # Gọi AI để tạo LaTeX
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt),
            ]

            response = await self.llm.ainvoke(messages)

            # Extract HTML source từ response
            html_source = self._extract_html_from_response(response.content)

            # Calculate token usage (approximate)
            token_usage = self._calculate_token_usage(
                system_prompt, human_prompt, response.content
            )

            return {
                "html_source": html_source,  # Changed from latex_source to html_source
                "token_usage": token_usage,
                "template_type": template_type,
                "color_theme": color_theme,
            }

        except Exception as e:
            raise Exception(f"Lỗi khi tạo HTML template: {str(e)}")

    def _create_system_prompt(self, template_type: str, color_theme: str) -> str:
        """Tạo system prompt cho AI"""
        base_prompt = f"""
Bạn là một chuyên gia thiết kế CV HTML chuyên nghiệp.

NHIỆM VỤ:
- Tạo HTML CV hoàn chỉnh với CSS embedded từ dữ liệu JSON được cung cấp
- Sử dụng style {template_type} với color theme {color_theme}
- Đảm bảo layout đẹp, responsive và print-friendly
- Tối ưu cho việc export thành PDF

YÊU CẦU TEMPLATE:
"""

        if template_type == "modern":
            base_prompt += """
- Layout 2 cột với sidebar bên trái
- Font: Google Fonts (Roboto, Inter, hoặc system fonts)
- Icon sử dụng Unicode symbols hoặc CSS shapes
- Màu accent theo color_theme
- Header với tên và contact info nổi bật
- Card-based sections với subtle shadows
- Responsive design cho mobile/tablet
"""
        elif template_type == "classic":
            base_prompt += """
- Layout 1 cột truyền thống, clean và minimal
- Font: Times New Roman, Georgia hoặc serif fonts
- Minimal design, chỉ dùng màu cho accent
- Section headers với simple underline
- Thông tin cá nhân ở đầu trang
- Traditional spacing và typography
"""
        elif template_type == "creative":
            base_prompt += """
- Layout sáng tạo với asymmetric design
- Sử dụng nhiều màu từ color_theme
- CSS shapes, gradients và visual elements
- Font: Google Fonts (Montserrat, Poppins)
- Progress bars cho skills (CSS-based)
- Creative use của flexbox/grid layout
"""

        base_prompt += f"""
COLOR SCHEME {color_theme.upper()}:
- Primary: {self._get_color_code(color_theme)}
- Secondary: {self._get_secondary_color(color_theme)}
- Text: #2C3E50 (dark gray)
- Background: #FFFFFF (white)
- Accent: Primary color cho highlights

CSS REQUIREMENTS:
- Embedded CSS trong <style> tag
- Print-friendly styles (@media print)
- Responsive design (@media screen)
- Web-safe fonts với fallbacks
- A4 page size optimization
- No external dependencies

OUTPUT FORMAT:
- Chỉ trả về HTML code hoàn chỉnh
- Bắt đầu với <!DOCTYPE html>
- Kết thúc với </html>
- CSS embedded trong <style> tag ở <head>
- Không giải thích, không markdown wrapper
- Sẵn sàng cho weasyprint PDF export
"""
        return base_prompt

    def _create_human_prompt(
        self, cv_data: ProcessCVResponse, custom_prompt: Optional[str] = None
    ) -> str:
        """Tạo human prompt với CV data"""
        prompt = "Tạo CV LaTeX từ dữ liệu sau:\n\n"

        # Convert CV data to structured format
        cv_info = {}

        if cv_data.cv_analysis_result:
            analysis = cv_data.cv_analysis_result

            # Personal Information
            if analysis.personal_information:
                cv_info["personal_info"] = {
                    "name": analysis.personal_information.full_name,
                    "email": analysis.personal_information.email,
                    "phone": analysis.personal_information.phone_number,
                    "linkedin": analysis.personal_information.linkedin_url,
                    "github": analysis.personal_information.github_url,
                    "address": analysis.personal_information.address,
                }

            # Work Experience
            if analysis.work_experience_history:
                cv_info["experience"] = []
                for exp in analysis.work_experience_history.items:
                    cv_info["experience"].append(
                        {
                            "company": exp.company_name,
                            "position": exp.job_title,
                            "start_date": exp.start_date,
                            "end_date": exp.end_date,
                            "responsibilities": exp.responsibilities_achievements,
                            "location": exp.location,
                        }
                    )

            # Education
            if analysis.education_history:
                cv_info["education"] = []
                for edu in analysis.education_history.items:
                    cv_info["education"].append(
                        {
                            "institution": edu.institution_name,
                            "degree": edu.degree_name,
                            "major": edu.major,
                            "graduation_date": edu.graduation_date,
                            "gpa": edu.gpa,
                        }
                    )

            # Skills
            if analysis.skills_summary:
                cv_info["skills"] = []
                for skill in analysis.skills_summary.items:
                    cv_info["skills"].append(
                        {
                            "name": skill.skill_name,
                            "level": skill.proficiency_level,
                            "category": skill.category,
                        }
                    )

            # Projects
            if analysis.projects:
                cv_info["projects"] = []
                for project in analysis.projects.items:
                    cv_info["projects"].append(
                        {
                            "name": project.project_name,
                            "description": project.description,
                            "technologies": project.technologies_used,
                            "url": project.project_url,
                        }
                    )

            # Certificates
            if analysis.certificates_and_courses:
                cv_info["certificates"] = []
                for cert in analysis.certificates_and_courses.items:
                    cv_info["certificates"].append(
                        {
                            "name": cert.certificate_name,
                            "organization": cert.issuing_organization,
                            "date": cert.issue_date,
                        }
                    )

            # Summary
            if analysis.cv_summary:
                cv_info["summary"] = analysis.cv_summary

        prompt += json.dumps(cv_info, indent=2, ensure_ascii=False)

        if custom_prompt:
            prompt += f"\n\nYêu cầu đặc biệt:\n{custom_prompt}"

        prompt += "\n\nTạo HTML CV hoàn chỉnh với embedded CSS cho dữ liệu này."

        return prompt

    def _extract_html_from_response(self, response_content: str) -> str:
        """Extract HTML code từ AI response với encoding safety"""
        try:
            # Ensure proper string type and encoding
            if isinstance(response_content, bytes):
                try:
                    response_content = response_content.decode("utf-8")
                except UnicodeDecodeError:
                    # Try other encodings
                    for encoding in ["latin1", "cp1252", "iso-8859-1"]:
                        try:
                            response_content = response_content.decode(encoding)
                            break
                        except UnicodeDecodeError:
                            continue
                    else:
                        # Fallback: decode with error replacement
                        response_content = response_content.decode(
                            "utf-8", errors="replace"
                        )

            # Tìm và extract HTML code từ response
            content = response_content.strip()

            # Nếu có ```html wrapper, extract nội dung
            if "```html" in content:
                start = content.find("```html") + 7
                end = content.find("```", start)
                content = content[start:end].strip()
            elif "```" in content:
                start = content.find("```") + 3
                end = content.find("```", start)
                content = content[start:end].strip()

            # Đảm bảo có <!DOCTYPE html> ở đầu
            if not content.startswith("<!DOCTYPE html>") and not content.startswith(
                "<html"
            ):
                # Tìm vị trí <!DOCTYPE hoặc <html
                doc_start = content.find("<!DOCTYPE")
                if doc_start == -1:
                    doc_start = content.find("<html")
                if doc_start != -1:
                    content = content[doc_start:]
                else:
                    # Add basic HTML structure if missing
                    if "<body>" in content:
                        content = f"<!DOCTYPE html>\n<html>\n<head><meta charset='UTF-8'></head>\n{content}\n</html>"

            # Ensure the content is clean UTF-8
            try:
                content.encode("utf-8")
            except UnicodeEncodeError:
                # Clean problematic characters
                content = content.encode("utf-8", errors="ignore").decode("utf-8")

            return content

        except Exception as e:
            logger.error(f"❌ Error extracting HTML from AI response: {e}")
            # Return a minimal working HTML document as fallback
            return """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>CV Error</title>
</head>
<body>
    <h1>Error extracting HTML content</h1>
    <p>There was an error processing the CV content.</p>
</body>
</html>"""

    def _calculate_token_usage(
        self, system_prompt: str, human_prompt: str, response: str
    ) -> LLMTokenUsage:
        """Calculate approximate token usage"""
        # Rough calculation: 1 token ≈ 4 characters
        input_tokens = len(system_prompt + human_prompt) // 4
        output_tokens = len(response) // 4
        total_tokens = input_tokens + output_tokens

        # Approximate cost for Gemini (very rough)
        price_usd = total_tokens * 0.0000015  # Approximate pricing

        return LLMTokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            price_usd=price_usd,
        )

    def _get_color_code(self, color_theme: str) -> str:
        """Get color code cho theme"""
        color_map = {
            "blue": "#3498DB",
            "green": "#27AE60",
            "red": "#E74C3C",
            "purple": "#9B59B6",
            "orange": "#F39C12",
            "teal": "#1ABC9C",
            "black": "#2C3E50",
        }
        return color_map.get(color_theme, "#3498DB")

    def _get_secondary_color(self, color_theme: str) -> str:
        """Get secondary color cho theme"""
        secondary_map = {
            "blue": "#2980B9",
            "green": "#229954",
            "red": "#C0392B",
            "purple": "#8E44AD",
            "orange": "#E67E22",
            "teal": "#16A085",
            "black": "#34495E",
        }
        return secondary_map.get(color_theme, "#2980B9")
