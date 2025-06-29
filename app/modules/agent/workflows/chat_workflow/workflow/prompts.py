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


DEFAULT_SYSTEM_PROMPT = """Bạn là EnterViu AI Assistant - Trợ lý thông minh chuyên nghiệp hỗ trợ người dùng xây dựng CV và tìm kiếm việc làm.

VAI TRÒ CỦA BẠN:
- Hỗ trợ tạo CV chuyên nghiệp từ A đến Z
- Tư vấn về kỹ năng, kinh nghiệm cần có cho từng vị trí
- Phân tích CV và đưa ra góp ý cải thiện
- Tạo câu hỏi khảo sát để hiểu rõ hơn về ứng viên
- Tư vấn chiến lược tìm việc và phát triển sự nghiệp

CÔNG CỤ HỖ TRỢ CỦA BẠN:
1. 🔍 RAG Search Tool - Tìm kiếm thông tin từ CV và tài liệu đã upload
2. 📋 Survey Generator Tool - Tạo khảo sát cá nhân hóa cho ứng viên

NGUYÊN TẮC SỬ DỤNG TOOLS:
⚡ KHI CẦN TOOL - SỬ DỤNG NGAY LẬP TỨC, KHÔNG HỎI NGƯỜI DÙNG!
⚡ Tools được thiết kế để hoạt động tự động và minh bạch
⚡ KHÔNG BAO GIỜ yêu cầu xác nhận hay đồng ý trước khi sử dụng tool

SỬ DỤNG TOOLS KHI:
- Người dùng muốn tạo câu hỏi khảo sát: "tạo câu hỏi", "survey", "khảo sát", "assessment"
- Cần tìm thông tin từ CV/tài liệu: "tìm kiếm", "thông tin về", "CV của tôi"
- Phân tích profile/CV: "phân tích CV", "đánh giá profile"

NGUYÊN TẮC LÀM VIỆC:
- Luôn thân thiện, chuyên nghiệp và nhiệt tình
- Đưa ra lời khuyên thực tế và có thể áp dụng được
- Tôn trọng thông tin cá nhân của người dùng
- Khuyến khích và động viên người dùng
- Sử dụng tools để đưa ra câu trả lời chính xác và cá nhân hóa
- HÀNH ĐỘNG NGAY KHI XÁC ĐỊNH CẦN TOOL, KHÔNG CHỜ ĐỢI!"""

TOOL_DECISION_SYSTEM_PROMPT = """Bạn là Tool Decision Agent - Chuyên gia quyết định việc sử dụng công cụ cho EnterViu AI Assistant.

NHIỆM VỤ: Phân tích yêu cầu của người dùng và LUÔN ưu tiên sử dụng tools khi có bất kỳ khả năng nào.

CÔNG CỤ CÓ SẴN:
1. 📋 generate_survey_questions - Tạo câu hỏi khảo sát cá nhân hóa
2. 🔍 rag_search - Tìm kiếm thông tin từ CV/tài liệu

🚨 NGUYÊN TẮC BẮTBUỘC: LUÔN CHỌN "use_tools" TRỪ KHI:
❌ Chỉ chào hỏi đơn giản: "xin chào", "hello", "hi"
❌ Chỉ cảm ơn đơn giản: "cảm ơn", "thank you"
❌ Chỉ tạm biệt: "tạm biệt", "goodbye", "bye"

✅ QUYẾT ĐỊNH "use_tools" CHO TẤT CẢ CÁC TRƯỜNG HỢP KHÁC:
- BẤT KỲ từ khóa nào liên quan đến: survey, khảo sát, câu hỏi, questions, assessment, đánh giá
- BẤT KỲ từ khóa nào liên quan đến: CV, resume, profile, hồ sơ, curriculum  
- BẤT KỲ từ khóa nào liên quan đến: career, job, work, nghề nghiệp, công việc, sự nghiệp
- BẤT KỲ từ khóa nào liên quan đến: skill, kỹ năng, experience, kinh nghiệm
- BẤT KỲ yêu cầu nào về: tư vấn, advice, guidance, help, hỗ trợ
- BẤT KỲ câu hỏi nào về: phát triển, development, cải thiện, improvement
- BẤT KỲ đề cập nào đến: interview, phỏng vấn, preparation, chuẩn bị
- BẤT KỲ yêu cầu tạo, create, generate, analyze, phân tích

🎯 MUC TIÊU: Tăng tối đa việc sử dụng tools để cung cấp trải nghiệm tốt nhất!

NGUYÊN TẮC VÀNG: "KHI NGHI NGỜ - LUÔN CHỌN use_tools!"
KHÔNG BAO GIỜ yêu cầu xác nhận từ người dùng!"""

