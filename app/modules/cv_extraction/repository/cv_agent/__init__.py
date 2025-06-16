from app.core.config import GOOGLE_API_KEY

# Changed from MeetingProcessor to CVProcessorWorkflow based on the new implementation
from .cv_processor import CVProcessorWorkflow
import logging


class CVAnalyzer:
	def __init__(self):
		self.logger = logging.getLogger(self.__class__.__name__)
		# Initialize CVProcessorWorkflow instead of MeetingProcessor
		self.cv_processor = CVProcessorWorkflow(api_key=GOOGLE_API_KEY)

	async def analyze_cv_content(
		self,
		cv_content: str,
	):
		try:
			self.logger.info(f'Starting CV analysis with content length: {len(cv_content or "")}')
			processor = self.cv_processor

			result = await processor.analyze_cv(cv_content)
			return result
		except Exception as e:
			self.logger.exception(f'Error in CVAnalyzer.analyze_cv_content: {str(e)}')
			# Return a more structured error, perhaps aligning with CVAnalysisResult structure
			return {
				'error': str(e),
				'raw_cv_content': cv_content,
				'llm_token_usage': (processor.token_tracker.get_usage() if hasattr(processor, 'token_tracker') else None),
			}
