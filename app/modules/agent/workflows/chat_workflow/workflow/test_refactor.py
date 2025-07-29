"""
Test file to verify the refactored workflow modules work correctly
"""


def test_imports():
	"""Test that all modules can be imported successfully"""
	try:
		# Test main workflow import
		from app.modules.agent.workflows.chat_workflow.workflow import (
			Workflow,
			create_workflow,
		)

		print('✅ Main workflow import successful')

		# Test modular components import
		from app.modules.agent.workflows.chat_workflow.workflow.main import (
			Workflow as MainWorkflow,
		)
		from app.modules.agent.workflows.chat_workflow.workflow.nodes import (
			WorkflowNodes,
		)
		from app.modules.agent.workflows.chat_workflow.workflow.routing import (
			WorkflowRouter,
		)
		from app.modules.agent.workflows.chat_workflow.workflow.workflow_builder import (
			WorkflowBuilder,
		)
		from app.modules.agent.workflows.chat_workflow.workflow.prompts import (
			DEFAULT_SYSTEM_PROMPT,
			TOOL_DECISION_SYSTEM_PROMPT,
			ToolDecision,
			SURVEY_KEYWORDS,
			has_survey_keywords,
			build_enhanced_system_prompt,
		)

		print('✅ All module imports successful')

		# Test that main and modular imports are the same
		assert Workflow is MainWorkflow
		print('✅ Workflow class consistency verified')

		# Test helper functions
		test_message = 'Tôi muốn tạo câu hỏi survey'
		has_keywords = has_survey_keywords(test_message)
		assert has_keywords == True
		print('✅ Helper functions working correctly')

		# Test JD matching tool import
		from app.modules.agent.workflows.chat_workflow.tools.jd_matching_tool import (
			trigger_jd_matching_tool,
			get_jd_matching_tool,
			set_authorization_token,
			set_conversation_context,
			get_authorization_token,
			get_conversation_context,
		)
		print('✅ JD matching tool import successful')

		# Test JD matching tool functions
		set_authorization_token('test_token')
		set_conversation_context('test_conversation', 'test_user')
		token = get_authorization_token()
		conv_id, user_id = get_conversation_context()
		assert token == 'test_token'
		assert conv_id == 'test_conversation'
		assert user_id == 'test_user'
		print('✅ JD matching tool functions working correctly')

		print('\n🎉 ALL TESTS PASSED - Refactored workflow is working correctly!')
		return True

	except Exception as e:
		print(f'❌ Import test failed: {str(e)}')
		return False


if __name__ == '__main__':
	test_imports()
