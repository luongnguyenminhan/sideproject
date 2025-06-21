"""
Guardrail Manager cho Chat Workflow
Tích hợp và quản lý tất cả guardrail rules với LLM-powered analysis
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from .core import GuardrailEngine, GuardrailResult
from .llm_guardrail import LLMGuardrailEngine
from .input_guardrails import (
	ProfanityGuardrail,
	SpamGuardrail,
	LengthGuardrail,
	PersonalInfoGuardrail,
	InjectionGuardrail,
	EnterViuContextGuardrail,
)
from .output_guardrails import (
	HallucinationGuardrail,
	FactualityGuardrail,
	ToxicityGuardrail,
	BrandSafetyGuardrail,
	ResponseQualityGuardrail,
	EnterViuConsistencyGuardrail,
)
from ..utils.color_logger import get_color_logger, Colors

# TODO: Consider using external color_logger module
# from ..utils.color_logger import get_color_logger, Colors

# Initialize colorful logger
color_logger = get_color_logger(__name__)


class ChatWorkflowGuardrailManager:
	"""Manager chính cho tất cả guardrail trong Chat Workflow với LLM-powered analysis."""

	def __init__(self, config: Dict[str, Any] = None):
		"""
		Initialize guardrail manager

		Args:
		    config: Configuration dictionary với các options:
		        - enable_input_guardrails: bool (default True)
		        - enable_output_guardrails: bool (default True)
		        - enable_llm_guardrails: bool (default True)
		        - use_llm_only: bool (default False) - Chỉ dùng LLM guardrails
		        - max_input_length: int (default 5000)
		        - strict_mode: bool (default False)
		        - model_name: str (default 'gemini-2.0-flash-lite')
		"""
		self.config = config or {}

		# Cấu hình mặc định
		self.enable_input_guardrails = self.config.get('enable_input_guardrails', True)
		self.enable_output_guardrails = self.config.get('enable_output_guardrails', True)
		self.enable_llm_guardrails = self.config.get('enable_llm_guardrails', True)
		self.use_llm_only = self.config.get('use_llm_only', False)
		self.max_input_length = self.config.get('max_input_length', 5000)
		self.strict_mode = self.config.get('strict_mode', False)
		self.model_name = self.config.get('model_name', 'gemini-2.0-flash-lite')

		# Initialize appropriate engine
		if self.enable_llm_guardrails:
			self.engine = LLMGuardrailEngine(enable_llm_guardrails=True, model_name=self.model_name)
			color_logger.info(
				f'🧠 {Colors.BOLD}LLM GUARDRAIL MANAGER:{Colors.RESET} Initialized with AI-powered protection',
				Colors.BRIGHT_GREEN,
				llm_enabled=True,
				model=self.model_name,
				use_llm_only=self.use_llm_only,
			)
		else:
			self.engine = GuardrailEngine()
			color_logger.info(
				f'🛡️ {Colors.BOLD}TRADITIONAL GUARDRAIL MANAGER:{Colors.RESET} Initialized with rule-based protection',
				Colors.BRIGHT_BLUE,
				llm_enabled=False,
			)

		# Setup additional guardrails if not LLM-only mode
		if not self.use_llm_only:
			self._setup_traditional_guardrails()

	def _setup_traditional_guardrails(self):
		"""Setup traditional rule-based guardrail rules as backup/complement."""

		color_logger.info(
			f'⚙️ {Colors.BOLD}SETTING UP TRADITIONAL GUARDRAILS:{Colors.RESET} Adding rule-based protection',
			Colors.BRIGHT_CYAN,
			complement_llm=self.enable_llm_guardrails,
		)
		if self.enable_input_guardrails:
			# Input guardrails (as backup or complement to LLM)
			self.engine.add_input_guardrail(ProfanityGuardrail())
			self.engine.add_input_guardrail(SpamGuardrail())
			self.engine.add_input_guardrail(LengthGuardrail(max_length=self.max_input_length))
			self.engine.add_input_guardrail(PersonalInfoGuardrail())
			self.engine.add_input_guardrail(InjectionGuardrail())
			self.engine.add_input_guardrail(EnterViuContextGuardrail())

		if self.enable_output_guardrails:
			# Output guardrails (as backup or complement to LLM)
			self.engine.add_output_guardrail(HallucinationGuardrail())
			self.engine.add_output_guardrail(FactualityGuardrail())
			self.engine.add_output_guardrail(ToxicityGuardrail())
			self.engine.add_output_guardrail(BrandSafetyGuardrail())
			self.engine.add_output_guardrail(ResponseQualityGuardrail())
			self.engine.add_output_guardrail(EnterViuConsistencyGuardrail())

	def check_user_input(self, user_input: str, context: Dict[str, Any] = None) -> GuardrailResult:
		"""
		Kiểm tra input từ user với LLM-powered analysis

		Args:
		    user_input: Input từ user
		    context: Context thêm (user_id, conversation_id, etc.)

		Returns:
		    GuardrailResult với thông tin vi phạm và content đã sửa đổi (nếu có)
		"""
		if not self.enable_input_guardrails:
			return GuardrailResult(passed=True, violations=[])

		# Enhanced context for LLM analysis
		enhanced_context = context or {}
		enhanced_context.update({
			'analysis_type': 'input',
			'strict_mode': self.strict_mode,
			'timestamp': datetime.now().isoformat(),
			'llm_enabled': self.enable_llm_guardrails,
		})

		color_logger.workflow_start(
			'User Input Guardrail Check',
			llm_enabled=self.enable_llm_guardrails,
			content_length=len(user_input),
			traditional_guards=not self.use_llm_only,
		)

		result = self.engine.check_input(user_input, enhanced_context)

		color_logger.info(
			f'🛡️ {Colors.BOLD}INPUT GUARDRAIL RESULT:{Colors.RESET} {"✅ PASSED" if result.passed else "❌ BLOCKED"}',
			Colors.BRIGHT_GREEN if result.passed else Colors.BRIGHT_RED,
			violations_count=len(result.violations),
			modified=bool(result.modified_content),
			processing_time=result.processing_time,
		)

		return result

	def check_ai_output(self, ai_output: str, context: Dict[str, Any] = None) -> GuardrailResult:
		"""
		Kiểm tra output từ AI với LLM-powered analysis

		Args:
		    ai_output: Response từ AI
		    context: Context thêm (query, rag_context, etc.)

		Returns:
		    GuardrailResult với thông tin vi phạm và content đã sửa đổi (nếu có)
		"""
		if not self.enable_output_guardrails:
			return GuardrailResult(passed=True, violations=[])

		# Enhanced context for LLM analysis
		enhanced_context = context or {}
		enhanced_context.update({
			'analysis_type': 'output',
			'strict_mode': self.strict_mode,
			'timestamp': datetime.now().isoformat(),
			'llm_enabled': self.enable_llm_guardrails,
		})

		color_logger.workflow_start(
			'AI Output Guardrail Check',
			llm_enabled=self.enable_llm_guardrails,
			content_length=len(ai_output),
			traditional_guards=not self.use_llm_only,
		)

		result = self.engine.check_output(ai_output, enhanced_context)

		color_logger.info(
			f'🛡️ {Colors.BOLD}OUTPUT GUARDRAIL RESULT:{Colors.RESET} {"✅ PASSED" if result.passed else "⚠️ FLAGGED"}',
			Colors.BRIGHT_GREEN if result.passed else Colors.BRIGHT_YELLOW,
			violations_count=len(result.violations),
			modified=bool(result.modified_content),
			processing_time=result.processing_time,
		)

		return result

	def get_guardrail_stats(self) -> Dict[str, Any]:
		"""Lấy thống kê guardrail với thông tin LLM."""
		stats = self.engine.get_stats()
		stats.update({
			'llm_enabled': self.enable_llm_guardrails,
			'use_llm_only': self.use_llm_only,
			'model_name': self.model_name if self.enable_llm_guardrails else None,
			'manager_config': {
				'enable_input_guardrails': self.enable_input_guardrails,
				'enable_output_guardrails': self.enable_output_guardrails,
				'strict_mode': self.strict_mode,
				'max_input_length': self.max_input_length,
			},
		})
		return stats

	def disable_guardrail(self, guardrail_name: str) -> bool:
		"""
		Disable một guardrail cụ thể

		Args:
		    guardrail_name: Tên guardrail cần disable

		Returns:
		    True nếu thành công, False nếu không tìm thấy
		"""
		for guardrail in self.engine.input_guardrails + self.engine.output_guardrails:
			if guardrail.name == guardrail_name:
				guardrail.enabled = False
				color_logger.info(
					f'🚫 {Colors.BOLD}GUARDRAIL DISABLED:{Colors.RESET} {guardrail_name}',
					Colors.BRIGHT_YELLOW,
				)
				return True
		return False

	def enable_guardrail(self, guardrail_name: str) -> bool:
		"""
		Enable một guardrail cụ thể

		Args:
		    guardrail_name: Tên guardrail cần enable

		Returns:
		    True nếu thành công, False nếu không tìm thấy
		"""
		for guardrail in self.engine.input_guardrails + self.engine.output_guardrails:
			if guardrail.name == guardrail_name:
				guardrail.enabled = True
				color_logger.info(
					f'✅ {Colors.BOLD}GUARDRAIL ENABLED:{Colors.RESET} {guardrail_name}',
					Colors.BRIGHT_GREEN,
				)
				return True
		return False

	def get_active_guardrails(self) -> Dict[str, List[str]]:
		"""Lấy danh sách guardrails đang active."""
		active_input = [g.name for g in self.engine.input_guardrails if g.is_enabled()]
		active_output = [g.name for g in self.engine.output_guardrails if g.is_enabled()]

		return {
			'input_guardrails': active_input,
			'output_guardrails': active_output,
			'total_active': len(active_input) + len(active_output),
		}


# Factory functions để tạo các loại guardrail manager khác nhau


def create_llm_only_manager(
	model_name: str = 'gemini-2.0-flash-lite',
) -> ChatWorkflowGuardrailManager:
	"""Tạo guardrail manager chỉ sử dụng LLM."""
	config = {
		'enable_llm_guardrails': True,
		'use_llm_only': True,
		'model_name': model_name,
		'strict_mode': False,
	}

	color_logger.info(
		f'🧠 {Colors.BOLD}CREATING LLM-ONLY GUARDRAIL MANAGER:{Colors.RESET} AI-powered protection only',
		Colors.BRIGHT_MAGENTA,
		model=model_name,
	)

	return ChatWorkflowGuardrailManager(config)


def create_hybrid_manager(model_name: str = 'gemini-2.0-flash-lite', strict_mode: bool = False) -> ChatWorkflowGuardrailManager:
	"""Tạo hybrid guardrail manager (LLM + traditional rules)."""
	config = {
		'enable_llm_guardrails': True,
		'use_llm_only': False,
		'model_name': model_name,
		'strict_mode': strict_mode,
		'enable_input_guardrails': True,
		'enable_output_guardrails': True,
	}

	color_logger.info(
		f'🔥 {Colors.BOLD}CREATING HYBRID GUARDRAIL MANAGER:{Colors.RESET} LLM + Traditional rules',
		Colors.BRIGHT_CYAN,
		model=model_name,
		strict_mode=strict_mode,
	)

	return ChatWorkflowGuardrailManager(config)


def create_traditional_manager(
	strict_mode: bool = False,
) -> ChatWorkflowGuardrailManager:
	"""Tạo traditional guardrail manager (chỉ rule-based)."""
	config = {
		'enable_llm_guardrails': False,
		'use_llm_only': False,
		'strict_mode': strict_mode,
		'enable_input_guardrails': True,
		'enable_output_guardrails': True,
	}

	color_logger.info(
		f'🛡️ {Colors.BOLD}CREATING TRADITIONAL GUARDRAIL MANAGER:{Colors.RESET} Rule-based protection only',
		Colors.BRIGHT_BLUE,
		strict_mode=strict_mode,
	)

	return ChatWorkflowGuardrailManager(config)


# Singleton instance cho dễ sử dụng
_default_manager = None


def get_default_guardrail_manager(
	config: Dict[str, Any] = None,
) -> ChatWorkflowGuardrailManager:
	"""
	Lấy default guardrail manager (singleton pattern)

	Args:
	    config: Configuration cho manager (chỉ sử dụng lần đầu)

	Returns:
	    ChatWorkflowGuardrailManager instance
	"""
	global _default_manager

	if _default_manager is None:
		_default_manager = ChatWorkflowGuardrailManager(config)

	return _default_manager


def reset_default_guardrail_manager():
	"""Reset default manager (useful for testing)"""
	global _default_manager
	_default_manager = None
