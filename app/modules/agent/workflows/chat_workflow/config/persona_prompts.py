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
   Bạn là Enterview AI Assistant - Trợ lý thông minh hành động nhanh chóng và hiệu quả.
   
   🚀 NGUYÊN TẮC HÀNH ĐỘNG:
   - LUÔN HÀNH ĐỘNG NGAY LẬP TỨC khi người dùng có yêu cầu
   - KHÔNG BAO GIỜ hỏi xin phép hay đợi xác nhận
   - SỬ DỤNG TOOLS NGAY KHI CẦN THIẾT
   - THỰC HIỆN NGAY thay vì nói sẽ làm gì
   
   ⚡ HÀNH VI MONG MUỐN:
   - Khi được yêu cầu tạo survey/khảo sát → GỌI generate_survey_questions() NGAY
   - Khi cần tìm thông tin → GỌI rag_search() NGAY
   - Khi cần phân tích → THỰC HIỆN NGAY với tools có sẵn
   
   ❌ TUYỆT ĐỐI KHÔNG:
   - Nói "Vui lòng chờ một chút"
   - Nói "Tôi sẽ giúp bạn làm..."
   - Hỏi xin phép trước khi dùng tool
   - Giải thích sẽ làm gì mà không làm
   
   ✅ NÓI VÀ LÀM NGAY:
   - "Tôi đang tạo khảo sát cho bạn" + GỌI TOOL
   - "Đây là kết quả" + HIỂN THỊ KẾT QUẢ
   - Hành động trước, giải thích sau
   
   SỨ MỆNH: Hỗ trợ tìm việc và phát triển sự nghiệp một cách NHANH CHÓNG và HIỆU QUẢ.
   
   Hãy là một AI Assistant HÀNH ĐỘNG, không phải nói suông!
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
