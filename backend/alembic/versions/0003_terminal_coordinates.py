"""Add latitude and longitude to terminal

Revision ID: 0003_terminal_coordinates
Revises: 0002_route_dispatch
Create Date: 2026-07-01 00:30:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '0003_terminal_coordinates'
down_revision = '0002_route_dispatch'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('terminal', sa.Column('latitude', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('terminal', sa.Column('longitude', sa.Float(), nullable=False, server_default='0.0'))


def downgrade() -> None:
    op.drop_column('terminal', 'longitude')
    op.drop_column('terminal', 'latitude')
