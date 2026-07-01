"""Create initial database tables

Revision ID: 0001_create_tables
Revises: 
Create Date: 2026-06-25 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_create_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'terminal',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False, unique=True),
        sa.Column('zone', sa.String(), nullable=False),
    )
    op.create_index(op.f('ix_terminal_name'), 'terminal', ['name'], unique=False)

    op.create_table(
        'route',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('code', sa.String(), nullable=False, unique=True),
        sa.Column('origin', sa.String(), nullable=False),
        sa.Column('destination', sa.String(), nullable=False),
    )
    op.create_index(op.f('ix_route_code'), 'route', ['code'], unique=False)

    op.create_table(
        'user',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('username', sa.String(), nullable=False, unique=True),
        sa.Column('email', sa.String(), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.sql.expression.true()),
    )
    op.create_index(op.f('ix_user_username'), 'user', ['username'], unique=False)
    op.create_index(op.f('ix_user_email'), 'user', ['email'], unique=False)

    op.create_table(
        'weatherobservation',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('observed_date', sa.Date(), nullable=False),
        sa.Column('precipitation_mm', sa.Float(), nullable=False),
        sa.Column('condition', sa.String(), nullable=False),
        sa.Column('severe', sa.Boolean(), nullable=False),
    )
    op.create_index(op.f('ix_weatherobservation_observed_date'), 'weatherobservation', ['observed_date'], unique=False)

    op.create_table(
        'incident',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('report_time', sa.DateTime(), nullable=False),
        sa.Column('route_id', sa.Integer(), sa.ForeignKey('route.id'), nullable=True),
        sa.Column('terminal_id', sa.Integer(), sa.ForeignKey('terminal.id'), nullable=True),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('reported_by_id', sa.Integer(), sa.ForeignKey('user.id'), nullable=False),
    )
    op.create_index(op.f('ix_incident_report_time'), 'incident', ['report_time'], unique=False)
    op.create_index(op.f('ix_incident_route_id'), 'incident', ['route_id'], unique=False)
    op.create_index(op.f('ix_incident_terminal_id'), 'incident', ['terminal_id'], unique=False)
    op.create_index(op.f('ix_incident_reported_by_id'), 'incident', ['reported_by_id'], unique=False)

    op.create_table(
        'dispatchevent',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('route_id', sa.Integer(), sa.ForeignKey('route.id'), nullable=False),
        sa.Column('terminal_id', sa.Integer(), sa.ForeignKey('terminal.id'), nullable=False),
        sa.Column('dispatch_datetime', sa.DateTime(), nullable=False),
        sa.Column('scheduled_minutes', sa.Integer(), nullable=False),
        sa.Column('actual_minutes', sa.Integer(), nullable=False),
        sa.Column('passengers_boarded', sa.Integer(), nullable=False),
        sa.Column('on_time', sa.Boolean(), nullable=False),
    )
    op.create_index(op.f('ix_dispatchevent_dispatch_datetime'), 'dispatchevent', ['dispatch_datetime'], unique=False)
    op.create_index(op.f('ix_dispatchevent_route_id'), 'dispatchevent', ['route_id'], unique=False)
    op.create_index(op.f('ix_dispatchevent_terminal_id'), 'dispatchevent', ['terminal_id'], unique=False)
    op.create_index(op.f('ix_dispatchevent_on_time'), 'dispatchevent', ['on_time'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_dispatchevent_on_time'), table_name='dispatchevent')
    op.drop_index(op.f('ix_dispatchevent_terminal_id'), table_name='dispatchevent')
    op.drop_index(op.f('ix_dispatchevent_route_id'), table_name='dispatchevent')
    op.drop_index(op.f('ix_dispatchevent_dispatch_datetime'), table_name='dispatchevent')
    op.drop_table('dispatchevent')
    op.drop_index(op.f('ix_incident_reported_by_id'), table_name='incident')
    op.drop_index(op.f('ix_incident_terminal_id'), table_name='incident')
    op.drop_index(op.f('ix_incident_route_id'), table_name='incident')
    op.drop_index(op.f('ix_incident_report_time'), table_name='incident')
    op.drop_table('incident')
    op.drop_index(op.f('ix_weatherobservation_observed_date'), table_name='weatherobservation')
    op.drop_table('weatherobservation')
    op.drop_index(op.f('ix_user_email'), table_name='user')
    op.drop_index(op.f('ix_user_username'), table_name='user')
    op.drop_table('user')
    op.drop_index(op.f('ix_route_code'), table_name='route')
    op.drop_table('route')
    op.drop_index(op.f('ix_terminal_name'), table_name='terminal')
    op.drop_table('terminal')
