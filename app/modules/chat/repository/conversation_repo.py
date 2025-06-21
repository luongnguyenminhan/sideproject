from pytz import timezone
from sqlalchemy.orm import Session
from fastapi import Depends

## IMPORT NGOÀI MODULE CẦN XỬ LÍ
## IMPORT NGOÀI MODULE CẦN XỬ LÍ
from app.core.database import get_db

## IMPORT NGOÀI MODULE CẦN XỬ LÍ
## IMPORT NGOÀI MODULE CẦN XỬ LÍ
from app.core.base_repo import BaseRepo
from ..dal.conversation_dal import ConversationDAL
from ..dal.message_dal import MessageDAL
from ..schemas.conversation_request import ConversationListRequest

## IMPORT NGOÀI MODULE CẦN XỬ LÍ
## IMPORT NGOÀI MODULE CẦN XỬ LÍ
from app.exceptions.exception import NotFoundException

## IMPORT NGOÀI MODULE CẦN XỬ LÍ
from app.middleware.translation_manager import _
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ConversationRepo(BaseRepo):
    def __init__(self, db: Session = Depends(get_db)):
        super().__init__(db)
        self.conversation_dal = ConversationDAL(db)
        self.message_dal = MessageDAL(db)

    def get_user_conversations(self, user_id: str, request: ConversationListRequest):
        """Get user's conversations with pagination and filtering"""
        conversations = self.conversation_dal.get_user_conversations(
            user_id=user_id,
            page=request.page,
            page_size=request.page_size,
            search=request.search,
            order_by=request.order_by,
            order_direction=request.order_direction,
        )
        return conversations

    def get_conversation_by_id(self, conversation_id: str, user_id: str):
        """Get conversation by ID and verify user access"""
        conversation = self.conversation_dal.get_user_conversation_by_id(
            conversation_id, user_id
        )
        if not conversation:
            raise NotFoundException(_("conversation_not_found"))
        return conversation

    def create_conversation(
        self,
        user_id: str,
        name: str,
        initial_message: str = None,
        system_prompt: str = None,
    ):
        """Create a new conversation"""
        conversation_data = {
            "name": name,
            "user_id": user_id,
            "message_count": 0,
            "last_activity": datetime.now(timezone("Asia/Ho_Chi_Minh")).isoformat(),
            "system_prompt": system_prompt,
        }

        with self.conversation_dal.transaction():
            conversation = self.conversation_dal.create(conversation_data)

            # If initial message provided, create it
            if initial_message:
                pass
            return conversation

    def update_conversation(
        self,
        conversation_id: str,
        user_id: str,
        name: str = None,
        system_prompt: str = None,
    ):
        """Update conversation details"""
        conversation = self.get_conversation_by_id(conversation_id, user_id)

        update_data = {}
        if name:
            update_data["name"] = name
        if system_prompt is not None:  # Allow empty string to clear system prompt
            update_data["system_prompt"] = system_prompt

        if update_data:
            with self.conversation_dal.transaction():
                updated_conversation = self.conversation_dal.update(
                    conversation_id, update_data
                )
                return updated_conversation

        return conversation

    def delete_conversation(self, conversation_id: str, user_id: str):
        """Delete a conversation and its messages"""
        conversation = self.get_conversation_by_id(conversation_id, user_id)

        with self.conversation_dal.transaction():
            # Soft delete related messages in MySQL first
            self.message_dal.soft_delete_by_conversation(conversation_id)

            # Soft delete conversation in MySQL
            update_data = {
                "is_deleted": True,
                "update_date": datetime.now(timezone("Asia/Ho_Chi_Minh")).isoformat(),
            }
            self.conversation_dal.update(conversation_id, update_data)

    def get_conversation_messages(
        self,
        conversation_id: str,
        page: int = 1,
        page_size: int = 50,
        before_message_id: str = None,
    ):
        """Get messages for a conversation with pagination"""
        messages = self.message_dal.get_conversation_messages(
            conversation_id=conversation_id,
            page=page,
            page_size=page_size,
            before_message_id=before_message_id,
        )
        return messages
