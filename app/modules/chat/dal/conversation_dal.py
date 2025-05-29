from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from app.core.base_dal import BaseDAL
from app.modules.chat.models.conversation import Conversation
from typing import Optional


class ConversationDAL(BaseDAL[Conversation]):
    def __init__(self, db: Session):
        super().__init__(db, Conversation)

    def get_user_conversations(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 10,
        search: Optional[str] = None,
        order_by: str = "last_activity",
        order_direction: str = "desc",
    ):
        """Get conversations for a user with pagination and filtering"""
        query = self.db.query(self.model).filter(
            self.model.user_id == user_id, self.model.is_deleted == False
        )

        # Apply search filter
        if search:
            query = query.filter(self.model.name.ilike(f"%{search}%"))

        # Apply ordering
        order_column = getattr(self.model, order_by, self.model.last_activity)
        if order_direction.lower() == "desc":
            query = query.order_by(desc(order_column))
        else:
            query = query.order_by(asc(order_column))

        return self.paginate(query, page, page_size)

    def get_user_conversation_by_id(
        self, conversation_id: str, user_id: str
    ) -> Optional[Conversation]:
        """Get a specific conversation for a user"""
        return (
            self.db.query(self.model)
            .filter(
                self.model.id == conversation_id,
                self.model.user_id == user_id,
                self.model.is_deleted == False,
            )
            .first()
        )
