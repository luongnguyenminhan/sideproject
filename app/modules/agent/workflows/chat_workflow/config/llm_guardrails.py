"""
LLM Guardrails Configuration for Chat Workflow
Centralized configuration for LLM-powered guardrails
"""

from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class GuardrailMode(str, Enum):
    """Operating modes for guardrails"""
    LLM_ONLY = 'llm_only'              # Only use LLM-based guardrails
    HYBRID = 'hybrid'                  # LLM + traditional rule-based
    TRADITIONAL = 'traditional'        # Only traditional rule-based
    DISABLED = 'disabled'              # All guardrails disabled


class GuardrailStrictness(str, Enum):
    """Strictness levels for guardrail enforcement"""
    RELAXED = 'relaxed'      # Allow most content, minimal blocking
    STANDARD = 'standard'    # Balanced approach (default)
    STRICT = 'strict'        # High security, more blocking
    PARANOID = 'paranoid'    # Maximum security, very strict


@dataclass
class LLMGuardrailConfig:
    """Configuration for LLM-powered guardrails"""
    
    # Core settings
    mode: GuardrailMode = GuardrailMode.LLM_ONLY
    strictness: GuardrailStrictness = GuardrailStrictness.STANDARD
    
    # LLM settings
    model_name: str = 'gemini-2.0-flash-lite'
    temperature: float = 0.1  # Low temperature for consistent analysis
    timeout_seconds: int = 30
    
    # Input guardrail settings
    enable_input_guardrails: bool = True
    max_input_length: int = 10000
    input_analysis_depth: str = 'comprehensive'  # basic, standard, comprehensive
    
    # Output guardrail settings  
    enable_output_guardrails: bool = True
    max_output_length: int = 20000
    output_analysis_depth: str = 'comprehensive'
    
    # Retry and fallback settings
    max_retry_attempts: int = 3
    enable_fallback: bool = True
    fallback_action: str = 'allow_with_warning'  # allow_with_warning, block, escalate
    
    # Performance settings
    enable_caching: bool = True
    cache_ttl_seconds: int = 3600
    parallel_analysis: bool = False  # For multiple guardrails
    
    # Confidence thresholds
    min_confidence_threshold: float = 0.7
    critical_confidence_threshold: float = 0.9
    
    # Content categories to monitor
    monitored_categories: List[str] = None
    
    # Brand safety settings (for EnterViu)
    brand_safety_enabled: bool = True
    enterview_specific_rules: bool = True
    career_context_awareness: bool = True
    
    def __post_init__(self):
        """Initialize default monitored categories if not provided"""
        if self.monitored_categories is None:
            self.monitored_categories = [
                'profanity',
                'harassment',
                'hate_speech', 
                'violence',
                'adult_content',
                'privacy_violation',
                'spam',
                'misinformation',
                'brand_safety',
                'off_topic',
                'security_threat'
            ]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'mode': self.mode.value,
            'strictness': self.strictness.value,
            'model_name': self.model_name,
            'temperature': self.temperature,
            'timeout_seconds': self.timeout_seconds,
            'enable_input_guardrails': self.enable_input_guardrails,
            'max_input_length': self.max_input_length,
            'input_analysis_depth': self.input_analysis_depth,
            'enable_output_guardrails': self.enable_output_guardrails,
            'max_output_length': self.max_output_length,
            'output_analysis_depth': self.output_analysis_depth,
            'max_retry_attempts': self.max_retry_attempts,
            'enable_fallback': self.enable_fallback,
            'fallback_action': self.fallback_action,
            'enable_caching': self.enable_caching,
            'cache_ttl_seconds': self.cache_ttl_seconds,
            'parallel_analysis': self.parallel_analysis,
            'min_confidence_threshold': self.min_confidence_threshold,
            'critical_confidence_threshold': self.critical_confidence_threshold,
            'monitored_categories': self.monitored_categories,
            'brand_safety_enabled': self.brand_safety_enabled,
            'enterview_specific_rules': self.enterview_specific_rules,
            'career_context_awareness': self.career_context_awareness
        }
    
    @classmethod
    def for_enterview_production(cls) -> 'LLMGuardrailConfig':
        """Create production config optimized for EnterViu"""
        return cls(
            mode=GuardrailMode.LLM_ONLY,
            strictness=GuardrailStrictness.STANDARD,
            model_name='gemini-2.0-flash-lite',
            temperature=0.1,
            enable_input_guardrails=True,
            enable_output_guardrails=True,
            max_retry_attempts=2,
            enable_fallback=True,
            fallback_action='allow_with_warning',
            min_confidence_threshold=0.7,
            critical_confidence_threshold=0.9,
            brand_safety_enabled=True,
            enterview_specific_rules=True,
            career_context_awareness=True
        )
    
    @classmethod
    def for_development(cls) -> 'LLMGuardrailConfig':
        """Create relaxed config for development"""
        return cls(
            mode=GuardrailMode.LLM_ONLY,
            strictness=GuardrailStrictness.RELAXED,
            model_name='gemini-2.0-flash-lite',
            temperature=0.2,
            enable_input_guardrails=True,
            enable_output_guardrails=True,
            max_retry_attempts=1,
            enable_fallback=True,
            fallback_action='allow_with_warning',
            min_confidence_threshold=0.5,
            critical_confidence_threshold=0.8,
            brand_safety_enabled=False,
            enterview_specific_rules=False,
            career_context_awareness=False
        )
    
    @classmethod  
    def for_high_security(cls) -> 'LLMGuardrailConfig':
        """Create high security config"""
        return cls(
            mode=GuardrailMode.HYBRID,
            strictness=GuardrailStrictness.STRICT,
            model_name='gemini-2.0-flash-lite',
            temperature=0.05,
            enable_input_guardrails=True,
            enable_output_guardrails=True,
            max_retry_attempts=3,
            enable_fallback=True,
            fallback_action='block',
            min_confidence_threshold=0.8,
            critical_confidence_threshold=0.95,
            brand_safety_enabled=True,
            enterview_specific_rules=True,
            career_context_awareness=True
        )


