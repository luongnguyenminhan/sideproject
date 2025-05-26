import json
import logging
import os
from typing import Any, Dict

import aiohttp  # type: ignore

logger = logging.getLogger(__name__)


class AgentMicroService:
	def __init__(self, base_url: str = 'https://open-ai-api.epoints.vn') -> None:
		self.base_url = base_url
		self.headers = {
			'accept': 'application/json',
			'Content-Type': 'application/json',
			'x-header-checksum': 'fixed-checksum-that-never-changes-123456789',  # Replace with actual checksum value
		}

	async def post_message(self, transcript: str, email: str | None = None) -> Dict[str, Any]:
		try:
			endpoint = f'{self.base_url}/api/v2/meeting-note/post-messages'
			payload = {'prompt': transcript}
			if email:
				payload['email'] = email
			else:
				payload['email'] = ''

			async with aiohttp.ClientSession() as session:
				async with session.post(endpoint, headers=self.headers, json=payload) as response:
					response.raise_for_status()
					return await response.json()

		except aiohttp.ClientError as e:
			raise Exception(f'Failed to post message: {str(e)}')
		except Exception as e:
			raise Exception(f'Unexpected error in post_message: {str(e)}')

	async def post_message_v2(
		self,
		transcript: str,
		email: str | None = None,
		meeting_type: str = 'general',
		custom_prompt: str | None = None,
	) -> Dict[str, Any]:
		try:
			endpoint = f'{self.base_url}/api/v2/meeting-note/post-messages'

			payload = {
				'prompt': transcript,
				'meeting_type': meeting_type,
				'custom_prompt': custom_prompt,
			}
			if email:
				payload['email'] = email
			else:
				payload['email'] = ''

			async with aiohttp.ClientSession() as session:
				async with session.post(endpoint, headers=self.headers, json=payload, timeout=10000000000) as response:
					response.raise_for_status()
					return await response.json()

		except aiohttp.ClientError as e:
			raise Exception(f'Failed to post message: {str(e)}')
		except Exception as e:
			raise Exception(f'Unexpected error in post_message: {str(e)}')

	async def post_summary(self, prompt: str) -> Dict[str, Any]:
		try:
			endpoint = f'{self.base_url}/api/v1/meeting-note/conversation-summarizer'
			payload = {'prompt': prompt}

			async with aiohttp.ClientSession() as session:
				async with session.post(endpoint, headers=self.headers, json=payload, timeout=10000000000) as response:
					response.raise_for_status()
					return await response.json()

		except aiohttp.ClientError as e:
			raise Exception(f'Failed to get summary: {str(e)}')
		except Exception as e:
			raise Exception(f'Unexpected error in post_summary: {str(e)}')

	async def process_audio(self, audio_path: str) -> Dict | None:
		"""
		Process an audio file and return the transcript

		Args:
		        audio_path: Path to the audio file

		Returns:
		        Dictionary containing transcript and token count
		"""
		try:
			endpoint = f'{self.base_url}/api/v1/meeting-note/audio-to-transcript'

			# Check if file exists
			if not os.path.exists(audio_path):
				raise FileNotFoundError(f'Audio file not found: {audio_path}')

			# Prepare the file for upload
			logger.debug(f'Processing audio file: {audio_path}')
			async with aiohttp.ClientSession() as session:
				with open(audio_path, 'rb') as audio_file:
					data = aiohttp.FormData()
					data.add_field(
						'audio',
						audio_file,
						filename=os.path.basename(audio_path),
						content_type='multipart/form-data',
					)

					# Send the request
					logger.debug(f'Sending request to endpoint: {endpoint}')
					async with session.post(endpoint, headers={'accept': 'application/json'}, data=data, timeout=10000000000) as response:
						logger.debug(f'Response status: {response.status}')
						response.raise_for_status()

						# Read the entire response at once
						data = await response.read()
						result = json.loads(data.decode('utf-8'))

						logger.debug('Received complete response data')
						print('Result:', result)

						return {
							'transcript': result.get('transcript', ''),
							'tokens': result.get(
								'tokens',
								{'totalTokens': 0, 'cachedContentTokenCount': 0},
							),
						}

		except aiohttp.ClientError as e:
			logger.error(f'API request failed: {str(e)}')
			return None
		except Exception as e:
			logger.error(f'Unexpected error in process_audio: {str(e)}')
			return None