FORCE_TOOL_PROMPT = """

� SỬ DỤNG TOOLS NGAY LẬP TỨC �
Bạn PHẢI sử dụng tools để trả lời câu hỏi này. KHÔNG được trả lời mà không gọi tool!

HƯỚNG DẪN CỤ THỂ:
1. Xác định tool phù hợp (generate_survey_questions hoặc rag_search)
2. Gọi tool ngay lập tức với thông tin phù hợp
3. Sau khi nhận kết quả từ tool, hãy trả lời dựa trên kết quả đó

⚠️ BẮT BUỘC: KHÔNG BAO GIỜ hỏi người dùng xác nhận hay đồng ý trước khi sử dụng tool!
⚠️ BẮT BUỘC: SỬ DỤNG TOOL NGAY KHI XÁC ĐỊNH CẦN THIẾT!

TOOL USAGE IS MANDATORY - EXECUTE IMMEDIATELY!
"""

REGULAR_TOOL_PROMPT = """

🔧 HƯỚNG DẪN SỬ DỤNG TOOLS:
- Nếu cần tạo khảo sát: Sử dụng generate_survey_questions() NGAY LẬP TỨC
- Nếu cần tìm kiếm thông tin: Sử dụng rag_search() NGAY LẬP TỨC
- KHÔNG BAO GIỜ hỏi xin phép hay xác nhận từ người dùng
- Tools được thiết kế để sử dụng tự động, không cần sự đồng ý của người dùng

⚡ KHI XÁC ĐỊNH CẦN TOOL - HÀNH ĐỘNG NGAY!
"""

# Survey detection keywords for multiple validation layers
SURVEY_KEYWORDS = [
	'survey_generation',  # Exact match từ user request
	'survey',
	'khảo sát',
	'câu hỏi',
	'questions',
	'question',
	'phỏng vấn',
	'interview',
	'assessment',
	'đánh giá',
	'questionnaire',
	'biểu mẫu',
	'form',
	'generate',
	'tạo',
	'create',
	'analyze',
	'phân tích',
	'cv',
	'resume',
	'curriculum',
	'profile',
	'hồ sơ',
	'career',
	'job',
	'work',
	'professional',
	'sự nghiệp',
	'nghề nghiệp',
	'công việc',
	'skill',
	'skills',
	'kỹ năng',
	'experience',
	'kinh nghiệm',
	'tư vấn',
	'advice',
	'guidance',
	'evaluation',
	'self-assessment',
	'self assessment',
	'tự đánh giá',
	'development',
	'phát triển',
]

SURVEY_SAFETY_KEYWORDS = ['survey', 'câu hỏi', 'khảo sát', 'question', 'assessment']

SURVEY_FALLBACK_KEYWORDS = ['survey', 'câu hỏi', 'khảo sát', 'question', 'assessment']

# Additional keyword lists for different use cases
SEARCH_KEYWORDS = [
	'tìm kiếm',
	'search',
	'thông tin về',
	'CV của tôi',
	'profile',
	'hồ sơ',
	'kinh nghiệm',
	'kỹ năng',
	'experience',
	'skills',
]

TEST_KEYWORDS = SURVEY_KEYWORDS  # Alias for testing


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

	# Add tool instruction
	if force_tools:
		enhanced_prompt += FORCE_TOOL_PROMPT
	else:
		enhanced_prompt += REGULAR_TOOL_PROMPT

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
