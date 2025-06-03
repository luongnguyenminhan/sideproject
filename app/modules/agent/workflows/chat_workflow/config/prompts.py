"""
System prompts và templates cho Chat Workflow
Vietnamese financial assistant prompts
"""

import time
import logging
from typing import Dict, Any, List, Optional

from ..utils.color_logger import get_color_logger, Colors

logger = logging.getLogger(__name__)
color_logger = get_color_logger(__name__)

# Initialize module
color_logger.info(
	f'📋 {Colors.BOLD}PROMPTS_INIT:{Colors.RESET}{Colors.BRIGHT_CYAN} Initializing prompts configuration module',
	Colors.BRIGHT_CYAN,
)


class SystemPrompts:
	"""Collection of system prompts cho different contexts"""

	DEFAULT_SYSTEM_PROMPT = """
    Bạn là MoneyEZ AI Assistant - trợ lý tài chính thông minh và thân thiện.
    
    Nhiệm vụ:
    • Hỗ trợ tư vấn tài chính cá nhân tại Việt Nam
    • Cung cấp thông tin về ngân hàng, đầu tư, tiết kiệm
    • Giải thích các khái niệm tài chính một cách dễ hiểu
    • Đưa ra lời khuyên phù hợp với luật pháp Việt Nam
    
    Nguyên tắc:
    • Luôn trả lời bằng tiếng Việt
    • Thông tin chính xác, cập nhật
    • Giải thích đơn giản, dễ hiểu  
    • Không đưa ra lời khuyên đầu tư cụ thể
    • Khuyến khích tham khảo chuyên gia khi cần
    • Tuân thủ quy định pháp luật Việt Nam
    """

	RAG_ENHANCED_TEMPLATE = """
    {base_prompt}
    
    === THÔNG TIN THAM KHẢO ===
    {context}
    
    Hướng dẫn sử dụng thông tin tham khảo:
    • Sử dụng thông tin trên để trả lời chính xác và chi tiết hơn
    • Kết hợp kiến thức có sẵn với thông tin được cung cấp
    • Nếu thông tin tham khảo không liên quan, bỏ qua và trả lời dựa trên kiến thức có sẵn
    • Luôn đảm bảo tính chính xác và phù hợp với bối cảnh Việt Nam
    """

	INVESTMENT_ADVISOR_PROMPT = """
    Bạn là chuyên gia tư vấn đầu tư tại Việt Nam với kinh nghiệm nhiều năm.
    
    Chuyên môn:
    • Phân tích thị trường chứng khoán Việt Nam
    • Tư vấn danh mục đầu tư phù hợp với từng cá nhân
    • Kiến thức về các sản phẩm đầu tư: cổ phiếu, trái phiếu, quỹ mở
    • Hiểu biết về quy định pháp luật đầu tư tại Việt Nam
    
    Lưu ý quan trọng:
    • KHÔNG đưa ra khuyến nghị đầu tư cụ thể vào cổ phiếu nào
    • Chỉ cung cấp thông tin giáo dục và hướng dẫn chung
    • Luôn nhắc nhở rủi ro đầu tư
    • Khuyến khích nghiên cứu kỹ trước khi đầu tư
    """

	BANKING_EXPERT_PROMPT = """
    Bạn là chuyên gia ngân hàng và tài chính cá nhân tại Việt Nam.
    
    Kiến thức chuyên sâu:
    • Các sản phẩm ngân hàng: tài khoản, thẻ tín dụng, khoản vay
    • Lãi suất và chính sách tiền tệ
    • Dịch vụ thanh toán số và fintech
    • Quy định của Ngân hàng Nhà nước Việt Nam
    
    Phong cách tư vấn:
    • Giải thích rõ ràng các điều khoản và điều kiện
    • So sánh khách quan các sản phẩm ngân hàng
    • Hướng dẫn cách sử dụng dịch vụ an toàn
    • Cảnh báo về các rủi ro và lừa đảo
    """

	INSURANCE_CONSULTANT_PROMPT = """
    Bạn là chuyên gia tư vấn bảo hiểm tại Việt Nam.
    
    Lĩnh vực chuyên môn:
    • Bảo hiểm nhân thọ và sức khỏe
    • Bảo hiểm tài sản và xe cộ  
    • Bảo hiểm xã hội và bảo hiểm y tế
    • Quy trình bồi thường và quyền lợi
    
    Nguyên tắc tư vấn:
    • Giải thích rõ ràng các loại hình bảo hiểm
    • Hướng dẫn cách chọn sản phẩm phù hợp
    • Cung cấp thông tin về quy trình khiếu nại
    • Luôn trung thực về ưu nhược điểm của từng sản phẩm
    """

	@classmethod
	def get_prompt_stats(cls) -> Dict[str, Any]:
		"""Get statistics about available system prompts"""
		start_time = time.time()
		color_logger.info(
			f'📊 {Colors.BOLD}PROMPT_STATS:{Colors.RESET}{Colors.BRIGHT_MAGENTA} Collecting prompt statistics',
			Colors.BRIGHT_MAGENTA,
		)

		prompts = {
			'default': cls.DEFAULT_SYSTEM_PROMPT,
			'rag_template': cls.RAG_ENHANCED_TEMPLATE,
			'investment': cls.INVESTMENT_ADVISOR_PROMPT,
			'banking': cls.BANKING_EXPERT_PROMPT,
			'insurance': cls.INSURANCE_CONSULTANT_PROMPT,
		}

		stats = {}
		for prompt_name, prompt_content in prompts.items():
			stats[prompt_name] = {
				'length': len(prompt_content),
				'lines': len(prompt_content.split('\n')),
				'words': len(prompt_content.split()),
			}

			color_logger.debug(
				f'Analyzed prompt: {prompt_name}',
				length=stats[prompt_name]['length'],
				lines=stats[prompt_name]['lines'],
				words=stats[prompt_name]['words'],
			)

		analysis_time = time.time() - start_time
		color_logger.performance_metric('prompt_analysis_time', f'{analysis_time:.3f}', 's')

		color_logger.success(
			'Prompt statistics collected',
			total_prompts=len(prompts),
			analysis_time=analysis_time,
		)

		return {
			'total_prompts': len(prompts),
			'prompt_details': stats,
			'analysis_time': analysis_time,
			'timestamp': time.time(),
		}


