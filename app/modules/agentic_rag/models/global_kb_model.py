from app.core.base_model import BaseEntity
from sqlalchemy import Column, String, Text
import json

class GlobalKB(BaseEntity):
    __tablename__ = "global_kb"
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(64), default="general")
    tags = Column(Text, default='[]')  # Lưu JSON string
    source = Column(String(255), nullable=True)

    def get_tags(self):
        try:
            return json.loads(self.tags or '[]')
        except Exception:
            return []

    def set_tags(self, tags_list):
        self.tags = json.dumps(tags_list)
