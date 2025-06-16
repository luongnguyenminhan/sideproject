from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import DATABASE_URL

# SQL Database setup

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
	bind=engine,
	autocommit=False,
	autoflush=False,
)

Base = declarative_base()


def get_db():
	"""get_db"""
	db = SessionLocal()
	try:
		yield db
	except Exception as e:
		db.rollback()  # Rollback nếu có lỗi
		print(f'[ERROR] Database session error: {e}')  # Debug log
		raise  # Quan trọng: Raise lại lỗi để FastAPI xử lý đúng
	finally:
		db.close()
