"""
Output Guardrail Rules cho Chat Workflow
Kiểm tra và xử lý đầu ra từ AI
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


class HallucinationGuardrail(BaseGuardrail):
	"""Kiểm tra hallucination trong AI response"""

	def __init__(self):
		super().__init__('hallucination_filter', True, GuardrailSeverity.HIGH)

		# Patterns cho các dấu hiệu hallucination
		self.uncertainty_phrases = [
			'tôi không chắc chắn',
			'có thể là',
			'theo như tôi biết',
			'tôi nghĩ rằng',
			'có lẽ',
			'không rõ',
			'tôi không có thông tin chính xác',
		]

		# Patterns cần cảnh báo
		self.suspicious_patterns = [
			r'theo nghiên cứu năm \d{4}',  # Tránh cite nghiên cứu không rõ nguồn
			r'chuyên gia .+ khuyên',  # Tránh quote expert không rõ
			r'\d+% người dùng',  # Tránh statistics không có nguồn
		]

	def check(self, content: str, context: Dict[str, Any] = None) -> GuardrailResult:
		violations = []
		content_lower = content.lower()

		# Kiểm tra uncertainty phrases (điều tốt)
		uncertainty_count = sum(1 for phrase in self.uncertainty_phrases if phrase in content_lower)

		# Kiểm tra suspicious patterns
		suspicious_findings = []
		for pattern in self.suspicious_patterns:
			matches = re.findall(pattern, content_lower)
			if matches:
				suspicious_findings.extend(matches)

		if suspicious_findings:
			violation = GuardrailViolation(
				rule_name=self.name,
				severity=self.severity,
				action=GuardrailAction.ALLOW,  # Cảnh báo nhưng cho phép
				message=f'Phát hiện khả năng hallucination: {len(suspicious_findings)} patterns',
				details={
					'suspicious_patterns': suspicious_findings,
					'uncertainty_count': uncertainty_count,
					'confidence_score': max(0, 1 - len(suspicious_findings) * 0.2),
				},
				timestamp=datetime.now(),
				confidence=max(0.3, 1 - len(suspicious_findings) * 0.1),
			)
			violations.append(violation)

		return GuardrailResult(passed=True, violations=violations)


class FactualityGuardrail(BaseGuardrail):
	"""Kiểm tra tính factual của response"""

	def __init__(self):
		super().__init__('factuality_filter', True, GuardrailSeverity.MEDIUM)

		# EnterViu facts để cross-check
		self.enterviu_facts = {
			'founding_date': '2024',
			'purpose': 'Career development and job matching platform',
			'services': ['Profile building', 'Job search', 'Employer matching', 'Career guidance'],
			'platform_type': 'Professional career platform',
		}

	def check(self, content: str, context: Dict[str, Any] = None) -> GuardrailResult:
		violations = []

		# Kiểm tra facts về EnterViu
		factual_issues = []

		# Check platform purpose
		if 'enterviu' in content.lower():
			if 'career' not in content.lower() and 'job' not in content.lower():
				factual_issues.append('Mục đích của EnterViu không được mô tả chính xác')

		# Check services
		if 'dịch vụ' in content.lower() or 'tính năng' in content.lower():
			service_keywords = ['profile', 'job', 'career', 'việc làm', 'cv']
			if not any(keyword in content.lower() for keyword in service_keywords):
				factual_issues.append('Các dịch vụ EnterViu không chính xác')

		if factual_issues:
			violation = GuardrailViolation(
				rule_name=self.name,
				severity=self.severity,
				action=GuardrailAction.ALLOW,
				message=f'Phát hiện khả năng thông tin không chính xác về EnterViu',
				details={'factual_issues': factual_issues},
				timestamp=datetime.now(),
			)
			violations.append(violation)

		return GuardrailResult(passed=True, violations=violations)


class ToxicityGuardrail(BaseGuardrail):
	"""Kiểm tra nội dung độc hại trong AI response"""

	def __init__(self):
		super().__init__('toxicity_filter', True, GuardrailSeverity.CRITICAL)

		# Toxic patterns
		self.toxic_patterns = [
			r'nên chết',
			r'đi chết',
			r'ghét cay ghét đắng',
			r'khinh miệt',
			r'phân biệt đối xử',
			# English
			r'you should die',
			r'kill yourself',
			r'hate you',
			r'discriminat',
		]

	def check(self, content: str, context: Dict[str, Any] = None) -> GuardrailResult:
		violations = []
		content_lower = content.lower()

		found_toxic = []
		for pattern in self.toxic_patterns:
			if re.search(pattern, content_lower, re.IGNORECASE):
				found_toxic.append(pattern)

		if found_toxic:
			violation = GuardrailViolation(
				rule_name=self.name,
				severity=self.severity,
				action=GuardrailAction.BLOCK,
				message=f'Phát hiện nội dung độc hại trong AI response',
				details={'toxic_patterns': found_toxic},
				timestamp=datetime.now(),
			)
			violations.append(violation)

			return GuardrailResult(passed=False, violations=violations)

		return GuardrailResult(passed=True, violations=[])


class BrandSafetyGuardrail(BaseGuardrail):
	"""Kiểm tra brand safety cho EnterViu"""

	def __init__(self):
		super().__init__('brand_safety_filter', True, GuardrailSeverity.HIGH)

		# Nội dung không phù hợp với thương hiệu EnterViu
		self.brand_unsafe_keywords = [
			# Violence
			'bạo lực',
			'đánh nhau',
			'chiến tranh',
			# Adult content
			'sex',
			'porn',
			'18+',
			# Negative career content
			'thất nghiệp vĩnh viễn',
			'không có hy vọng',
			'bỏ việc',
			# Competitor mentions (có thể thêm)
			# "competitor_platform_name"
		]

	def check(self, content: str, context: Dict[str, Any] = None) -> GuardrailResult:
		violations = []
		content_lower = content.lower()

		found_unsafe = [kw for kw in self.brand_unsafe_keywords if kw in content_lower]

		if found_unsafe:
			violation = GuardrailViolation(
				rule_name=self.name,
				severity=self.severity,
				action=GuardrailAction.MODIFY,
				message=f'Nội dung có thể không phù hợp với thương hiệu EnterViu',
				details={'unsafe_keywords': found_unsafe},
				timestamp=datetime.now(),
			)
			violations.append(violation)

			# Suggest modification
			modified_content = content
			for keyword in found_unsafe:
				modified_content = modified_content.replace(keyword, '***')

			return GuardrailResult(passed=True, violations=violations, modified_content=modified_content)

		return GuardrailResult(passed=True, violations=[])


class ResponseQualityGuardrail(BaseGuardrail):
	"""Kiểm tra chất lượng response"""

	def __init__(self):
		super().__init__('response_quality_filter', True, GuardrailSeverity.MEDIUM)
		self.min_length = 10
		self.max_length = 3000

	def check(self, content: str, context: Dict[str, Any] = None) -> GuardrailResult:
		violations = []

		# Kiểm tra độ dài
		if len(content.strip()) < self.min_length:
			violation = GuardrailViolation(
				rule_name=self.name,
				severity=self.severity,
				action=GuardrailAction.BLOCK,
				message=f'Response quá ngắn ({len(content)} < {self.min_length} ký tự)',
				details={'content_length': len(content), 'min_length': self.min_length},
				timestamp=datetime.now(),
			)
			violations.append(violation)

			return GuardrailResult(passed=False, violations=violations)

		if len(content) > self.max_length:
			violation = GuardrailViolation(
				rule_name=self.name,
				severity=self.severity,
				action=GuardrailAction.ALLOW,  # Cảnh báo nhưng cho phép
				message=f'Response hơi dài ({len(content)} > {self.max_length} ký tự)',
				details={'content_length': len(content), 'max_length': self.max_length},
				timestamp=datetime.now(),
			)
			violations.append(violation)

		# Kiểm tra có phải chỉ toàn ký tự đặc biệt
		if re.match(r'^[^\w\s]*$', content.strip()):
			violation = GuardrailViolation(
				rule_name=self.name,
				severity=self.severity,
				action=GuardrailAction.BLOCK,
				message='Response chỉ chứa ký tự đặc biệt',
				details={'special_chars_only': True},
				timestamp=datetime.now(),
			)
			violations.append(violation)

			return GuardrailResult(passed=False, violations=violations)

		return GuardrailResult(passed=True, violations=violations)


class EnterViuConsistencyGuardrail(BaseGuardrail):
	"""Kiểm tra tính nhất quán với EnterViu values"""

	def __init__(self):
		super().__init__('enterviu_consistency_filter', True, GuardrailSeverity.LOW)

		# EnterViu values
		self.enterviu_values = [
			'professional',
			'career-focused',
			'innovative',
			'supportive',
			'growth-oriented',
			'collaborative',
			'opportunity-driven',
			'success-focused',
		]

		# Negative values (trái với EnterViu)
		self.negative_values = [
			'unprofessional',
			'lazy',
			'outdated',
			'unsupportive',
			'stagnant',
			'competitive in negative way',
			'opportunity-blocking',
		]

	def check(self, content: str, context: Dict[str, Any] = None) -> GuardrailResult:
		violations = []
		content_lower = content.lower()

		# Kiểm tra negative values
		found_negative = [val for val in self.negative_values if val in content_lower]

		if found_negative:
			violation = GuardrailViolation(
				rule_name=self.name,
				severity=self.severity,
				action=GuardrailAction.ALLOW,  # Chỉ cảnh báo
				message=f'Response có thể không phù hợp với giá trị EnterViu',
				details={'negative_values': found_negative},
				timestamp=datetime.now(),
			)
			violations.append(violation)

		# Kiểm tra có promote EnterViu values không
		found_positive = [val for val in self.enterviu_values if val in content_lower]

		return GuardrailResult(
			passed=True,
			violations=violations,
			metadata={
				'enterviu_values_mentioned': found_positive,
				'negative_values_mentioned': found_negative,
				'alignment_score': len(found_positive) / max(1, len(found_negative) + len(found_positive)),
			},
		)
