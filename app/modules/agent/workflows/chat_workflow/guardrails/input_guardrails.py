"""
Input Guardrail Rules cho Chat Workflow
Kiểm tra và xử lý đầu vào từ user
"""

import re
from typing import Dict, List, Any
from .core import (
	BaseGuardrail,
	GuardrailResult,
	GuardrailViolation,
	GuardrailSeverity,
	GuardrailAction,
)
from datetime import datetime


class ProfanityGuardrail(BaseGuardrail):
	"""Kiểm tra từ ngữ không phù hợp"""

	def __init__(self):
		super().__init__('profanity_filter', True, GuardrailSeverity.HIGH)

		# Danh sách từ cấm (có thể mở rộng)
		self.banned_words = {
			# Tiếng Việt
			'đụ',
			'địt',
			'lồn',
			'cặc',
			'đéo',
			'đm',
			'vcl',
			'vkl',
			'clgt',
			'đcm',
			'shit',
			'fuck',
			'damn',
			'bitch',
			'asshole',
			'motherfucker',
			# Có thể thêm nhiều hơn
		}

		# Từ thay thế
		self.replacements = {
			'đụ': '***',
			'địt': '***',
			'lồn': '***',
			'cặc': '***',
			'đéo': '***',
			'đm': '***',
			'vcl': '***',
			'vkl': '***',
			'shit': '***',
			'fuck': '***',
			'damn': '***',
			'bitch': '***',
		}

	def check(self, content: str, context: Dict[str, Any] = None) -> GuardrailResult:
		violations = []
		modified_content = content.lower()
		found_profanity = []

		for word in self.banned_words:
			if word in modified_content:
				found_profanity.append(word)
				modified_content = modified_content.replace(word, self.replacements.get(word, '***'))

		if found_profanity:
			violation = GuardrailViolation(
				rule_name=self.name,
				severity=self.severity,
				action=GuardrailAction.MODIFY,
				message=f'Phát hiện từ ngữ không phù hợp: {", ".join(found_profanity)}',
				details={'banned_words_found': found_profanity},
				timestamp=datetime.now(),
			)
			violations.append(violation)

			return GuardrailResult(
				passed=True,  # Vẫn cho phép nhưng đã sửa đổi
				violations=violations,
				modified_content=modified_content,
			)

		return GuardrailResult(passed=True, violations=[])


class SpamGuardrail(BaseGuardrail):
	"""Kiểm tra spam và repetitive content"""

	def __init__(self):
		super().__init__('spam_filter', True, GuardrailSeverity.MEDIUM)
		self.max_repeated_chars = 5
		self.max_repeated_words = 3

	def check(self, content: str, context: Dict[str, Any] = None) -> GuardrailResult:
		violations = []

		# Kiểm tra ký tự lặp lại
		repeated_char_pattern = r'(.)\1{' + str(self.max_repeated_chars) + ',}'
		if re.search(repeated_char_pattern, content):
			violation = GuardrailViolation(
				rule_name=self.name,
				severity=self.severity,
				action=GuardrailAction.MODIFY,
				message=f'Phát hiện ký tự lặp lại quá {self.max_repeated_chars} lần',
				details={'repeated_chars': True},
				timestamp=datetime.now(),
			)
			violations.append(violation)

			# Sửa đổi content
			modified_content = re.sub(repeated_char_pattern, r'\1\1\1', content)

			return GuardrailResult(passed=True, violations=violations, modified_content=modified_content)

		# Kiểm tra từ lặp lại
		words = content.split()
		if len(words) > 0:
			word_count = {}
			for word in words:
				word_lower = word.lower()
				word_count[word_lower] = word_count.get(word_lower, 0) + 1

			repeated_words = {word: count for word, count in word_count.items() if count > self.max_repeated_words}

			if repeated_words:
				violation = GuardrailViolation(
					rule_name=self.name,
					severity=self.severity,
					action=GuardrailAction.ALLOW,  # Chỉ cảnh báo
					message=f'Phát hiện từ lặp lại: {repeated_words}',
					details={'repeated_words': repeated_words},
					timestamp=datetime.now(),
				)
				violations.append(violation)

		return GuardrailResult(passed=True, violations=violations)


