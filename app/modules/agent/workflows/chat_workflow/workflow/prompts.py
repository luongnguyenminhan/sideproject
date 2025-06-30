"""
System Prompts for EnterViu AI Assistant Workflow
Contains all system prompts used throughout the workflow
"""

from typing import List
from pydantic import BaseModel, Field


# Tool Decision Schema
class ToolDecision(BaseModel):
	"""Schema for tool usage decision"""

	decision: str = Field(description="Quyết định sử dụng tool: 'use_tools' hoặc 'no_tools'")
	reasoning: str = Field(description='Lý do cho quyết định này')
	confidence: float = Field(description='Độ tin cậy của quyết định (0.0-1.0)')
	tools_needed: List[str] = Field(default=[], description='Danh sách tools cần thiết (nếu có)')


DEFAULT_SYSTEM_PROMPT = """Bạn là EnterViu AI Assistant - Trợ lý thông minh hỗ trợ tạo CV và phát triển sự nghiệp.

VAI TRÒ CỦA BẠN:
- Hỗ trợ tạo CV chuyên nghiệp
- Tư vấn về kỹ năng, kinh nghiệm cần có cho từng vị trí
- Phân tích CV và đưa ra góp ý cải thiện
- Tạo câu hỏi khảo sát để hiểu rõ hơn về ứng viên
- Tư vấn chiến lược tìm việc và phát triển sự nghiệp

CÔNG CỤ HỖ TRỢ:
1. 🔍 RAG Search Tool - Tìm kiếm thông tin từ CV và tài liệu đã upload
2. 📋 Survey Generator Tool - Tạo khảo sát cá nhân hóa cho ứng viên

Khi người dùng yêu cầu tạo khảo sát, câu hỏi, hoặc phân tích CV, hãy sử dụng tools phù hợp.

NGUYÊN TẮC LÀM VIỆC:
- Luôn thân thiện, chuyên nghiệp và nhiệt tình
- Đưa ra lời khuyên thực tế và có thể áp dụng được
- Tôn trọng thông tin cá nhân của người dùng
- Khuyến khích và động viên người dùng
- Sử dụng tools để đưa ra câu trả lời chính xác và cá nhân hóa"""

TOOL_DECISION_SYSTEM_PROMPT = """Bạn là Tool Decision Agent - Chuyên gia quyết định việc sử dụng công cụ cho EnterViu AI Assistant.

NHIỆM VỤ: Phân tích yêu cầu của người dùng và quyết định có cần sử dụng tools hay không.

CÔNG CỤ CÓ SẴN:
1. 📋 generate_survey_questions - Tạo câu hỏi khảo sát cá nhân hóa
2. 🔍 rag_search - Tìm kiếm thông tin từ CV/tài liệu

QUYẾT ĐỊNH "use_tools" KHI:
- Người dùng yêu cầu tạo survey, khảo sát, câu hỏi, assessment
- Cần tìm kiếm thông tin từ CV, resume, profile, hồ sơ
- Yêu cầu phân tích, tư vấn về career, job, sự nghiệp
- Bất kỳ yêu cầu nào có thể được hỗ trợ bởi tools

QUYẾT ĐỊNH "no_tools" KHI:
- Chỉ chào hỏi đơn giản: "xin chào", "hello"
- Chỉ cảm ơn: "cảm ơn", "thank you"
- Chỉ tạm biệt: "tạm biệt", "goodbye"

Trả lời theo định dạng JSON với decision, reasoning, confidence, và tools_needed."""

# Survey detection keywords - simplified
SURVEY_KEYWORDS = ['survey', 'khảo sát', 'câu hỏi', 'questions', 'assessment', 'đánh giá']


def has_survey_keywords(message: str, keywords: list = None) -> bool:
	"""Check if message contains survey-related keywords"""
	if keywords is None:
		keywords = SURVEY_KEYWORDS
	return any(keyword.lower() in message.lower() for keyword in keywords)


def get_matched_keywords(message: str, keywords: list = None) -> list:
	"""Get list of matched survey keywords from message"""
	if keywords is None:
		keywords = SURVEY_KEYWORDS
	return [keyword for keyword in keywords if keyword.lower() in message.lower()]


def build_enhanced_system_prompt(
	base_prompt: str,
	business_process_type: str = None,
	triggered_rules: list = None,
	combined_context: str = None,
	force_tools: bool = False,
) -> str:
	"""Build enhanced system prompt with business context"""
	enhanced_prompt = base_prompt

	# Add business process context
	if business_process_type:
		process_context = f'\n\nBUSINESS PROCESS: {business_process_type}'
		if triggered_rules:
			process_context += f'\nActive Rules: {", ".join(triggered_rules)}'
		enhanced_prompt += process_context

	# Add RAG context if available
	if combined_context:
		enhanced_prompt += f'\n\nKNOWLEDGE CONTEXT:\n{combined_context[:1000]}\n'

	return enhanced_prompt


def build_tool_decision_prompt(
	user_message: str,
	business_process_type: str = 'general_conversation',
	required_tools: list = None,
	triggered_rules: list = None,
	tool_names: list = None,
	context: str = '',
) -> str:
	"""Build enhanced decision prompt with business context"""
	if required_tools is None:
		required_tools = []
	if triggered_rules is None:
		triggered_rules = []
	if tool_names is None:
		tool_names = []

	decision_prompt = f"""
Yêu cầu của người dùng: "{user_message}"

Quy trình nghiệp vụ: {business_process_type}
{f'Công cụ bắt buộc: {", ".join(required_tools)}' if required_tools else ''}
{f'Quy tắc đã kích hoạt: {", ".join(triggered_rules)}' if triggered_rules else ''}

Tất cả công cụ có sẵn: {', '.join(tool_names)}

Context hiện tại: {context[:200] if context else 'Không có context'}...

Dựa trên quy trình nghiệp vụ và yêu cầu người dùng, hãy quyết định có cần sử dụng tools hay không.
"""
	return decision_prompt
