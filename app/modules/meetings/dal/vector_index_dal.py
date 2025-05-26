"""Vector index data access layer"""

from datetime import datetime
from typing import List

from pytz import timezone
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.core.base_dal import BaseDAL
from app.modules.meetings.models.vector_index import VectorIndex


class VectorIndexDAL(BaseDAL[VectorIndex]):
	"""VectorIndexDAL for database operations on vector indices"""

	def __init__(self, db: Session):
		"""Initialize the VectorIndexDAL

		Args:
		    db (Session): Database session
		"""
		super().__init__(db, VectorIndex)

	def get_indices_by_meeting(self, meeting_id: str, index_type: str | None = None) -> List[VectorIndex]:
		"""Get all vector indices for a meeting

		Args:
		    meeting_id (str): Meeting ID
		    index_type (Optional[str]): Index type filter

		Returns:
		    List[VectorIndex]: List of vector indices
		"""
		query = self.db.query(VectorIndex).filter(and_(VectorIndex.meeting_id == meeting_id, VectorIndex.is_deleted == False))

		if index_type:
			query = query.filter(VectorIndex.index_type == index_type)

		return query.all()

	def get_indices_by_transcript(self, transcript_id: str) -> List[VectorIndex]:
		"""Get all vector indices for a transcript

		Args:
		    transcript_id (str): Transcript ID

		Returns:
		    List[VectorIndex]: List of vector indices
		"""
		return (
			self.db.query(VectorIndex)
			.filter(
				and_(
					VectorIndex.transcript_id == transcript_id,
					VectorIndex.is_deleted == False,
				)
			)
			.all()
		)

	def get_indices_by_meeting_note(self, meeting_note_id: str) -> List[VectorIndex]:
		"""Get all vector indices for a meeting note

		Args:
		    meeting_note_id (str): Meeting note ID

		Returns:
		    List[VectorIndex]: List of vector indices
		"""
		return (
			self.db.query(VectorIndex)
			.filter(
				and_(
					VectorIndex.meeting_note_id == meeting_note_id,
					VectorIndex.is_deleted == False,
				)
			)
			.all()
		)

	def get_index_by_vector_db_id(self, vector_db_id: str) -> VectorIndex | None:
		"""Get a vector index by vector database ID

		Args:
		    vector_db_id (str): Vector database ID

		Returns:
		    Optional[VectorIndex]: Vector index if found, None otherwise
		"""
		return (
			self.db.query(VectorIndex)
			.filter(
				and_(
					VectorIndex.vector_db_id == vector_db_id,
					VectorIndex.is_deleted == False,
				)
			)
			.first()
		)

	def create_index(self, index_data: dict) -> VectorIndex:
		"""Create a new vector index

		Args:
		    index_data (dict): Index data

		Returns:
		    VectorIndex: Created vector index
		"""
		# Add indexed_at timestamp if not provided
		if 'indexed_at' not in index_data:
			index_data['indexed_at'] = datetime.now(timezone('Asia/Ho_Chi_Minh'))

		return self.create(index_data)

	def update_index(self, index_id: str, index_data: dict) -> VectorIndex | None:
		"""Update an existing vector index

		Args:
		    index_id (str): Index ID
		    index_data (dict): Updated index data

		Returns:
		    Optional[VectorIndex]: Updated vector index if found, None otherwise
		"""
		return self.update(index_id, index_data)

	def delete_index(self, index_id: str) -> bool:
		"""Delete a vector index

		Args:
		    index_id (str): Index ID

		Returns:
		    bool: True if deleted, False otherwise
		"""
		return self.update(index_id, {'is_deleted': True}) is not None

	def delete_indices_by_meeting(self, meeting_id: str) -> int:
		"""Delete all vector indices for a meeting

		Args:
		    meeting_id (str): Meeting ID

		Returns:
		    int: Number of indices deleted
		"""
		indices = self.get_indices_by_meeting(meeting_id)
		count = 0

		for index in indices:
			if self.delete_index(index.id):
				count += 1

		return count
