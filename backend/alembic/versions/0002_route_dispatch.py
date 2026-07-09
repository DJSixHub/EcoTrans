"""Add route_type and enriched dispatch event columns

Revision ID: 0002_route_dispatch
Revises: 0001_create_tables
Create Date: 2026-07-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '0002_route_dispatch'
down_revision = '0001_create_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('route', sa.Column('route_type', sa.String(), nullable=False, server_default='Regular'))
    op.add_column('dispatchevent', sa.Column('planned_frequency_minutes', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('dispatchevent', sa.Column('route_type', sa.String(), nullable=False, server_default='Regular'))
    op.add_column('dispatchevent', sa.Column('service_level', sa.String(), nullable=False, server_default='Standard'))
    op.add_column('dispatchevent', sa.Column('day_type', sa.String(), nullable=False, server_default='weekday'))
    op.add_column('dispatchevent', sa.Column('peak_period', sa.String(), nullable=False, server_default='offpeak'))
    op.add_column('dispatchevent', sa.Column('vehicle_capacity', sa.Integer(), nullable=False, server_default='50'))
    op.add_column('dispatchevent', sa.Column('passenger_load_factor', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('dispatchevent', sa.Column('weather_condition', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('dispatchevent', 'weather_condition')
    op.drop_column('dispatchevent', 'passenger_load_factor')
    op.drop_column('dispatchevent', 'vehicle_capacity')
    op.drop_column('dispatchevent', 'peak_period')
    op.drop_column('dispatchevent', 'day_type')
    op.drop_column('dispatchevent', 'service_level')
    op.drop_column('dispatchevent', 'route_type')
    op.drop_column('dispatchevent', 'planned_frequency_minutes')
    op.drop_column('route', 'route_type')
