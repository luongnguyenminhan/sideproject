"""calendar_meeting_sync_migration
Add meeting_link and organizer fields to meetings table

Revision ID: calendar_meeting_sync
Revises: a625265e8ecb
Create Date: 2025-04-25

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = 'calendar_meeting_sync'
down_revision = 'a625265e8ecb'
branch_labels = None
depends_on = None


def upgrade():
    # Add meeting_link column to meetings table if it doesn't exist
    op.execute("""
    ALTER TABLE meetings 
    ADD COLUMN IF NOT EXISTS meeting_link VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS organizer_email VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS organizer_name VARCHAR(255) NULL;
    """)
    
    # Ensure calendar_events table has meeting_id foreign key
    op.execute("""
    ALTER TABLE calendar_events
    MODIFY COLUMN meeting_id VARCHAR(36) NULL,
    ADD CONSTRAINT IF NOT EXISTS fk_calendar_event_meeting
    FOREIGN KEY (meeting_id) REFERENCES meetings(id)
    ON DELETE SET NULL;
    """)


def downgrade():
    # Remove columns from meetings table
    op.drop_column('meetings', 'meeting_link')
    op.drop_column('meetings', 'organizer_email')
    op.drop_column('meetings', 'organizer_name')
    
    # Remove foreign key constraint
    op.execute("""
    ALTER TABLE calendar_events
    DROP FOREIGN KEY IF EXISTS fk_calendar_event_meeting;
    """)