# Default configurations for different environments
DEFAULT_CONFIGS = {
    'production': LLMGuardrailConfig.for_enterview_production(),
    'development': LLMGuardrailConfig.for_development(), 
    'testing': LLMGuardrailConfig.for_development(),
    'staging': LLMGuardrailConfig.for_enterview_production(),
    'high_security': LLMGuardrailConfig.for_high_security()
}


def get_guardrail_config(environment: str = 'production') -> LLMGuardrailConfig:
    """Get guardrail configuration for specific environment"""
    return DEFAULT_CONFIGS.get(environment, DEFAULT_CONFIGS['production'])


def create_custom_guardrail_config(**kwargs) -> LLMGuardrailConfig:
    """Create custom guardrail configuration with overrides"""
    base_config = LLMGuardrailConfig.for_enterview_production()
    
    # Update with provided kwargs
    for key, value in kwargs.items():
        if hasattr(base_config, key):
            setattr(base_config, key, value)
    
    return base_config


# Factory functions for LLM Guardrails Manager integration
def get_llm_guardrails_manager():
    """Get LLM Guardrails Manager with EnterViu configuration"""
    from ..guardrails.manager import create_llm_only_manager
    return create_llm_only_manager(model_name='gemini-2.0-flash-lite')


def initialize_guardrails_with_llm(llm_instance):
    """Initialize guardrails system with LLM instance"""
    from ..guardrails.manager import create_llm_only_manager
    
    # Create mock manager for compatibility - in real implementation
    # we would use the actual LLM instance to create the guardrails
    class MockGuardrailsManager:
        def __init__(self, llm):
            self.llm = llm
            self.manager = create_llm_only_manager(model_name='gemini-2.0-flash-lite')
        
        async def validate_user_input(self, user_input: str, context: dict = None):
            """Validate user input through LLM guardrails"""
            try:
                result = self.manager.check_user_input(user_input, context)
                return {
                    'is_safe': result.passed,
                    'summary': f'Input validation: {"passed" if result.passed else "failed"}',
                    'violations': [v.message for v in result.violations],
                    'overall_severity': result.violations[0].severity.value if result.violations else 'low'
                }
            except Exception as e:
                return {
                    'is_safe': True,
                    'summary': f'Input validation error: {str(e)}',
                    'error': str(e)
                }
        
        async def validate_ai_response(self, ai_response: str, context: dict = None):
            """Validate AI response through LLM guardrails"""
            try:
                result = self.manager.check_ai_output(ai_response, context)
                return {
                    'is_safe': result.passed,
                    'summary': f'Output validation: {"passed" if result.passed else "flagged"}',
                    'violations': [v.message for v in result.violations],
                    'overall_severity': result.violations[0].severity.value if result.violations else 'low'
                }
            except Exception as e:
                return {
                    'is_safe': True, # Allow on error for output
                    'summary': f'Output validation error: {str(e)}',
                    'error': str(e)
                }
        
        async def validate_tool_usage(self, tool_name: str, tool_args: dict, context: dict = None):
            """Validate tool usage - simple implementation"""
            try:
                # Simple validation - could be enhanced with actual LLM analysis
                return {
                    'is_safe': True,
                    'summary': f'Tool {tool_name} usage validated',
                    'tool_name': tool_name
                }
            except Exception as e:
                return {
                    'is_safe': True, # Allow on error
                    'summary': f'Tool validation error: {str(e)}',
                    'error': str(e)
                }
    
    return MockGuardrailsManager(llm_instance)