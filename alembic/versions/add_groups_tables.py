"""Add groups and group_members tables

Revision ID: add_groups_tables
Revises: cf6752638ff4
Create Date: 2025-05-20 15:40:22.123456

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mysql import TINYINT


# revision identifiers, used by Alembic.
revision = 'add_groups_tables'
down_revision = 'cf6752638ff4'  # Update this to your actual latest migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create groups table
    op.create_table(
        'groups',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(36), nullable=False),
        sa.Column('create_date', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('update_date', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('is_active', TINYINT(1), nullable=False, default=1),
        sa.Column('is_public', TINYINT(1), nullable=False, default=0),
        sa.Column('is_deleted', TINYINT(1), nullable=False, default=0),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_groups_created_by'),
        sa.Index('idx_groups_created_by', 'created_by')
    )
    
    # Create group_members table
    op.create_table(
        'group_members',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('group_id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('role', sa.Enum('LEADER', 'MEMBER', name='groupmemberrole'), nullable=False, default='MEMBER'),
        sa.Column('join_status', sa.Enum('PENDING', 'ACCEPTED', 'REJECTED', name='groupmemberjoinstatus'), nullable=False, default='PENDING'),
        sa.Column('invited_by', sa.String(36), nullable=True),
        sa.Column('invited_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('responded_at', sa.DateTime(), nullable=True),
        sa.Column('create_date', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('update_date', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('is_deleted', TINYINT(1), nullable=False, default=0),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id'], name='fk_gm_group'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_gm_user'),
        sa.ForeignKeyConstraint(['invited_by'], ['users.id'], name='fk_gm_inviter'),
        sa.Index('idx_gm_group', 'group_id'),
        sa.Index('idx_gm_user', 'user_id')
    )
    
    # Add group_id to meetings table
    op.add_column('meetings',
        sa.Column('group_id', sa.String(36), nullable=True)
    )
    op.create_foreign_key(
        'fk_meetings_group',
        'meetings', 'groups',
        ['group_id'], ['id']
    )
    op.create_index('idx_meetings_group', 'meetings', ['group_id'])


def downgrade() -> None:
    # Drop foreign key and column from meetings table
    op.drop_constraint('fk_meetings_group', 'meetings', type_='foreignkey')
    op.drop_index('idx_meetings_group', table_name='meetings')
    op.drop_column('meetings', 'group_id')
    
    # Drop group_members table
    op.drop_table('group_members')
    
    # Drop types created for enums
    op.execute("DROP TYPE IF EXISTS groupmemberrole")
    op.execute("DROP TYPE IF EXISTS groupmemberjoinstatus")
    
    # Drop groups table
    op.drop_table('groups')
