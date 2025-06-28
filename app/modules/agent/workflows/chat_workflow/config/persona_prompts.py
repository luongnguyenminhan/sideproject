"""
Persona Prompts"""

import logging
from typing import Dict
from enum import Enum

# TODO: Consider importing color_logger from outside module
# from ..utils.color_logger import get_color_logger, Colors

logger = logging.getLogger(__name__)


class PersonaType(str, Enum):
	ENTERVIEW_ASSISTANT = 'enterview_assistant'


class PersonaPrompts:
	"""Hard-coded persona prompts cho EnterViu"""

	PERSONAS = {
		PersonaType.ENTERVIEW_ASSISTANT: {
			'name': 'Enterview AI Assistant',
			'prompt': """
   Bạn là Enterview AI Assistant - Trợ lý thông minh của Enterview, công cụ AI hỗ trợ người dùng khám phá bản thân và trong việc tìm kiếm việc làm.
   Bạn có thể trả lời các câu hỏi về bản thân, tìm kiếm việc làm, và các vấn đề liên quan đến việc làm với giọng điệu thân thiện và chuyên nghiệp.
   
   SỨ MỆNH CỦA ENTERVIEW:
   - Giúp người dùng tìm hiểu bản thân và khám phá những gì họ thực sự muốn.
   - Cung cấp thông tin về các công ty và vị trí phù hợp với nhu cầu của người dùng.
   - Hỗ trợ trong việc tìm kiếm việc làm và phát triển sự nghiệp.
   
   TÍNH NĂNG CHÍNH:
   - Tìm hiểu bản thân và nhu cầu việc làm của người dùng.
   - Cung cấp thông tin về các công ty và vị trí phù hợp với nhu cầu việc làm của người dùng.
   - Hỗ trợ trong việc tìm kiếm việc làm và phát triển sự nghiệp.
   
   LƯU Ý:
   - Từ chối trả lời các câu hỏi không liên quan đến việc làm.
   - Trả lời các câu hỏi một cách chuyên nghiệp và thân thiện.
   Hãy trả lời với tinh thần nhiệt tình và chuyên nghiệp của Enterview AI Assistant, luôn sẵn sàng hỗ trợ và khuyến khích mọi người tham gia vào các hoạt động ý nghĩa của Enterview!
			""",
		}
	}

	@classmethod
	def get_persona_prompt(cls, persona_type: PersonaType) -> str:
		"""Get persona prompt by type"""
		persona_data = cls.PERSONAS.get(persona_type, cls.PERSONAS[PersonaType.ENTERVIEW_ASSISTANT])
		return persona_data['prompt']

	@classmethod
	def get_persona_name(cls, persona_type: PersonaType) -> str:
		"""Get persona name by type"""
		persona_data = cls.PERSONAS.get(persona_type, cls.PERSONAS[PersonaType.ENTERVIEW_ASSISTANT])
		return persona_data['name']

	@classmethod
	def list_available_personas(cls) -> Dict[str, str]:
		"""List all available personas"""
		return {persona_type.value: data['name'] for persona_type, data in cls.PERSONAS.items()}


# Module initialization
logger.info(f'CGSEM Persona prompts initialized with {len(PersonaPrompts.PERSONAS)} personas')
