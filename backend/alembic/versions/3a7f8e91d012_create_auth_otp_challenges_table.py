"""create_auth_otp_challenges_table

Revision ID: 3a7f8e91d012
Revises: 21e2c13b255e
Create Date: 2026-09-11 05:10:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '3a7f8e91d012'
down_revision: Union[str, None] = '21e2c13b255e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'auth_otp_challenges',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('otp_hash', sa.String(length=255), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_attempts', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('consumed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('request_ip_hash', sa.String(length=64), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('last_attempt_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_auth_otp_challenges_email'), 'auth_otp_challenges', ['email'], unique=False)
    op.create_index(op.f('ix_auth_otp_challenges_expires_at'), 'auth_otp_challenges', ['expires_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_auth_otp_challenges_expires_at'), table_name='auth_otp_challenges')
    op.drop_index(op.f('ix_auth_otp_challenges_email'), table_name='auth_otp_challenges')
    op.drop_table('auth_otp_challenges')
