from sqlalchemy.orm import Session
from app.core.base_dal import BaseDAL
from app.modules.agentic_rag.models.global_kb_model import GlobalKB

class GlobalKBDAL(BaseDAL[GlobalKB]):
    def __init__(self, db: Session):
        super().__init__(db, GlobalKB)

    def search(self, query: str, top_k: int = 10, category: str = None):
        q = self.db.query(self.model).filter(self.model.is_deleted == False)
        if category:
            q = q.filter(self.model.category == category)
        if query:
            q = q.filter(self.model.content.ilike(f"%{query}%"))
        return q.limit(top_k).all()

    def stats(self):
        total = self.db.query(self.model).filter(self.model.is_deleted == False).count()
        return {"total_documents": total}
