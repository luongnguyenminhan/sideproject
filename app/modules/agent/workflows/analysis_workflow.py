from typing import Dict, Any, AsyncGenerator
from app.modules.chat.agent.workflows.base_workflow import BaseWorkflow
from app.modules.chat.agent.services.langgraph_service import LangGraphService


class AnalysisWorkflow(BaseWorkflow):
    """Data analysis and insights workflow implementation"""
    
    def __init__(self, config):
        super().__init__(config)
        self.workflow_type = "analytical"
        self.langgraph_service = LangGraphService()
    
    async def execute(self, context: Dict[str, Any], api_key: str = None) -> Dict[str, Any]:
        """Execute analytical workflow"""
        
        if not self.validate_context(context):
            raise ValueError("Invalid context for analysis workflow")
        
        # Enhance context for analytical processing
        enhanced_context = self.prepare_context(context)
        enhanced_context['analysis_mode'] = True
        enhanced_context['focus'] = 'data_insights'
        
        # Add analysis-specific processing
        enhanced_context['processing_steps'] = [
            'data_understanding',
            'pattern_recognition',
            'insight_generation',
            'recommendation_formulation'
        ]
        
        # Execute through LangGraph service
        result = await self.langgraph_service.execute_workflow(
            agent_config=self.config,
            context=enhanced_context,
            api_key=api_key
        )
        
        # Add analysis-specific metadata
        result['metadata']['workflow_type'] = self.workflow_type
        result['metadata']['analysis_approach'] = 'structured_insights'
        result['metadata']['processing_steps'] = enhanced_context['processing_steps']
        
        return result
    
    async def execute_streaming(self, context: Dict[str, Any], 
                              api_key: str = None) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute streaming analytical workflow"""
        
        if not self.validate_context(context):
            yield {
                'type': 'error',
                'message': 'Invalid context for analysis workflow'
            }
            return
        
        # Enhance context for analytical processing
        enhanced_context = self.prepare_context(context)
        enhanced_context['analysis_mode'] = True
        enhanced_context['focus'] = 'data_insights'
        
        # Add analysis-specific processing
        enhanced_context['processing_steps'] = [
            'data_understanding',
            'pattern_recognition',
            'insight_generation',
            'recommendation_formulation'
        ]
        
        # Execute streaming through LangGraph service
        async for chunk in self.langgraph_service.execute_streaming_workflow(
            agent_config=self.config,
            context=enhanced_context,
            api_key=api_key
        ):
            # Add analysis-specific metadata to chunks
            if chunk.get('type') == 'metadata':
                chunk['data']['workflow_type'] = self.workflow_type
                chunk['data']['analysis_approach'] = 'structured_insights'
                chunk['data']['processing_steps'] = enhanced_context['processing_steps']
            
            # Add processing step indicators
            if chunk.get('type') == 'content':
                content = chunk.get('content', '')
                
                # Add step indicators based on content
                for i, step in enumerate(enhanced_context['processing_steps']):
                    if step.replace('_', ' ') in content.lower():
                        chunk['processing_step'] = {
                            'current': step,
                            'step_number': i + 1,
                            'total_steps': len(enhanced_context['processing_steps'])
                        }
                        break
            
            yield chunk
    
    def prepare_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare context specifically for analysis workflow"""
        enhanced_context = super().prepare_context(context)
        
        # Add analysis-specific system prompt enhancement
        system_enhancement = """
        You are a data analysis specialist. Focus on:
        1. Understanding the data or problem thoroughly
        2. Identifying patterns, trends, and insights
        3. Providing structured, evidence-based analysis
        4. Offering actionable recommendations
        5. Using clear, logical reasoning in your explanations
        6. Presenting findings in an organized manner
        
        Structure your response with:
        - Data Understanding
        - Key Insights
        - Patterns/Trends
        - Recommendations
        - Next Steps
        """
        
        enhanced_context['system_enhancement'] = system_enhancement
        enhanced_context['response_style'] = 'analytical_structured'
        enhanced_context['output_format'] = 'structured_analysis'
        
        return enhanced_context
    
    def validate_context(self, context: Dict[str, Any]) -> bool:
        """Validate context for analysis workflow"""
        base_valid = super().validate_context(context)
        
        # Additional validation for analysis
        if not base_valid:
            return False
        
        # Check if message contains analytical intent
        user_message = context.get('user_message', '').lower()
        analytical_keywords = [
            'analyze', 'analysis', 'insights', 'patterns', 'trends',
            'data', 'statistics', 'examine', 'investigate', 'study',
            'compare', 'evaluate', 'assess', 'review'
        ]
        
        has_analytical_intent = any(keyword in user_message for keyword in analytical_keywords)
        
        return has_analytical_intent or context.get('force_analysis', False)
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get analysis workflow capabilities"""
        return {
            'streaming': True,
            'memory': True,
            'tools': [
                'data_analysis',
                'pattern_recognition',
                'statistical_analysis',
                'web_search',
                'memory_retrieval'
            ],
            'features': [
                'structured_analysis',
                'insight_generation',
                'trend_identification',
                'evidence_based_reasoning',
                'actionable_recommendations',
                'data_visualization_suggestions'
            ],
            'max_context_length': 20,
            'response_style': 'analytical_structured',
            'output_formats': ['structured_analysis', 'detailed_report', 'executive_summary']
        }