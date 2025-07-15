"""
JD Matching Tool for Chat Agent (N8N Integration)
Triggers the n8n JD matching workflow with provided JD and candidate data.
"""

import logging
import json
from typing import Dict, Any, Optional
from langchain_core.tools import tool
from app.utils.n8n_api_client import n8n_client

logger = logging.getLogger(__name__)

@tool(return_direct=False)
async def trigger_jd_matching_tool(
    jd_data_json: str,
    candidate_data_json: str,
    authorization_token: Optional[str] = None,
) -> str:
    """
    Trigger the JD matching workflow on n8n with provided JD and candidate data.

    Args:
        jd_data_json: Job Description data as JSON string
        candidate_data_json: Candidate profile data as JSON string
        authorization_token: Optional auth token for n8n

    Returns:
        Result from n8n workflow or error message
    """
    try:
        jd_data = json.loads(jd_data_json)
        candidate_data = json.loads(candidate_data_json)
    except Exception as e:
        logger.error(f'[trigger_jd_matching_tool] Invalid input JSON: {e}')
        return f'❌ Invalid input JSON: {str(e)}'

    try:
        logger.info('[trigger_jd_matching_tool] Calling n8n JD matching workflow...')
        result = await n8n_client.trigger_jd_matching(
            jd_data=jd_data,
            candidate_data=candidate_data,
            authorization_token=authorization_token,
        )
        logger.info('[trigger_jd_matching_tool] JD matching workflow completed.')
        return f'✅ JD matching result: {json.dumps(result)}'
    except Exception as e:
        logger.error(f'[trigger_jd_matching_tool] Error triggering JD matching: {e}')
        return f'❌ Error triggering JD matching: {str(e)}'

__all__ = ['trigger_jd_matching_tool'] 