class PromptTemplates:
	"""Dynamic prompt templates cho different scenarios"""

	@staticmethod
	def get_rag_enhanced_prompt(base_prompt: str, context: str) -> str:
		"""Tạo enhanced prompt với RAG context"""
		start_time = time.time()
		color_logger.info(
			f'🧠 {Colors.BOLD}RAG_ENHANCE:{Colors.RESET}{Colors.BRIGHT_YELLOW} Creating RAG-enhanced prompt',
			Colors.BRIGHT_YELLOW,
			base_prompt_length=len(base_prompt),
			context_length=len(context),
		)

		if not base_prompt.strip():
			color_logger.warning('Empty base prompt provided', fallback_action='using_default')
			base_prompt = SystemPrompts.DEFAULT_SYSTEM_PROMPT

		if not context.strip():
			color_logger.warning('Empty context provided', fallback_action='using_base_prompt_only')
			return base_prompt

		enhanced_prompt = SystemPrompts.RAG_ENHANCED_TEMPLATE.format(base_prompt=base_prompt.strip(), context=context.strip())

		enhancement_time = time.time() - start_time
		color_logger.performance_metric('prompt_enhancement_time', f'{enhancement_time:.3f}', 's')

		color_logger.success(
			'RAG-enhanced prompt created',
			original_length=len(base_prompt),
			context_length=len(context),
			enhanced_length=len(enhanced_prompt),
			enhancement_ratio=f'{len(enhanced_prompt) / len(base_prompt):.2f}x',
		)

		return enhanced_prompt

	@staticmethod
	def get_context_specific_prompt(topic: str) -> str:
		"""Get specialized prompt based on topic"""
		start_time = time.time()
		color_logger.info(
			f'🎯 {Colors.BOLD}TOPIC_ANALYSIS:{Colors.RESET}{Colors.CYAN} Analyzing topic for prompt selection',
			Colors.CYAN,
			topic_length=len(topic),
			topic_preview=topic[:50] + '...' if len(topic) > 50 else topic,
		)

		topic_lower = topic.lower()

		# Investment-related topics
		investment_terms = [
			'đầu tư',
			'cổ phiếu',
			'chứng khoán',
			'quỹ',
			'trái phiếu',
			'portfolio',
			'fund',
		]
		investment_matches = [term for term in investment_terms if term in topic_lower]

		# Banking-related topics
		banking_terms = [
			'ngân hàng',
			'thẻ tín dụng',
			'vay',
			'lãi suất',
			'tài khoản',
			'atm',
			'internet banking',
		]
		banking_matches = [term for term in banking_terms if term in topic_lower]

		# Insurance-related topics
		insurance_terms = [
			'bảo hiểm',
			'bồi thường',
			'claim',
			'premium',
			'bảo hiểm y tế',
			'bảo hiểm nhân thọ',
		]
		insurance_matches = [term for term in insurance_terms if term in topic_lower]

		selected_prompt = None
		prompt_type = 'default'

		if investment_matches:
			selected_prompt = SystemPrompts.INVESTMENT_ADVISOR_PROMPT
			prompt_type = 'investment'
			color_logger.info(
				f'📈 {Colors.BOLD}INVESTMENT_TOPIC:{Colors.RESET}{Colors.GREEN} Investment topic detected',
				Colors.GREEN,
				matched_terms=investment_matches,
			)
		elif banking_matches:
			selected_prompt = SystemPrompts.BANKING_EXPERT_PROMPT
			prompt_type = 'banking'
			color_logger.info(
				f'🏦 {Colors.BOLD}BANKING_TOPIC:{Colors.RESET}{Colors.BLUE} Banking topic detected',
				Colors.BLUE,
				matched_terms=banking_matches,
			)
		elif insurance_matches:
			selected_prompt = SystemPrompts.INSURANCE_CONSULTANT_PROMPT
			prompt_type = 'insurance'
			color_logger.info(
				f'🛡️ {Colors.BOLD}INSURANCE_TOPIC:{Colors.RESET}{Colors.MAGENTA} Insurance topic detected',
				Colors.MAGENTA,
				matched_terms=insurance_matches,
			)
		else:
			selected_prompt = SystemPrompts.DEFAULT_SYSTEM_PROMPT
			color_logger.info(
				f'📝 {Colors.BOLD}DEFAULT_TOPIC:{Colors.RESET}{Colors.DIM} Using default prompt for general topic',
				Colors.DIM,
			)

		analysis_time = time.time() - start_time
		color_logger.performance_metric('topic_analysis_time', f'{analysis_time:.3f}', 's')

		color_logger.success(
			'Context-specific prompt selected',
			prompt_type=prompt_type,
			prompt_length=len(selected_prompt),
			analysis_time=analysis_time,
			topic_classification='automated',
		)

		return selected_prompt

	@staticmethod
	def format_documents(docs: list) -> str:
		"""Format retrieved documents cho prompt context"""
		start_time = time.time()
		color_logger.info(
			f'📄 {Colors.BOLD}DOC_FORMAT:{Colors.RESET}{Colors.BRIGHT_CYAN} Formatting documents for prompt context',
			Colors.BRIGHT_CYAN,
			doc_count=len(docs) if docs else 0,
		)

		if not docs:
			color_logger.warning('No documents provided for formatting', result='empty_context')
			return ''

		formatted_docs = []
		total_content_length = 0

		for i, doc in enumerate(docs):
			try:
				content = doc.page_content if hasattr(doc, 'page_content') else str(doc)
				source = doc.metadata.get('source', 'unknown') if hasattr(doc, 'metadata') else 'unknown'
				score = doc.metadata.get('similarity_score', 0) if hasattr(doc, 'metadata') else 0

				formatted_doc = f'Tài liệu {i + 1} (Nguồn: {source}, Độ tin cậy: {score:.2f}):\n{content}'
				formatted_docs.append(formatted_doc)
				total_content_length += len(content)

				color_logger.debug(
					f'Document {i + 1} formatted',
					content_length=len(content),
					source=source,
					score=score,
				)

			except Exception as e:
				color_logger.warning(
					f'Error formatting document {i + 1}: {str(e)}',
					doc_index=i,
					error_type=type(e).__name__,
				)
				continue

		formatted_result = '\n\n'.join(formatted_docs)
		formatting_time = time.time() - start_time

		color_logger.performance_metric('doc_formatting_time', f'{formatting_time:.3f}', 's')

		color_logger.success(
			'Documents formatted successfully',
			processed_docs=len(formatted_docs),
			total_content_length=total_content_length,
			final_length=len(formatted_result),
			formatting_time=formatting_time,
		)

		return formatted_result

	@staticmethod
	def create_error_fallback_prompt(error_context: str) -> str:
		"""Create fallback prompt when errors occur"""
		start_time = time.time()
		color_logger.info(
			f'🚨 {Colors.BOLD}ERROR_FALLBACK:{Colors.RESET}{Colors.BRIGHT_RED} Creating error fallback prompt',
			Colors.BRIGHT_RED,
			error_context_length=len(error_context),
		)

		# Sanitize error context for user display
		sanitized_context = error_context[:200] + '...' if len(error_context) > 200 else error_context

		fallback_prompt = f"""
        Tôi xin lỗi, đã xảy ra sự cố khi xử lý yêu cầu của bạn.
        
        Chi tiết lỗi: {sanitized_context}
        
        Vui lòng:
        • Thử lại với câu hỏi đơn giản hơn
        • Kiểm tra kết nối internet
        • Liên hệ hỗ trợ nếu vấn đề tiếp tục
        
        Tôi sẵn sàng hỗ trợ bạn với các câu hỏi tài chính khác.
        """

		creation_time = time.time() - start_time
		color_logger.performance_metric('fallback_creation_time', f'{creation_time:.3f}', 's')

		color_logger.success(
			'Error fallback prompt created',
			original_error_length=len(error_context),
			sanitized_length=len(sanitized_context),
			fallback_length=len(fallback_prompt),
			creation_time=creation_time,
		)

		return fallback_prompt

	@staticmethod
	def get_prompt_variations(base_topic: str, user_intent: str = 'general') -> List[str]:
		"""Generate prompt variations based on topic and intent"""
		start_time = time.time()
		color_logger.info(
			f'🔄 {Colors.BOLD}PROMPT_VARIATIONS:{Colors.RESET}{Colors.BRIGHT_MAGENTA} Generating prompt variations',
			Colors.BRIGHT_MAGENTA,
			base_topic=base_topic,
			user_intent=user_intent,
		)

		variations = []

		# Base prompt
		base_prompt = PromptTemplates.get_context_specific_prompt(base_topic)
		variations.append(base_prompt)

		# Intent-specific variations
		if user_intent == 'detailed':
			detailed_prompt = base_prompt + '\n\nVui lòng cung cấp thông tin chi tiết và ví dụ cụ thể.'
			variations.append(detailed_prompt)
			color_logger.debug('Added detailed variation')

		elif user_intent == 'simple':
			simple_prompt = base_prompt + '\n\nVui lòng giải thích một cách đơn giản, dễ hiểu cho người mới bắt đầu.'
			variations.append(simple_prompt)
			color_logger.debug('Added simple variation')

		elif user_intent == 'comparison':
			comparison_prompt = base_prompt + '\n\nVui lòng so sánh các lựa chọn và đưa ra ưu nhược điểm của từng phương án.'
			variations.append(comparison_prompt)
			color_logger.debug('Added comparison variation')

		generation_time = time.time() - start_time
		color_logger.performance_metric('variation_generation_time', f'{generation_time:.3f}', 's')

		color_logger.success(
			'Prompt variations generated',
			total_variations=len(variations),
			base_topic=base_topic,
			user_intent=user_intent,
			generation_time=generation_time,
		)

		return variations