class LengthGuardrail(BaseGuardrail):
	"""Kiểm tra độ dài input"""

	def __init__(self, max_length: int = 5000):
		super().__init__('length_filter', True, GuardrailSeverity.MEDIUM)
		self.max_length = max_length

	def check(self, content: str, context: Dict[str, Any] = None) -> GuardrailResult:
		if len(content) > self.max_length:
			violation = GuardrailViolation(
				rule_name=self.name,
				severity=self.severity,
				action=GuardrailAction.BLOCK,
				message=f'Input quá dài ({len(content)} > {self.max_length} ký tự)',
				details={'content_length': len(content), 'max_length': self.max_length},
				timestamp=datetime.now(),
			)

			return GuardrailResult(passed=False, violations=[violation])

		return GuardrailResult(passed=True, violations=[])


class PersonalInfoGuardrail(BaseGuardrail):
	"""Kiểm tra thông tin cá nhân nhạy cảm"""

	def __init__(self):
		super().__init__('personal_info_filter', True, GuardrailSeverity.HIGH)

		# Patterns để detect thông tin cá nhân
		self.patterns = {
			'phone': r'\b(?:\+84|0)(?:[1-9]\d{8,9})\b',
			'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
			'id_card': r'\b\d{9}(?:\d{3})?\b',  # CMND/CCCD Vietnam
			'credit_card': r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
		}

	def check(self, content: str, context: Dict[str, Any] = None) -> GuardrailResult:
		violations = []
		found_info = {}

		for info_type, pattern in self.patterns.items():
			matches = re.findall(pattern, content)
			if matches:
				found_info[info_type] = matches

		if found_info:
			violation = GuardrailViolation(
				rule_name=self.name,
				severity=self.severity,
				action=GuardrailAction.ALLOW,  # Cảnh báo nhưng cho phép
				message=f'Phát hiện thông tin cá nhân: {list(found_info.keys())}',
				details={'personal_info_types': list(found_info.keys())},
				timestamp=datetime.now(),
			)
			violations.append(violation)

		return GuardrailResult(passed=True, violations=violations)


class InjectionGuardrail(BaseGuardrail):
	"""Kiểm tra prompt injection attacks"""

	def __init__(self):
		super().__init__('injection_filter', True, GuardrailSeverity.CRITICAL)

		# Patterns nguy hiểm
		self.dangerous_patterns = [
			r'ignore\s+previous\s+instructions?',
			r'forget\s+everything',
			r'you\s+are\s+now',
			r'act\s+as\s+if',
			r'pretend\s+to\s+be',
			r'system\s*:',
			r'<\s*script',
			r'javascript\s*:',
			r'eval\s*\(',
			r'exec\s*\(',
		]

	def check(self, content: str, context: Dict[str, Any] = None) -> GuardrailResult:
		violations = []
		content_lower = content.lower()

		for pattern in self.dangerous_patterns:
			if re.search(pattern, content_lower, re.IGNORECASE):
				violation = GuardrailViolation(
					rule_name=self.name,
					severity=self.severity,
					action=GuardrailAction.BLOCK,
					message=f'Phát hiện khả năng prompt injection: {pattern}',
					details={'detected_pattern': pattern},
					timestamp=datetime.now(),
				)
				violations.append(violation)

				return GuardrailResult(passed=False, violations=violations)

		return GuardrailResult(passed=True, violations=[])


class EnterViuContextGuardrail(BaseGuardrail):
	"""Guardrail đặc biệt cho context EnterViu"""

	def __init__(self):
		super().__init__('enterviu_context_filter', True, GuardrailSeverity.LOW)

		# Keywords liên quan đến competitors hoặc nội dung không phù hợp với EnterViu
		self.off_topic_keywords = [
			'competitor_brand_1',
			'competitor_brand_2',  # Thay bằng tên thực
			'hate_speech',
			'discrimination',
		]

	def check(self, content: str, context: Dict[str, Any] = None) -> GuardrailResult:
		violations = []
		content_lower = content.lower()

		found_keywords = [kw for kw in self.off_topic_keywords if kw in content_lower]

		if found_keywords:
			violation = GuardrailViolation(
				rule_name=self.name,
				severity=self.severity,
				action=GuardrailAction.ALLOW,  # Chỉ log, không block
				message=f'Nội dung có thể không phù hợp với EnterViu context',
				details={'keywords_found': found_keywords},
				timestamp=datetime.now(),
			)
			violations.append(violation)

		return GuardrailResult(passed=True, violations=violations)
