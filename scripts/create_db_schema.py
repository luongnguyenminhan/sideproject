#!/usr/bin/env python
"""
Database Schema Creation Script

This script creates all database tables defined by SQLAlchemy models.
It imports all model classes to ensure they are registered with the Base metadata.
"""

import importlib
import os
import sys
from datetime import datetime

from pytz import timezone

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import database configuration
from app.core.config import DATABASE_URL, SQLALCHEMY_DATABASE_URI
from app.core.database import Base, engine

# Meeting Calendar module
from app.modules.meeting_calendar.models.calendar import (
	CalendarEvent,
	CalendarIntegration,
)

# Meeting Files module
from app.modules.meeting_files.models.meeting_file import MeetingFile

# Meeting Tags module
from app.modules.meeting_tags.models.tag import MeetingTag, Tag

# Meeting Transcripts module
from app.modules.meeting_transcripts.models.transcript import Transcript

# Meetings module
from app.modules.meetings.models.meeting import Meeting
from app.modules.meetings.models.meeting_note import MeetingItem, MeetingNote
from app.modules.meetings.models.notification import Notification
from app.modules.meetings.models.token_usage import TokenUsage
from app.modules.meetings.models.vector_index import VectorIndex
from app.modules.users.models.otp import OTP
from app.modules.users.models.user_logs import UserLog

# Import all models to ensure they're registered with Base.metadata
# Users module
from app.modules.users.models.users import User


def create_tables():
	"""Create all tables defined by SQLAlchemy models"""
	print(f'[{datetime.now(timezone("Asia/Ho_Chi_Minh"))}] Starting database schema creation...')
	print(f'[{datetime.now(timezone("Asia/Ho_Chi_Minh"))}] Using database URL: {DATABASE_URL}')

	# Get all tables defined in the metadata
	tables = Base.metadata.tables
	print(f'[{datetime.now(timezone("Asia/Ho_Chi_Minh"))}] Found {len(tables)} tables defined in SQLAlchemy models:')
	for table_name in sorted(tables.keys()):
		print(f'  - {table_name}')

	# Create all tables
	print(f'[{datetime.now(timezone("Asia/Ho_Chi_Minh"))}] Creating tables in database...')
	Base.metadata.create_all(bind=engine)
	print(f'[{datetime.now(timezone("Asia/Ho_Chi_Minh"))}] Database schema creation completed successfully!')


if __name__ == '__main__':
	create_tables()
