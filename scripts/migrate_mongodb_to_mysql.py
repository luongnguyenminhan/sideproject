"""
Migration script để chuyển messages từ MongoDB sang MySQL
Chạy script này nếu bạn có dữ liệu cũ trong MongoDB cần migrate

Usage:
    python scripts/migrate_mongodb_to_mysql.py
"""

import sys
import os
from datetime import datetime
from sqlalchemy.orm import Session

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import get_db
from app.modules.chat.dal.message_dal import MessageDAL
from app.modules.chat.models.message import Message, MessageRole


def migrate_mongodb_messages_to_mysql():
    """
    Migrate messages từ MongoDB sang MySQL
    
    Lưu ý: Script này giả định bạn có MongoDB service running
    và có dữ liệu cần migrate. Cập nhật logic theo cấu trúc
    MongoDB hiện tại của bạn.
    """
    print("🚀 Starting MongoDB to MySQL migration...")
    
    # TODO: Import MongoDB client của bạn
    # from your_mongodb_service import mongodb_client
    
    db_session = next(get_db())
    message_dal = MessageDAL(db_session)
    
    try:
        # TODO: Thay thế logic này bằng cách lấy dữ liệu từ MongoDB thực tế
        print("📥 Fetching messages from MongoDB...")
        
        # Ví dụ mock data - thay thế bằng logic thật
        mongodb_messages = [
            # {
            #     'message_id': 'uuid-here',
            #     'conversation_id': 'conv-uuid',
            #     'user_id': 'user-uuid',
            #     'role': 'user',
            #     'content': 'Hello world',
            #     'timestamp': datetime.utcnow(),
            #     'model_used': 'gpt-3.5-turbo',
            #     'tokens_used': '{"total": 100}',
            #     'response_time_ms': '1500'
            # }
        ]
        
        migrated_count = 0
        
        for mongo_message in mongodb_messages:
            try:
                # Kiểm tra xem message đã tồn tại trong MySQL chưa
                existing_message = message_dal.get_by_id(mongo_message['message_id'])
                if existing_message:
                    print(f"⏭️ Message {mongo_message['message_id']} already exists, skipping...")
                    continue
                
                # Tạo message data cho MySQL
                message_data = {
                    'id': mongo_message['message_id'],
                    'conversation_id': mongo_message['conversation_id'],
                    'user_id': mongo_message['user_id'],
                    'role': MessageRole(mongo_message['role']),
                    'content': mongo_message['content'],
                    'timestamp': mongo_message['timestamp'],
                    'model_used': mongo_message.get('model_used'),
                    'tokens_used': mongo_message.get('tokens_used'),
                    'response_time_ms': mongo_message.get('response_time_ms'),
                }
                
                # Lưu vào MySQL
                message_dal.create(message_data)
                migrated_count += 1
                
                if migrated_count % 100 == 0:
                    print(f"✅ Migrated {migrated_count} messages...")
                    
            except Exception as e:
                print(f"❌ Error migrating message {mongo_message.get('message_id', 'unknown')}: {e}")
                continue
        
        # Commit transaction
        db_session.commit()
        print(f"🎉 Migration completed! Migrated {migrated_count} messages from MongoDB to MySQL")
        
    except Exception as e:
        print(f"💥 Migration failed: {e}")
        db_session.rollback()
        raise
    finally:
        db_session.close()


if __name__ == "__main__":
    # Cảnh báo
    response = input("⚠️  Bạn có chắc chắn muốn migrate dữ liệu từ MongoDB sang MySQL? (y/N): ")
    if response.lower() != 'y':
        print("🚫 Migration cancelled.")
        sys.exit(0)
    
    migrate_mongodb_messages_to_mysql() 