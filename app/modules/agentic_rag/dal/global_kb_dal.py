from sqlalchemy.orm import Session

## IMPORT NGOÀI MODULE CẦN XỬ LÍ
from app.core.base_dal import BaseDAL
from ..models.global_kb_model import GlobalKB


class GlobalKBDAL(BaseDAL[GlobalKB]):
	def __init__(self, db: Session):
		super().__init__(db, GlobalKB)

	def search(self, query: str, top_k: int = 10, category: str = None):
		q = self.db.query(self.model).filter(self.model.is_deleted == False)
		if category:
			q = q.filter(self.model.category == category)
		if query:
			# Search by title or file_name since we don't store content anymore
			q = q.filter(self.model.title.ilike(f'%{query}%') | self.model.file_name.ilike(f'%{query}%'))
		return q.limit(top_k).all()

	def get_indexed_files(self):
		"""Get all successfully indexed files"""
		return (
			self.db.query(self.model)
			.filter(
				self.model.is_deleted == False,
				self.model.indexed == True,
				self.model.index_status == 'success',
			)
			.all()
		)

	def stats(self):
		total = self.db.query(self.model).filter(self.model.is_deleted == False).count()
		indexed = self.db.query(self.model).filter(self.model.is_deleted == False, self.model.indexed == True).count()
		return {
			'total_documents': total,
			'indexed_documents': indexed,
			'pending_documents': total - indexed,
		}