class ValidationPrompts:
	"""Prompts cho validation và safety checks"""

	SAFETY_GUIDELINES = """
    Hướng dẫn an toàn khi tư vấn tài chính:
    
    1. KHÔNG BAO GIỜ:
       • Đưa ra khuyến nghị đầu tư cụ thể
       • Đảm bảo lợi nhuận hay tỷ suất sinh lời
       • Khuyến khích vay nợ quá mức khả năng
       • Cung cấp thông tin sai lệch về sản phẩm tài chính
    
    2. LUÔN LUÔN:
       • Cảnh báo về rủi ro đầu tư
       • Khuyến khích nghiên cứu kỹ lưỡng
       • Đề xuất tham khảo chuyên gia
       • Tuân thủ quy định pháp luật Việt Nam
    
    3. KHI KHÔNG CHẮC CHẮN:
       • Thừa nhận giới hạn kiến thức
       • Hướng dẫn tìm kiếm thông tin từ nguồn chính thức
       • Đề xuất liên hệ tổ chức tài chính uy tín
    """

	@staticmethod
	def validate_response_content(response: str) -> bool:
		"""Validate response cho compliance"""
		start_time = time.time()
		color_logger.info(
			f'🛡️ {Colors.BOLD}SAFETY_VALIDATION:{Colors.RESET}{Colors.YELLOW} Validating response for safety compliance',
			Colors.YELLOW,
			response_length=len(response),
		)

		# Check for prohibited content
		prohibited_phrases = [
			'đảm bảo lợi nhuận',
			'chắc chắn sinh lời',
			'không có rủi ro',
			'khuyến nghị mua',
			'nên bán ngay',
			'100% an toàn',
			'chắc chắn kiếm tiền',
		]

		response_lower = response.lower()
		violations = []

		for phrase in prohibited_phrases:
			if phrase in response_lower:
				violations.append(phrase)
				color_logger.warning(
					f'Safety violation detected',
					prohibited_phrase=phrase,
					violation_type='financial_advice',
				)

		validation_time = time.time() - start_time
		color_logger.performance_metric('safety_validation_time', f'{validation_time:.3f}', 's')

		is_valid = len(violations) == 0

		if is_valid:
			color_logger.success(
				'Response passed safety validation',
				validation_time=validation_time,
				prohibited_phrases_checked=len(prohibited_phrases),
				violations_found=0,
			)
		else:
			color_logger.error(
				f'Response failed safety validation',
				violations_count=len(violations),
				violations=violations,
				validation_time=validation_time,
			)

		return is_valid

	@staticmethod
	def get_safety_score(response: str) -> Dict[str, Any]:
		"""Get detailed safety analysis score"""
		start_time = time.time()
		color_logger.info(
			f'📊 {Colors.BOLD}SAFETY_ANALYSIS:{Colors.RESET}{Colors.BRIGHT_CYAN} Performing detailed safety analysis',
			Colors.BRIGHT_CYAN,
			response_length=len(response),
		)

		analysis = {
			'overall_score': 1.0,
			'violations': [],
			'warnings': [],
			'recommendations': [],
			'compliance_level': 'full',
		}

		response_lower = response.lower()

		# High-risk phrases (score reduction: 0.5)
		high_risk_phrases = ['đảm bảo lợi nhuận', 'chắc chắn sinh lời', '100% an toàn']
		# Medium-risk phrases (score reduction: 0.2)
		medium_risk_phrases = ['nên mua ngay', 'cơ hội hiếm có', 'không thể bỏ lỡ']
		# Low-risk phrases (score reduction: 0.1)
		low_risk_phrases = ['khả năng cao', 'rất có thể', 'thường thì']

		# Check high-risk violations
		for phrase in high_risk_phrases:
			if phrase in response_lower:
				analysis['violations'].append({'phrase': phrase, 'severity': 'high', 'score_reduction': 0.5})
				analysis['overall_score'] -= 0.5

		# Check medium-risk warnings
		for phrase in medium_risk_phrases:
			if phrase in response_lower:
				analysis['warnings'].append({'phrase': phrase, 'severity': 'medium', 'score_reduction': 0.2})
				analysis['overall_score'] -= 0.2

		# Check low-risk notices
		for phrase in low_risk_phrases:
			if phrase in response_lower:
				analysis['warnings'].append({'phrase': phrase, 'severity': 'low', 'score_reduction': 0.1})
				analysis['overall_score'] -= 0.1

		# Ensure score doesn't go below 0
		analysis['overall_score'] = max(0.0, analysis['overall_score'])

		# Determine compliance level
		if analysis['overall_score'] >= 0.9:
			analysis['compliance_level'] = 'full'
		elif analysis['overall_score'] >= 0.7:
			analysis['compliance_level'] = 'good'
		elif analysis['overall_score'] >= 0.5:
			analysis['compliance_level'] = 'acceptable'
		else:
			analysis['compliance_level'] = 'poor'

		# Generate recommendations
		if analysis['violations']:
			analysis['recommendations'].append('Loại bỏ các cụm từ đảm bảo lợi nhuận')
		if analysis['warnings']:
			analysis['recommendations'].append('Cân nhắc điều chỉnh ngôn từ để giảm tính khuyến khích đầu tư')
		if analysis['overall_score'] < 0.8:
			analysis['recommendations'].append('Thêm cảnh báo rủi ro và khuyến nghị tham khảo chuyên gia')

		analysis_time = time.time() - start_time
		color_logger.performance_metric('safety_analysis_time', f'{analysis_time:.3f}', 's')

		color_logger.success(
			'Safety analysis completed',
			overall_score=analysis['overall_score'],
			compliance_level=analysis['compliance_level'],
			violations_count=len(analysis['violations']),
			warnings_count=len(analysis['warnings']),
			analysis_time=analysis_time,
		)

		return analysis

	@staticmethod
	def get_compliance_report() -> Dict[str, Any]:
		"""Get compliance guidelines and statistics"""
		start_time = time.time()
		color_logger.info(
			f'📋 {Colors.BOLD}COMPLIANCE_REPORT:{Colors.RESET}{Colors.BRIGHT_WHITE} Generating compliance report',
			Colors.BRIGHT_WHITE,
		)

		report = {
			'guidelines_count': len(ValidationPrompts.SAFETY_GUIDELINES.split('\n')),
			'prohibited_phrases': [
				'đảm bảo lợi nhuận',
				'chắc chắn sinh lời',
				'không có rủi ro',
				'khuyến nghị mua',
				'nên bán ngay',
				'100% an toàn',
			],
			'required_disclosures': [
				'Cảnh báo rủi ro đầu tư',
				'Khuyến nghị tham khảo chuyên gia',
				'Tuân thủ quy định pháp luật Việt Nam',
			],
			'compliance_standards': {
				'financial_advice': 'Không đưa ra khuyến nghị đầu tư cụ thể',
				'risk_disclosure': 'Luôn cảnh báo về rủi ro',
				'legal_compliance': 'Tuân thủ quy định NHNN và SBV',
			},
		}

		report_time = time.time() - start_time
		color_logger.performance_metric('compliance_report_time', f'{report_time:.3f}', 's')

		color_logger.success(
			'Compliance report generated',
			guidelines_lines=report['guidelines_count'],
			prohibited_phrases=len(report['prohibited_phrases']),
			required_disclosures=len(report['required_disclosures']),
			report_time=report_time,
		)

		return report


# Module initialization complete
color_logger.success(
	'Prompts module initialized successfully',
	classes_loaded=['SystemPrompts', 'PromptTemplates', 'ValidationPrompts'],
	prompt_types=['default', 'investment', 'banking', 'insurance'],
	validation_enabled=True,
)

color_logger.info(
	f'✅ {Colors.BOLD}MODULE_READY:{Colors.RESET}{Colors.BRIGHT_GREEN} Prompts configuration module ready for use',
	Colors.BRIGHT_GREEN,
	total_classes=3,
	safety_validation=True,
	rag_enhancement=True,
)
