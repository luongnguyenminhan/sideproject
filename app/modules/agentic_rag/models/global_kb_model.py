## IMPORT NGOÀI MODULE CẦN XỬ LÍ
from app.core.base_model import BaseEntity
from sqlalchemy import Column, String, Text, Boolean


class GlobalKB(BaseEntity):
	__tablename__ = 'global_kb'
	title = Column(String(255), nullable=False)
	file_name = Column(String(255), nullable=False)
	file_type = Column(String(100), nullable=True)
	category = Column(String(64), default='general')
	source = Column(String(500), nullable=True)  # MinIO URL
	indexed = Column(Boolean, default=False)  # Track if file is indexed
	index_status = Column(String(50), default='pending')  # pending, success, failed
