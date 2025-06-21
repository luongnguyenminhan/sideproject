"""
Semantic Chunking Service - Đơn giản và nhẹ
"""

import logging
from typing import List
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings

## IMPORT NGOÀI MODULE CẦN XỬ LÍ
from app.core.config import GOOGLE_API_KEY
import numpy as np

logger = logging.getLogger(__name__)


class SemanticChunkingService:
	"""Service cho semantic chunking đơn giản"""

	def __init__(self):
		self.embedding = GoogleGenerativeAIEmbeddings(model='models/embedding-001', google_api_key=GOOGLE_API_KEY)

	def semantic_chunk(self, text: str, max_chunk_size: int = 1000, similarity_threshold: float = 0.7) -> List[str]:
		"""
		Semantic chunking đơn giản:
		- Chia văn bản theo câu
		- Nhóm câu có similarity cao
		- Giữ chunk size hợp lý
		"""
		# Chia theo câu đơn giản
		sentences = [s.strip() for s in text.split('.') if s.strip()]
		if len(sentences) <= 1:
			return [text]

		# Tính embedding cho từng câu
		embeddings = self.embedding.embed_documents(sentences)

		chunks = []
		current_chunk = [sentences[0]]
		current_size = len(sentences[0])

		for i in range(1, len(sentences)):
			sentence = sentences[i]
			sentence_size = len(sentence)

			# Kiểm tra similarity với câu cuối của chunk hiện tại
			similarity = self._cosine_similarity(embeddings[i - 1], embeddings[i])

			# Nếu similarity cao và size cho phép -> thêm vào chunk hiện tại
			if similarity >= similarity_threshold and current_size + sentence_size <= max_chunk_size:
				current_chunk.append(sentence)
				current_size += sentence_size
			else:
				# Tạo chunk mới
				chunks.append('. '.join(current_chunk) + '.')
				current_chunk = [sentence]
				current_size = sentence_size

		# Thêm chunk cuối
		if current_chunk:
			chunks.append('. '.join(current_chunk) + '.')

		return chunks

	def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
		"""Tính cosine similarity đơn giản"""
		try:
			a, b = np.array(vec1), np.array(vec2)
			return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
		except:
			return 0.0
