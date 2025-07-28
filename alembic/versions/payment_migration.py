"""Add Payment table

Revision ID: payment_migration
Revises: c3e76c20f3a6
Create Date: 2025-07-24 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'payment_migration'
down_revision = 'c3e76c20f3a6'  # Change this to your latest migration
branch_labels = None
depends_on = None


def upgrade():
    # Create payment table
    op.create_table(
        'payments',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('order_code', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('payment_link_id', sa.String(255), nullable=True),
        sa.Column('status', sa.Enum('created', 'pending', 'processing', 'completed', 'failed', 'cancelled', name='paymentstatus'), default='created'),
        sa.Column('checkout_url', sa.Text(), nullable=True),
        sa.Column('qr_code', sa.Text(), nullable=True),
        sa.Column('currency', sa.String(10), default='VND'),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('reference', sa.String(255), nullable=True),
        sa.Column('transaction_date_time', sa.DateTime(), nullable=True),
        sa.Column('counter_account_bank_id', sa.String(255), nullable=True),
        sa.Column('counter_account_bank_name', sa.String(255), nullable=True),
        sa.Column('counter_account_name', sa.String(255), nullable=True),
        sa.Column('counter_account_number', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
    )
    
    # Create indexes
    op.create_index('ix_payments_order_code', 'payments', ['order_code'])
    op.create_index('ix_payments_payment_link_id', 'payments', ['payment_link_id'])
    op.create_index('ix_payments_user_id', 'payments', ['user_id'])


def downgrade():
    # Drop payment table
    op.drop_index('ix_payments_user_id', 'payments')
    op.drop_index('ix_payments_payment_link_id', 'payments')
    op.drop_index('ix_payments_order_code', 'payments')
    op.drop_table('payments')
    op.execute('DROP TYPE paymentstatus')
