"""Dashboard Data Access Layer"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy import func, and_, or_, desc, asc, text
from sqlalchemy.orm import Session, joinedload

from app.core.base_dal import BaseDAL
from app.modules.users.models.users import User
from app.modules.users.models.user_logs import UserLog
from app.modules.chat.models.conversation import Conversation
from app.modules.chat.models.message import Message
from app.modules.chat.models.file import File
from app.modules.payment.models.payment import Payment
from app.modules.subscription.models.order import Order
from app.modules.question_session.models.question_session import QuestionSession, QuestionAnswer
from app.modules.agent.models.agent import Agent
from app.modules.agentic_rag.models.global_kb_model import GlobalKB
from app.enums.subscription_enums import RankEnum, OrderStatusEnum
from app.enums.user_enums import UserRoleEnum


class DashboardDAL:
    """Data Access Layer for Dashboard analytics"""

    def __init__(self, db: Session):
        self.db = db

    # Overview Statistics
    def get_overview_stats(self, start_date: Optional[datetime] = None, 
                          end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get general overview statistics"""
        now = datetime.utcnow()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)

        # User statistics
        total_users = self.db.query(User).filter(User.is_deleted == False).count()
        
        active_users_today = self.db.query(User).filter(
            and_(User.last_login_at >= today, User.is_deleted == False)
        ).count()
        
        active_users_week = self.db.query(User).filter(
            and_(User.last_login_at >= week_start, User.is_deleted == False)
        ).count()
        
        active_users_month = self.db.query(User).filter(
            and_(User.last_login_at >= month_start, User.is_deleted == False)
        ).count()

        # Conversation and Message statistics
        total_conversations = self.db.query(Conversation).filter(Conversation.is_deleted == False).count()
        total_messages = self.db.query(Message).filter(Message.is_deleted == False).count()
        
        conversations_today = self.db.query(Conversation).filter(
            and_(Conversation.create_date >= today, Conversation.is_deleted == False)
        ).count()
        
        messages_today = self.db.query(Message).filter(
            and_(Message.create_date >= today, Message.is_deleted == False)
        ).count()

        # Revenue statistics
        revenue_query = self.db.query(func.sum(Payment.amount)).filter(
            and_(Payment.status == 'COMPLETED', Payment.is_deleted == False)
        )
        
        total_revenue = revenue_query.scalar() or 0
        
        revenue_today = revenue_query.filter(Payment.created_at >= today).scalar() or 0
        
        revenue_week = revenue_query.filter(Payment.created_at >= week_start).scalar() or 0
        
        revenue_month = revenue_query.filter(Payment.created_at >= month_start).scalar() or 0

        # File statistics
        total_files = self.db.query(File).filter(File.is_deleted == False).count()
        
        total_file_size = self.db.query(func.sum(File.size)).filter(
            File.is_deleted == False
        ).scalar() or 0
        
        files_today = self.db.query(File).filter(
            and_(File.create_date >= today, File.is_deleted == False)
        ).count()

        # Question Session statistics
        total_sessions = self.db.query(QuestionSession).filter(
            QuestionSession.is_deleted == False
        ).count()
        
        completed_sessions = self.db.query(QuestionSession).filter(
            and_(QuestionSession.session_status == 'completed', QuestionSession.is_deleted == False)
        ).count()
        
        active_sessions = self.db.query(QuestionSession).filter(
            and_(QuestionSession.session_status == 'active', QuestionSession.is_deleted == False)
        ).count()

        return {
            "total_users": total_users,
            "active_users_today": active_users_today,
            "active_users_this_week": active_users_week,
            "active_users_this_month": active_users_month,
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "conversations_today": conversations_today,
            "messages_today": messages_today,
            "total_revenue": total_revenue / 100,  # Convert from cents to currency
            "revenue_this_month": revenue_month / 100,
            "revenue_this_week": revenue_week / 100,
            "revenue_today": revenue_today / 100,
            "total_files": total_files,
            "total_file_size": total_file_size,
            "files_uploaded_today": files_today,
            "total_question_sessions": total_sessions,
            "completed_sessions": completed_sessions,
            "active_sessions": active_sessions
        }

    # User Analytics
    def get_user_analytics(self, page: int = 1, page_size: int = 20, 
                          order_by: str = "create_date", order_direction: str = "desc") -> Tuple[List[Dict[str, Any]], int]:
        """Get detailed user analytics with pagination"""
        
        # Build the query with joins to get conversation and message counts
        query = self.db.query(
            User,
            func.count(Conversation.id.distinct()).label('conversation_count'),
            func.count(Message.id.distinct()).label('message_count'),
            func.count(File.id.distinct()).label('file_count')
        ).outerjoin(Conversation, User.id == Conversation.user_id)\
         .outerjoin(Message, User.id == Message.user_id)\
         .outerjoin(File, User.id == File.user_id)\
         .filter(User.is_deleted == False)\
         .group_by(User.id)

        # Apply ordering
        if hasattr(User, order_by):
            order_column = getattr(User, order_by)
            if order_direction.lower() == "desc":
                query = query.order_by(desc(order_column))
            else:
                query = query.order_by(asc(order_column))

        # Get total count
        total_count = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        results = query.offset(offset).limit(page_size).all()

        # Format results
        user_stats = []
        for result in results:
            user, conv_count, msg_count, file_count = result
            user_stats.append({
                "user_id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "rank": user.rank,
                "total_conversations": conv_count or 0,
                "total_messages": msg_count or 0,
                "total_files": file_count or 0,
                "last_activity": user.last_login_at,
                "join_date": user.create_date
            })

        return user_stats, total_count

    def get_user_growth_stats(self) -> Dict[str, Any]:
        """Get user growth statistics"""
        
        # Daily growth for last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        daily_growth = self.db.query(
            func.date(User.create_date).label('date'),
            func.count(User.id).label('count')
        ).filter(
            and_(User.create_date >= thirty_days_ago, User.is_deleted == False)
        ).group_by(func.date(User.create_date)).order_by('date').all()

        # Monthly growth for last 12 months
        twelve_months_ago = datetime.utcnow() - timedelta(days=365)
        monthly_growth = self.db.query(
            func.extract('year', User.create_date).label('year'),
            func.extract('month', User.create_date).label('month'),
            func.count(User.id).label('count')
        ).filter(
            and_(User.create_date >= twelve_months_ago, User.is_deleted == False)
        ).group_by(
            func.extract('year', User.create_date),
            func.extract('month', User.create_date)
        ).order_by('year', 'month').all()

        # Role distribution
        role_distribution = dict(self.db.query(
            User.role, func.count(User.id)
        ).filter(User.is_deleted == False).group_by(User.role).all())

        # Rank distribution
        rank_distribution = dict(self.db.query(
            User.rank, func.count(User.id)
        ).filter(User.is_deleted == False).group_by(User.rank).all())

        return {
            "daily_growth": [{"date": str(date), "count": count} for date, count in daily_growth],
            "monthly_growth": [{"year": int(year), "month": int(month), "count": count} 
                             for year, month, count in monthly_growth],
            "role_distribution": role_distribution,
            "rank_distribution": rank_distribution
        }

    # Revenue Analytics
    def get_revenue_analytics(self, start_date: Optional[datetime] = None,
                             end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get revenue analytics"""
        
        base_query = self.db.query(Payment).filter(
            and_(Payment.status == 'COMPLETED', Payment.is_deleted == False)
        )

        if start_date:
            base_query = base_query.filter(Payment.created_at >= start_date)
        if end_date:
            base_query = base_query.filter(Payment.created_at <= end_date)

        # Daily revenue for the period
        daily_revenue = self.db.query(
            func.date(Payment.created_at).label('date'),
            func.sum(Payment.amount).label('amount'),
            func.count(Payment.id).label('transaction_count')
        ).filter(
            and_(Payment.status == 'COMPLETED', Payment.is_deleted == False)
        )
        
        if start_date:
            daily_revenue = daily_revenue.filter(Payment.created_at >= start_date)
        if end_date:
            daily_revenue = daily_revenue.filter(Payment.created_at <= end_date)
            
        daily_revenue = daily_revenue.group_by(
            func.date(Payment.created_at)
        ).order_by('date').all()

        # Monthly revenue
        monthly_revenue = self.db.query(
            func.extract('year', Payment.created_at).label('year'),
            func.extract('month', Payment.created_at).label('month'),
            func.sum(Payment.amount).label('amount'),
            func.count(Payment.id).label('transaction_count')
        ).filter(
            and_(Payment.status == 'COMPLETED', Payment.is_deleted == False)
        )
        
        if start_date:
            monthly_revenue = monthly_revenue.filter(Payment.created_at >= start_date)
        if end_date:
            monthly_revenue = monthly_revenue.filter(Payment.created_at <= end_date)
            
        monthly_revenue = monthly_revenue.group_by(
            func.extract('year', Payment.created_at),
            func.extract('month', Payment.created_at)
        ).order_by('year', 'month').all()

        # Revenue by subscription rank (through orders)
        revenue_by_rank = dict(self.db.query(
            Order.rank_type,
            func.sum(Order.amount)
        ).filter(
            and_(Order.status == OrderStatusEnum.COMPLETED, Order.is_deleted == False)
        ).group_by(Order.rank_type).all())

        # Total metrics
        total_revenue = base_query.with_entities(func.sum(Payment.amount)).scalar() or 0
        transaction_count = base_query.count()
        avg_transaction = (total_revenue / transaction_count) if transaction_count > 0 else 0

        return {
            "daily_revenue": [
                {
                    "date": str(date),
                    "amount": float(amount) / 100,  # Convert from cents
                    "transaction_count": count,
                    "rank_type": None
                } for date, amount, count in daily_revenue
            ],
            "monthly_revenue": [
                {
                    "date": f"{int(year)}-{int(month):02d}",
                    "amount": float(amount) / 100,
                    "transaction_count": count,
                    "rank_type": None
                } for year, month, amount, count in monthly_revenue
            ],
            "revenue_by_rank": {rank: float(amount) / 100 for rank, amount in revenue_by_rank.items()},
            "total_revenue": float(total_revenue) / 100,
            "average_transaction_value": float(avg_transaction) / 100
        }

    # Chat Analytics
    def get_chat_analytics(self, page: int = 1, page_size: int = 20) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Get chat analytics"""
        
        # Get conversations with stats
        conversations_query = self.db.query(
            Conversation,
            User.name,
            User.email,
            func.count(File.id.distinct()).label('file_count')
        ).join(User, Conversation.user_id == User.id)\
         .outerjoin(File, Conversation.id == File.conversation_id)\
         .filter(Conversation.is_deleted == False)\
         .group_by(Conversation.id, User.name, User.email)\
         .order_by(desc(Conversation.last_activity))

        total_conversations = conversations_query.count()
        
        # Get paginated results
        offset = (page - 1) * page_size
        conversations = conversations_query.offset(offset).limit(page_size).all()

        conversation_stats = []
        for conv, user_name, user_email, file_count in conversations:
            conversation_stats.append({
                "conversation_id": conv.id,
                "name": conv.name,
                "user_name": user_name,
                "user_email": user_email,
                "message_count": conv.message_count,
                "file_count": file_count or 0,
                "last_activity": conv.last_activity,
                "created_date": conv.create_date
            })

        # Overall metrics
        total_messages = self.db.query(Message).filter(Message.is_deleted == False).count()
        avg_messages = total_messages / total_conversations if total_conversations > 0 else 0

        # Most active conversations
        most_active = self.db.query(
            Conversation,
            User.name,
            User.email
        ).join(User, Conversation.user_id == User.id)\
         .filter(Conversation.is_deleted == False)\
         .order_by(desc(Conversation.message_count))\
         .limit(5).all()

        most_active_list = [
            {
                "conversation_id": conv.id,
                "name": conv.name,
                "user_name": user_name,
                "user_email": user_email,
                "message_count": conv.message_count,
                "file_count": 0,  # Would need another query to get this
                "last_activity": conv.last_activity,
                "created_date": conv.create_date
            } for conv, user_name, user_email in most_active
        ]

        # Recent conversations
        recent = conversations[:5]  # Take first 5 from the paginated results

        analytics = {
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "average_messages_per_conversation": avg_messages,
            "most_active_conversations": most_active_list,
            "recent_conversations": [
                {
                    "conversation_id": conv.id,
                    "name": conv.name,
                    "user_name": user_name,
                    "user_email": user_email,
                    "message_count": conv.message_count,
                    "file_count": file_count or 0,
                    "last_activity": conv.last_activity,
                    "created_date": conv.create_date
                } for conv, user_name, user_email, file_count in recent
            ]
        }

        return conversation_stats, analytics

    def get_chat_usage_stats(self) -> Dict[str, Any]:
        """Get chat usage statistics"""
        
        # Daily stats for last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        daily_stats = self.db.query(
            func.date(Conversation.create_date).label('date'),
            func.count(Conversation.id).label('conversations'),
            func.sum(Conversation.message_count).label('messages')
        ).filter(
            and_(Conversation.create_date >= thirty_days_ago, Conversation.is_deleted == False)
        ).group_by(func.date(Conversation.create_date)).order_by('date').all()

        # Hourly distribution
        hourly_stats = self.db.query(
            func.extract('hour', Message.timestamp).label('hour'),
            func.count(Message.id).label('message_count')
        ).filter(Message.is_deleted == False).group_by(
            func.extract('hour', Message.timestamp)
        ).order_by('hour').all()

        # User engagement metrics
        user_engagement = self.db.query(
            func.avg(Conversation.message_count).label('avg_messages_per_conversation'),
            func.max(Conversation.message_count).label('max_messages_in_conversation'),
            func.count(func.distinct(Conversation.user_id)).label('active_users')
        ).filter(Conversation.is_deleted == False).first()

        return {
            "daily_stats": [
                {
                    "date": str(date),
                    "conversations": conversations,
                    "messages": messages or 0
                } for date, conversations, messages in daily_stats
            ],
            "hourly_distribution": [
                {
                    "hour": int(hour),
                    "message_count": count
                } for hour, count in hourly_stats
            ],
            "user_engagement": {
                "avg_messages_per_conversation": float(user_engagement.avg_messages_per_conversation or 0),
                "max_messages_in_conversation": user_engagement.max_messages_in_conversation or 0,
                "active_users": user_engagement.active_users or 0
            }
        }

    # File Analytics
    def get_file_analytics(self, page: int = 1, page_size: int = 20) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Get file analytics"""
        
        # Get files with user info
        files_query = self.db.query(
            File,
            User.name,
            User.email
        ).join(User, File.user_id == User.id)\
         .filter(File.is_deleted == False)\
         .order_by(desc(File.upload_date))

        total_files = files_query.count()
        
        # Get paginated results
        offset = (page - 1) * page_size
        files = files_query.offset(offset).limit(page_size).all()

        file_stats = []
        for file, user_name, user_email in files:
            file_stats.append({
                "file_id": file.id,
                "name": file.name,
                "original_name": file.original_name,
                "type": file.type,
                "size": file.size,
                "user_name": user_name,
                "user_email": user_email,
                "download_count": file.download_count or 0,
                "upload_date": file.upload_date,
                "is_indexed": file.is_indexed
            })

        # File type distribution
        file_type_distribution = dict(self.db.query(
            File.type,
            func.count(File.id)
        ).filter(File.is_deleted == False).group_by(File.type).all())

        # Total size
        total_size = self.db.query(func.sum(File.size)).filter(
            File.is_deleted == False
        ).scalar() or 0

        # Recent uploads (last 10)
        recent_uploads = files[:10]
        recent_list = [
            {
                "file_id": file.id,
                "name": file.name,
                "original_name": file.original_name,
                "type": file.type,
                "size": file.size,
                "user_name": user_name,
                "user_email": user_email,
                "download_count": file.download_count or 0,
                "upload_date": file.upload_date,
                "is_indexed": file.is_indexed
            } for file, user_name, user_email in recent_uploads
        ]

        # Most downloaded files
        most_downloaded = self.db.query(
            File,
            User.name,
            User.email
        ).join(User, File.user_id == User.id)\
         .filter(File.is_deleted == False)\
         .order_by(desc(File.download_count))\
         .limit(10).all()

        most_downloaded_list = [
            {
                "file_id": file.id,
                "name": file.name,
                "original_name": file.original_name,
                "type": file.type,
                "size": file.size,
                "user_name": user_name,
                "user_email": user_email,
                "download_count": file.download_count or 0,
                "upload_date": file.upload_date,
                "is_indexed": file.is_indexed
            } for file, user_name, user_email in most_downloaded
        ]

        analytics = {
            "total_files": total_files,
            "total_size": total_size,
            "file_type_distribution": file_type_distribution,
            "recent_uploads": recent_list,
            "most_downloaded": most_downloaded_list
        }

        return file_stats, analytics

    # Question Session Analytics
    def get_session_analytics(self, page: int = 1, page_size: int = 20) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Get question session analytics"""
        
        # Get sessions with user info and answer counts
        sessions_query = self.db.query(
            QuestionSession,
            User.name,
            User.email,
            func.count(QuestionAnswer.id.distinct()).label('answer_count')
        ).join(User, QuestionSession.user_id == User.id)\
         .outerjoin(QuestionAnswer, QuestionSession.id == QuestionAnswer.session_id)\
         .filter(QuestionSession.is_deleted == False)\
         .group_by(QuestionSession.id, User.name, User.email)\
         .order_by(desc(QuestionSession.create_date))

        total_sessions = sessions_query.count()
        
        # Get paginated results
        offset = (page - 1) * page_size
        sessions = sessions_query.offset(offset).limit(page_size).all()

        session_stats = []
        for session, user_name, user_email, answer_count in sessions:
            # Calculate completion rate
            questions_count = len(session.questions_data) if session.questions_data else 0
            completion_rate = (answer_count / questions_count * 100) if questions_count > 0 else 0

            session_stats.append({
                "session_id": session.id,
                "name": session.name,
                "user_name": user_name,
                "user_email": user_email,
                "session_type": session.session_type,
                "session_status": session.session_status,
                "questions_count": questions_count,
                "answers_count": answer_count or 0,
                "completion_rate": completion_rate,
                "start_date": session.start_date,
                "completion_date": session.completion_date,
                "created_date": session.create_date
            })

        # Overall completion rate
        total_completed = self.db.query(QuestionSession).filter(
            and_(QuestionSession.session_status == 'completed', QuestionSession.is_deleted == False)
        ).count()
        overall_completion_rate = (total_completed / total_sessions * 100) if total_sessions > 0 else 0

        # Session type distribution
        session_type_distribution = dict(self.db.query(
            QuestionSession.session_type,
            func.count(QuestionSession.id)
        ).filter(QuestionSession.is_deleted == False).group_by(QuestionSession.session_type).all())

        # Status distribution
        status_distribution = dict(self.db.query(
            QuestionSession.session_status,
            func.count(QuestionSession.id)
        ).filter(QuestionSession.is_deleted == False).group_by(QuestionSession.session_status).all())

        # Recent sessions
        recent_sessions = session_stats[:5]

        analytics = {
            "total_sessions": total_sessions,
            "completion_rate": overall_completion_rate,
            "session_type_distribution": session_type_distribution,
            "status_distribution": status_distribution,
            "recent_sessions": recent_sessions
        }

        return session_stats, analytics

    # Agent Analytics
    def get_agent_analytics(self, page: int = 1, page_size: int = 20) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Get agent analytics"""
        
        # Get agents with owner info
        agents_query = self.db.query(
            Agent,
            User.name.label('owner_name')
        ).outerjoin(User, Agent.user_id == User.id)\
         .filter(Agent.is_deleted == False)\
         .order_by(desc(Agent.create_date))

        total_agents = agents_query.count()
        
        # Get paginated results
        offset = (page - 1) * page_size
        agents = agents_query.offset(offset).limit(page_size).all()

        agent_stats = []
        for agent, owner_name in agents:
            # TODO: Add usage count from conversation logs or message logs
            usage_count = 0  # This would require joining with conversation/message tables
            
            agent_stats.append({
                "agent_id": agent.id,
                "name": agent.name,
                "description": agent.description,
                "model_provider": agent.model_provider.value,
                "model_name": agent.model_name,
                "is_active": agent.is_active,
                "usage_count": usage_count,
                "owner_name": owner_name,
                "created_date": agent.create_date
            })

        # Active agents count
        active_agents = self.db.query(Agent).filter(
            and_(Agent.is_active == True, Agent.is_deleted == False)
        ).count()

        # Provider distribution
        provider_distribution = dict(self.db.query(
            Agent.model_provider,
            func.count(Agent.id)
        ).filter(Agent.is_deleted == False).group_by(Agent.model_provider).all())

        # Model distribution
        model_distribution = dict(self.db.query(
            Agent.model_name,
            func.count(Agent.id)
        ).filter(Agent.is_deleted == False).group_by(Agent.model_name).all())

        analytics = {
            "total_agents": total_agents,
            "active_agents": active_agents,
            "provider_distribution": {str(k): v for k, v in provider_distribution.items()},
            "model_distribution": model_distribution
        }

        return agent_stats, analytics

    # Activity Logs
    def get_activity_logs(self, page: int = 1, page_size: int = 20,
                         user_id: Optional[str] = None, action: Optional[str] = None,
                         start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Tuple[List[Dict[str, Any]], int]:
        """Get activity logs"""
        
        query = self.db.query(
            UserLog,
            User.name,
            User.email
        ).join(User, UserLog.user_id == User.id)\
         .filter(UserLog.is_deleted == False)

        # Apply filters
        if user_id:
            query = query.filter(UserLog.user_id == user_id)
        if action:
            query = query.filter(UserLog.action.ilike(f"%{action}%"))
        if start_date:
            query = query.filter(UserLog.create_date >= start_date)
        if end_date:
            query = query.filter(UserLog.create_date <= end_date)

        query = query.order_by(desc(UserLog.create_date))

        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        logs = query.offset(offset).limit(page_size).all()

        activity_logs = []
        for log, user_name, user_email in logs:
            activity_logs.append({
                "log_id": log.id,
                "user_name": user_name,
                "user_email": user_email,
                "action": log.action,
                "details": log.details,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "created_date": log.create_date
            })

        return activity_logs, total_count

    # Recent Activity
    def get_recent_activity(self, limit: int = 5) -> Dict[str, Any]:
        """Get recent activity across all modules"""
        
        # Recent users
        recent_users = self.db.query(User).filter(
            User.is_deleted == False
        ).order_by(desc(User.create_date)).limit(limit).all()

        # Recent conversations
        recent_conversations = self.db.query(
            Conversation,
            User.name,
            User.email
        ).join(User, Conversation.user_id == User.id)\
         .filter(Conversation.is_deleted == False)\
         .order_by(desc(Conversation.create_date)).limit(limit).all()

        # Recent files
        recent_files = self.db.query(
            File,
            User.name,
            User.email
        ).join(User, File.user_id == User.id)\
         .filter(File.is_deleted == False)\
         .order_by(desc(File.upload_date)).limit(limit).all()

        # Recent payments
        recent_payments = self.db.query(
            Payment,
            User.name,
            User.email
        ).outerjoin(User, Payment.user_id == User.id)\
         .filter(Payment.is_deleted == False)\
         .order_by(desc(Payment.created_at)).limit(limit).all()

        # Recent sessions
        recent_sessions = self.db.query(
            QuestionSession,
            User.name,
            User.email
        ).join(User, QuestionSession.user_id == User.id)\
         .filter(QuestionSession.is_deleted == False)\
         .order_by(desc(QuestionSession.create_date)).limit(limit).all()

        return {
            "recent_users": [
                {
                    "user_id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "role": user.role,
                    "rank": user.rank,
                    "total_conversations": 0,  # Would need additional query
                    "total_messages": 0,  # Would need additional query
                    "total_files": 0,  # Would need additional query
                    "last_activity": user.last_login_at,
                    "join_date": user.create_date
                } for user in recent_users
            ],
            "recent_conversations": [
                {
                    "conversation_id": conv.id,
                    "name": conv.name,
                    "user_name": user_name,
                    "user_email": user_email,
                    "message_count": conv.message_count,
                    "file_count": 0,  # Would need additional query
                    "last_activity": conv.last_activity,
                    "created_date": conv.create_date
                } for conv, user_name, user_email in recent_conversations
            ],
            "recent_files": [
                {
                    "file_id": file.id,
                    "name": file.name,
                    "original_name": file.original_name,
                    "type": file.type,
                    "size": file.size,
                    "user_name": user_name,
                    "user_email": user_email,
                    "download_count": file.download_count or 0,
                    "upload_date": file.upload_date,
                    "is_indexed": file.is_indexed
                } for file, user_name, user_email in recent_files
            ],
            "recent_payments": [
                {
                    "payment_id": payment.id,
                    "order_code": payment.order_code,
                    "amount": payment.amount / 100,  # Convert from cents
                    "status": payment.status.value if payment.status else None,
                    "user_name": user_name,
                    "user_email": user_email,
                    "created_at": payment.created_at
                } for payment, user_name, user_email in recent_payments
            ],
            "recent_sessions": [
                {
                    "session_id": session.id,
                    "name": session.name,
                    "user_name": user_name,
                    "user_email": user_email,
                    "session_type": session.session_type,
                    "session_status": session.session_status,
                    "questions_count": len(session.questions_data) if session.questions_data else 0,
                    "answers_count": 0,  # Would need additional query
                    "completion_rate": 0,  # Would need additional query
                    "start_date": session.start_date,
                    "completion_date": session.completion_date,
                    "created_date": session.create_date
                } for session, user_name, user_email in recent_sessions
            ]
        }

    # System Health
    def get_system_health(self) -> Dict[str, Any]:
        """Get system health metrics"""
        
        try:
            # Test database connection
            self.db.execute(text("SELECT 1"))
            database_status = "healthy"
        except Exception:
            database_status = "unhealthy"

        # Count records in each table
        record_counts = {
            "users": self.db.query(User).count(),
            "conversations": self.db.query(Conversation).count(),
            "messages": self.db.query(Message).count(),
            "files": self.db.query(File).count(),
            "payments": self.db.query(Payment).count(),
            "orders": self.db.query(Order).count(),
            "question_sessions": self.db.query(QuestionSession).count(),
            "question_answers": self.db.query(QuestionAnswer).count(),
            "agents": self.db.query(Agent).count(),
            "global_kb": self.db.query(GlobalKB).count(),
            "user_logs": self.db.query(UserLog).count()
        }

        # Storage info
        total_file_size = self.db.query(func.sum(File.size)).scalar() or 0
        indexed_files = self.db.query(File).filter(File.is_indexed == True).count()
        total_files = self.db.query(File).count()
        indexing_rate = (indexed_files / total_files * 100) if total_files > 0 else 0

        storage_info = {
            "total_file_size": total_file_size,
            "total_files": total_files,
            "indexed_files": indexed_files,
            "indexing_rate": indexing_rate
        }

        # Performance metrics
        performance_metrics = {
            "avg_messages_per_conversation": 0,  # Would need calculation
            "avg_files_per_user": total_files / record_counts["users"] if record_counts["users"] > 0 else 0,
            "completion_rate": 0  # Would need calculation
        }

        return {
            "database_status": database_status,
            "total_records": record_counts,
            "storage_info": storage_info,
            "performance_metrics": performance_metrics,
            "last_updated": datetime.utcnow()
        }
