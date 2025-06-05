"""
Guardrail Core System cho Chat Workflow
Production-ready content safety và compliance system
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Union
import re
import time
from datetime import datetime


class GuardrailSeverity(Enum):
	"""Mức độ nghiêm trọng của vi phạm guardrail"""

	LOW = 'low'
	MEDIUM = 'medium'
	HIGH = 'high'
	CRITICAL = 'critical'


class GuardrailAction(Enum):
	"""Hành động khi vi phạm guardrail"""

	ALLOW = 'allow'  # Cho phép với cảnh báo
	MODIFY = 'modify'  # Sửa đổi nội dung
	BLOCK = 'block'  # Chặn hoàn toàn
	ESCALATE = 'escalate'  # Báo cáo và chặn


@dataclass
class GuardrailViolation:
	"""Chi tiết vi phạm guardrail"""

	rule_name: str
	severity: GuardrailSeverity
	action: GuardrailAction
	message: str
	details: Dict[str, Any]
	timestamp: datetime
	confidence: float = 1.0


@dataclass
class GuardrailResult:
	"""Kết quả kiểm tra guardrail"""

	passed: bool
	violations: List[GuardrailViolation]
	modified_content: Optional[str] = None
	metadata: Dict[str, Any] = None
	processing_time: float = 0.0


class BaseGuardrail(ABC):
	"""Base class cho tất cả guardrail rules"""

	def __init__(
		self,
		name: str,
		enabled: bool = True,
		severity: GuardrailSeverity = GuardrailSeverity.MEDIUM,
	):
		self.name = name
		self.enabled = enabled
		self.severity = severity
		self.violation_count = 0
		self.last_violation = None

	@abstractmethod
	def check(self, content: str, context: Dict[str, Any] = None) -> GuardrailResult:
		"""Kiểm tra nội dung theo rule cụ thể"""
		pass

	def is_enabled(self) -> bool:
		"""Kiểm tra rule có được enable không"""
		return self.enabled

	def get_stats(self) -> Dict[str, Any]:
		"""Lấy thống kê vi phạm"""
		return {
			'name': self.name,
			'violation_count': self.violation_count,
			'last_violation': self.last_violation,
			'enabled': self.enabled,
			'severity': self.severity.value,
		}


class GuardrailEngine:
	"""Engine chính để xử lý tất cả guardrail rules"""

	def __init__(self):
		self.input_guardrails: List[BaseGuardrail] = []
		self.output_guardrails: List[BaseGuardrail] = []
		self.global_stats = {
			'total_checks': 0,
			'total_violations': 0,
			'blocked_content': 0,
			'modified_content': 0,
		}

	def add_input_guardrail(self, guardrail: BaseGuardrail):
		"""Thêm input guardrail"""
		self.input_guardrails.append(guardrail)

	def add_output_guardrail(self, guardrail: BaseGuardrail):
		"""Thêm output guardrail"""
		self.output_guardrails.append(guardrail)

	def check_input(self, user_input: str, context: Dict[str, Any] = None) -> GuardrailResult:
		"""Kiểm tra đầu vào từ user"""
		return self._run_guardrails(user_input, self.input_guardrails, context or {})

	def check_output(self, ai_output: str, context: Dict[str, Any] = None) -> GuardrailResult:
		"""Kiểm tra đầu ra từ AI"""
		return self._run_guardrails(ai_output, self.output_guardrails, context or {})

	def _run_guardrails(self, content: str, guardrails: List[BaseGuardrail], context: Dict[str, Any]) -> GuardrailResult:
		"""Chạy tất cả guardrail rules"""
		start_time = time.time()
		all_violations = []
		modified_content = content

		self.global_stats['total_checks'] += 1

		for guardrail in guardrails:
			if not guardrail.is_enabled():
				continue

			try:
				result = guardrail.check(modified_content, context)

				if result.violations:
					all_violations.extend(result.violations)
					guardrail.violation_count += len(result.violations)
					guardrail.last_violation = datetime.now()

					# Áp dụng modifications nếu có
					if result.modified_content:
						modified_content = result.modified_content
						self.global_stats['modified_content'] += 1

			except Exception as e:
				# Log error nhưng không crash toàn bộ system
				violation = GuardrailViolation(
					rule_name=guardrail.name,
					severity=GuardrailSeverity.HIGH,
					action=GuardrailAction.ESCALATE,
					message=f'Guardrail execution error: {str(e)}',
					details={'error': str(e), 'guardrail': guardrail.name},
					timestamp=datetime.now(),
				)
				all_violations.append(violation)

		# Xác định kết quả cuối cùng
		has_blocking_violations = any(v.action in [GuardrailAction.BLOCK, GuardrailAction.ESCALATE] for v in all_violations)

		if has_blocking_violations:
			self.global_stats['blocked_content'] += 1

		if all_violations:
			self.global_stats['total_violations'] += len(all_violations)

		processing_time = time.time() - start_time

		return GuardrailResult(
			passed=not has_blocking_violations,
			violations=all_violations,
			modified_content=modified_content if modified_content != content else None,
			metadata={
				'original_content_length': len(content),
				'modified_content_length': len(modified_content),
				'guardrails_checked': len([g for g in guardrails if g.is_enabled()]),
				'violations_found': len(all_violations),
			},
			processing_time=processing_time,
		)

	def get_stats(self) -> Dict[str, Any]:
		"""Lấy thống kê tổng quan"""
		guardrail_stats = []

		for guardrail in self.input_guardrails + self.output_guardrails:
			guardrail_stats.append(guardrail.get_stats())

		return {
			'global_stats': self.global_stats,
			'guardrail_stats': guardrail_stats,
			'total_guardrails': len(self.input_guardrails) + len(self.output_guardrails),
			'active_guardrails': len([g for g in self.input_guardrails + self.output_guardrails if g.is_enabled()]),
		}
