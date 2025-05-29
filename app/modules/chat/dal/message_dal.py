from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.core.base_dal import BaseDAL
from app.modules.chat.models.message import Message
from typing import List, Optional


class MessageDAL(BaseDAL[Message]):
    def __init__(self, db: Session):
        super().__init__(db, Message)

    def get_conversation_messages(
        self,
        conversation_id: str,
        page: int = 1,
        page_size: int = 50,
        before_message_id: Optional[str] = None,
    ):
        """Get messages for a conversation with pagination"""
        query = self.db.query(self.model).filter(
            self.model.conversation_id == conversation_id,
            self.model.is_deleted == False,
        )

        # If before_message_id is provided, get messages before that message
        if before_message_id:
            before_message = self.get_by_id(before_message_id)
            if before_message:
                query = query.filter(self.model.timestamp < before_message.timestamp)

        # Order by timestamp descending (newest first)
        query = query.order_by(desc(self.model.timestamp))

        return self.paginate(query, page, page_size)

    def get_conversation_history(
        self, conversation_id: str, limit: int = 10
    ) -> List[Message]:
        """Get recent messages for conversation context"""
        return (
            self.db.query(self.model)
            .filter(
                self.model.conversation_id == conversation_id,
                self.model.is_deleted == False,
            )
            .order_by(desc(self.model.timestamp))
            .limit(limit)
            .all()
        )

    def get_latest_message(self, conversation_id: str) -> Optional[Message]:
        """Get the latest message in a conversation"""
        return (
            self.db.query(self.model)
            .filter(
                self.model.conversation_id == conversation_id,
                self.model.is_deleted == False,
            )
            .order_by(desc(self.model.timestamp))
            .first()
        )
