import json
from pathlib import Path

from fastapi import Request


class TranslationManager:
	"""
	A class that manages translations and handles the installation of the
	correct language translation at runtime.
	"""

	_instance = None

	def __new__(cls):
		if cls._instance is None:
			cls._instance = super().__new__(cls)
			cls._instance.lang = 'vi'  # Default language
			cls._instance.load_translation(cls._instance.lang)
		return cls._instance

	def load_translation(self, lang: str):
		"""Load translations from a JSON file based on the selected language."""
		locales_dir = Path(Path(__file__).parent).parent / 'locales'
		file_path = locales_dir / f'{lang}.json'
		if file_path.exists():
			with open(file_path, encoding='utf-8') as f:
				self.translations = json.load(f)
		else:
			self.translations = {}  # Empty if file doesn't exist

	def translate(self, text: str) -> str:
		"""Return the translated string for the given message."""
		return self.translations.get(text, text)  # Default to input if not found


async def set_language(request: Request):
	"""Middleware function to set language based on the Accept-Language header."""
	translator = TranslationManager()
	lang = request.headers.get('lang') or request.query_params.get('lang', 'vi')
	lang = lang[:2]  # Ensure it's only 2 characters (e.g., "en", "vi")
	# Store the language in request state
	request.state.lang = lang
	print(lang)
	translator.load_translation(lang)


def _(text: str) -> str:
	"""Shortcut function to access translation for a given string."""
	translator = TranslationManager()
	return translator.translate(text)
