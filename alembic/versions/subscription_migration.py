"""Add subscription tables

Revision ID: subscription_migration
Revises: payment_migration
Create Date: 2025-07-27 10:00:00

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime
import uuid


# revision identifiers, used by Alembic.
revision = 'subscription_migration'
down_revision = 'payment_migration'
branch_labels = None
depends_on = None


def upgrade():
    # Create ranks table
    op.create_table(
        'ranks',
        sa.Column('id', sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column('create_date', sa.DateTime(timezone=True), default=datetime.now),
        sa.Column('update_date', sa.DateTime(timezone=True), onupdate=datetime.now),
        sa.Column('is_deleted', sa.Boolean, default=False),
        sa.Column('name', sa.Enum('basic', 'enterviu_pro', 'enterviu_ultra', name='rankenum'), nullable=False, unique=True),
        sa.Column('description', sa.String(500), nullable=False),
        sa.Column('benefits', sa.JSON, nullable=False),
        sa.Column('price', sa.String(20), nullable=False)
    )
    
    # Create subscription orders table
    op.create_table(
        'subscription_orders',
        sa.Column('id', sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column('create_date', sa.DateTime(timezone=True), default=datetime.now),
        sa.Column('update_date', sa.DateTime(timezone=True), onupdate=datetime.now),
        sa.Column('is_deleted', sa.Boolean, default=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('order_code', sa.String(50), nullable=False, unique=True),
        sa.Column('rank_type', sa.Enum('basic', 'enterviu_pro', 'enterviu_ultra', name='rankenum'), nullable=False),
        sa.Column('amount', sa.Float, nullable=False),
        sa.Column('status', sa.Enum('pending', 'completed', 'canceled', 'expired', name='orderstatusenum'), nullable=False),
        sa.Column('payment_link_id', sa.String(100), nullable=True),
        sa.Column('checkout_url', sa.String(500), nullable=True),
        sa.Column('transaction_id', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime, default=datetime.now),
        sa.Column('expired_at', sa.DateTime, nullable=False),
        sa.Column('activated_at', sa.DateTime, nullable=True),
        sa.Column('expired_subscription_at', sa.DateTime, nullable=True),
        sa.Column('cancel_reason', sa.String(255), nullable=True),
    )
    
    # Create indexes
    op.create_index('idx_subscription_orders_user_id', 'subscription_orders', ['user_id'])
    op.create_index('idx_subscription_orders_order_code', 'subscription_orders', ['order_code'])
    op.create_index('idx_subscription_orders_status', 'subscription_orders', ['status'])
    
    # Add subscription-related columns to users table
    op.add_column('users', sa.Column('rank', sa.Enum('basic', 'enterviu_pro', 'enterviu_ultra', name='rankenum'), 
                                     nullable=False, server_default='basic'))
    op.add_column('users', sa.Column('rank_activated_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('rank_expired_at', sa.DateTime(timezone=True), nullable=True))


def downgrade():
    # Remove subscription-related columns from users table
    op.drop_column('users', 'rank_expired_at')
    op.drop_column('users', 'rank_activated_at')
    op.drop_column('users', 'rank')
    
    # Drop tables
    op.drop_table('subscription_orders')
    op.drop_table('ranks')
    
    # Drop enums
    op.execute('DROP TYPE rankenum')
    op.execute('DROP TYPE orderstatusenum')
