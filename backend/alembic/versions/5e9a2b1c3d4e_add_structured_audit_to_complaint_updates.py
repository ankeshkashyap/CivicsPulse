"""add_structured_audit_to_complaint_updates

Revision ID: 5e9a2b1c3d4e
Revises: 4d8f1a2b3c4d
Create Date: 2026-09-11 18:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '5e9a2b1c3d4e'
down_revision: Union[str, None] = '4d8f1a2b3c4d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create complaint_action_type enum type
    complaint_action_type = postgresql.ENUM(
        'STATUS_CHANGE',
        'SEVERITY_CHANGE',
        'DEPARTMENT_ASSIGNMENT',
        'PROGRESS_REMARK',
        name='complaint_action_type',
        create_type=False,
    )
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        complaint_action_type.create(bind, checkfirst=True)

    # 2. Add structured audit columns to complaint_updates
    op.add_column(
        'complaint_updates',
        sa.Column(
            'action_type',
            sa.Enum('STATUS_CHANGE', 'SEVERITY_CHANGE', 'DEPARTMENT_ASSIGNMENT', 'PROGRESS_REMARK', name='complaint_action_type'),
            server_default='STATUS_CHANGE',
            nullable=False,
        ),
    )
    op.add_column(
        'complaint_updates',
        sa.Column(
            'old_severity',
            sa.Enum('LOW', 'MEDIUM', 'HIGH', name='complaint_severity'),
            nullable=True,
        ),
    )
    op.add_column(
        'complaint_updates',
        sa.Column(
            'new_severity',
            sa.Enum('LOW', 'MEDIUM', 'HIGH', name='complaint_severity'),
            nullable=True,
        ),
    )
    op.add_column(
        'complaint_updates',
        sa.Column('old_department_id', sa.Uuid(), nullable=True),
    )
    op.add_column(
        'complaint_updates',
        sa.Column('new_department_id', sa.Uuid(), nullable=True),
    )

    # 3. Add foreign key constraints
    op.create_foreign_key(
        'fk_complaint_updates_old_department_id',
        'complaint_updates',
        'departments',
        ['old_department_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.create_foreign_key(
        'fk_complaint_updates_new_department_id',
        'complaint_updates',
        'departments',
        ['new_department_id'],
        ['id'],
        ondelete='SET NULL',
    )


def downgrade() -> None:
    op.drop_constraint('fk_complaint_updates_new_department_id', 'complaint_updates', type_='foreignkey')
    op.drop_constraint('fk_complaint_updates_old_department_id', 'complaint_updates', type_='foreignkey')
    op.drop_column('complaint_updates', 'new_department_id')
    op.drop_column('complaint_updates', 'old_department_id')
    op.drop_column('complaint_updates', 'new_severity')
    op.drop_column('complaint_updates', 'old_severity')
    op.drop_column('complaint_updates', 'action_type')

    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        sa.Enum(name='complaint_action_type').drop(bind, checkfirst=True)
