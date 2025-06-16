"""
CV RAG Enhancement Tool for Chat Agent
Enhance RAG queries với CV context để cải thiện search results
"""

import logging
import json
from typing import Dict, Any, Optional, List
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class CVRAGEnhancementInput(BaseModel):
	"""Input schema for CV RAG Enhancement tool"""

	conversation_id: str = Field(description='ID của conversation')
	user_id: str = Field(description='ID của user')
	original_query: str = Field(description='Original user query')


class CVRAGEnhancementTool(BaseTool):
	"""Tool để enhance RAG queries với CV context"""

	name: str = 'cv_rag_enhancement'
	description: str = """
    Enhance RAG queries với CV context để tìm kiếm thông tin phù hợp hơn.
    Sử dụng khi user đã upload CV và query cần context về background/skills.
    Input: conversation_id, user_id, và original_query
    """

	db_session: Session = Field(exclude=True)

	def __init__(self, db_session: Session, **kwargs):
		super().__init__(db_session=db_session, **kwargs)

	def _run(self, conversation_id: str, user_id: str, original_query: str) -> str:
		"""
		Enhance RAG query với CV context

		Args:
		    conversation_id: ID của conversation
		    user_id: ID của user
		    original_query: Query gốc từ user

		Returns:
		    Enhanced query string hoặc original nếu không có CV
		"""
		try:
			logger.info(f'[CVRAGEnhancement] Enhancing query for conversation: {conversation_id}')

			# Import here to avoid circular import
			from app.modules.chat.repository.chat_repo import ChatRepo

			chat_repo = ChatRepo(self.db_session)

			# Get conversation and CV context
			conversation = chat_repo.get_conversation_by_id(conversation_id, user_id)

			if not conversation or not conversation.metadata:
				return original_query

			metadata = json.loads(conversation.metadata)
			cv_context = metadata.get('cv_context')

			if not cv_context or not cv_context.get('cv_uploaded'):
				return original_query

			# Extract relevant CV info for query enhancement
			enhancement_factors = []

			# Add skills context
			skills = cv_context.get('skills', [])
			if skills:
				relevant_skills = self._extract_relevant_skills(original_query, skills)
				if relevant_skills:
					enhancement_factors.append(f'Skills: {", ".join(relevant_skills[:5])}')

			# Add experience level context
			exp_count = cv_context.get('experience_count', 0)
			if exp_count > 0:
				if exp_count >= 5:
					enhancement_factors.append('Senior level professional')
				elif exp_count >= 2:
					enhancement_factors.append('Mid-level professional')
				else:
					enhancement_factors.append('Junior level professional')

			# Add education context if relevant
			edu_count = cv_context.get('education_count', 0)
			if edu_count > 0 and self._is_education_relevant(original_query):
				enhancement_factors.append('University educated')

			# Get detailed context from full CV analysis
			full_cv_analysis = cv_context.get('full_cv_analysis', {})

			# Add industry/domain context
			work_exp = full_cv_analysis.get('work_experience_history', {}).get('items', [])
			industries = self._extract_industries(work_exp)
			if industries:
				enhancement_factors.append(f'Industry experience: {", ".join(industries[:3])}')

			# Add role/position context
			roles = self._extract_roles(work_exp)
			if roles:
				enhancement_factors.append(f'Role background: {", ".join(roles[:3])}')

			# Build enhanced query
			if enhancement_factors:
				enhancement_context = ' | '.join(enhancement_factors)
				enhanced_query = f'{original_query} [User Context: {enhancement_context}]'

				logger.info(f'[CVRAGEnhancement] Query enhanced with CV context')
				return enhanced_query
			else:
				return original_query

		except Exception as e:
			logger.error(f'[CVRAGEnhancement] Error enhancing query: {str(e)}')
			return original_query

	def _extract_relevant_skills(self, query: str, skills: List[str]) -> List[str]:
		"""Extract skills relevant to the query"""
		query_lower = query.lower()
		relevant_skills = []

		# Keywords that suggest skill relevance
		skill_keywords = [
			'skill',
			'technology',
			'programming',
			'language',
			'framework',
			'tool',
			'software',
			'platform',
			'tech',
			'development',
		]

		# Check if query is asking about skills/tech
		if any(keyword in query_lower for keyword in skill_keywords):
			# Return top skills
			return skills[:10]

		# Check for specific skill mentions in query
		for skill in skills:
			if skill.lower() in query_lower:
				relevant_skills.append(skill)

		return relevant_skills

	def _is_education_relevant(self, query: str) -> bool:
		"""Check if education context is relevant to query"""
		education_keywords = [
			'education',
			'degree',
			'university',
			'college',
			'study',
			'course',
			'certification',
			'training',
			'academic',
			'learn',
		]
		query_lower = query.lower()
		return any(keyword in query_lower for keyword in education_keywords)

	def _extract_industries(self, work_experiences: List[Dict]) -> List[str]:
		"""Extract industries from work experience"""
		industries = set()

		for exp in work_experiences:
			company_name = exp.get('company_name', '').lower()
			job_title = exp.get('job_title', '').lower()

			# Simple industry detection based on company names and job titles
			if any(keyword in company_name + ' ' + job_title for keyword in ['tech', 'software', 'it', 'developer', 'engineer']):
				industries.add('Technology')
			elif any(keyword in company_name + ' ' + job_title for keyword in ['bank', 'finance', 'fintech', 'investment']):
				industries.add('Finance')
			elif any(keyword in company_name + ' ' + job_title for keyword in ['marketing', 'sales', 'advertising']):
				industries.add('Marketing')
			elif any(keyword in company_name + ' ' + job_title for keyword in ['education', 'teacher', 'instructor']):
				industries.add('Education')
			elif any(keyword in company_name + ' ' + job_title for keyword in ['health', 'medical', 'hospital']):
				industries.add('Healthcare')

		return list(industries)

	def _extract_roles(self, work_experiences: List[Dict]) -> List[str]:
		"""Extract role types from work experience"""
		roles = set()

		for exp in work_experiences:
			job_title = exp.get('job_title', '').lower()

			if any(keyword in job_title for keyword in ['manager', 'lead', 'director', 'head']):
				roles.add('Management')
			elif any(keyword in job_title for keyword in ['developer', 'engineer', 'programmer']):
				roles.add('Technical')
			elif any(keyword in job_title for keyword in ['analyst', 'consultant', 'advisor']):
				roles.add('Analysis')
			elif any(keyword in job_title for keyword in ['designer', 'creative', 'ui', 'ux']):
				roles.add('Design')
			elif any(keyword in job_title for keyword in ['sales', 'business development', 'account']):
				roles.add('Sales')

		return list(roles)

	async def _arun(self, conversation_id: str, user_id: str, original_query: str) -> str:
		"""Async version"""
		return self._run(conversation_id, user_id, original_query)
