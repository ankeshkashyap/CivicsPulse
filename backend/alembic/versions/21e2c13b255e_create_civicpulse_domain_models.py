"""create_civicpulse_domain_models

Revision ID: 21e2c13b255e
Revises: 
Create Date: 2026-09-11 04:48:20.058269

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '21e2c13b255e'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Define Enums
user_role_enum = sa.Enum('CITIZEN', 'ADMIN', name='user_role')
complaint_category_enum = sa.Enum(
    'ROADS', 'STREETLIGHTS', 'GARBAGE', 'DRAINAGE', 'WATER',
    'SEWERAGE', 'TRAFFIC', 'PUBLIC_SAFETY', 'PARKS', 'OTHER',
    name='complaint_category'
)
complaint_severity_enum = sa.Enum('LOW', 'MEDIUM', 'HIGH', name='complaint_severity')
complaint_status_enum = sa.Enum(
    'SUBMITTED', 'UNDER_REVIEW', 'ASSIGNED', 'IN_PROGRESS', 'RESOLVED', 'REJECTED',
    name='complaint_status'
)


def upgrade() -> None:
    # 1. Cities Table
    op.create_table(
        'cities',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('state', sa.String(length=100), nullable=False),
        sa.Column('country', sa.String(length=100), server_default='India', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', 'state', 'country', name='uq_cities_name_state_country')
    )
    op.create_index('ix_cities_name', 'cities', ['name'], unique=False)

    # 2. Departments Table
    op.create_table(
        'departments',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('city_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['city_id'], ['cities.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('city_id', 'name', name='uq_departments_city_id_name')
    )
    op.create_index('ix_departments_city_id', 'departments', ['city_id'], unique=False)

    # 3. Users Table
    op.create_table(
        'users',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('city_id', sa.Uuid(), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=150), nullable=True),
        sa.Column('role', user_role_enum, nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('is_verified', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['city_id'], ['cities.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email', name='uq_users_email')
    )
    op.create_index('ix_users_city_id', 'users', ['city_id'], unique=False)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_role', 'users', ['role'], unique=False)

    # 4. Complaints Table
    op.create_table(
        'complaints',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('city_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('department_id', sa.Uuid(), nullable=True),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', complaint_category_enum, nullable=False),
        sa.Column('severity', complaint_severity_enum, nullable=False),
        sa.Column('status', complaint_status_enum, nullable=False),
        sa.Column('latitude', sa.Numeric(precision=9, scale=6), nullable=False),
        sa.Column('longitude', sa.Numeric(precision=9, scale=6), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint('latitude >= -90.0 AND latitude <= 90.0', name='chk_complaint_latitude'),
        sa.CheckConstraint('longitude >= -180.0 AND longitude <= 180.0', name='chk_complaint_longitude'),
        sa.ForeignKeyConstraint(['city_id'], ['cities.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_complaints_city_id', 'complaints', ['city_id'], unique=False)
    op.create_index('ix_complaints_user_id', 'complaints', ['user_id'], unique=False)
    op.create_index('ix_complaints_department_id', 'complaints', ['department_id'], unique=False)
    op.create_index('ix_complaints_category', 'complaints', ['category'], unique=False)
    op.create_index('ix_complaints_severity', 'complaints', ['severity'], unique=False)
    op.create_index('ix_complaints_status', 'complaints', ['status'], unique=False)
    op.create_index('ix_complaints_created_at', 'complaints', ['created_at'], unique=False)

    # 5. Complaint Images Table
    op.create_table(
        'complaint_images',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('complaint_id', sa.Uuid(), nullable=False),
        sa.Column('image_url', sa.String(length=1024), nullable=False),
        sa.Column('public_id', sa.String(length=255), nullable=False),
        sa.Column('latitude', sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column('longitude', sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            'latitude IS NULL OR (latitude >= -90.0 AND latitude <= 90.0)',
            name='chk_image_latitude'
        ),
        sa.CheckConstraint(
            'longitude IS NULL OR (longitude >= -180.0 AND longitude <= 180.0)',
            name='chk_image_longitude'
        ),
        sa.ForeignKeyConstraint(['complaint_id'], ['complaints.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_complaint_images_complaint_id', 'complaint_images', ['complaint_id'], unique=False)

    # 6. Complaint Updates Table
    op.create_table(
        'complaint_updates',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('complaint_id', sa.Uuid(), nullable=False),
        sa.Column('updated_by_user_id', sa.Uuid(), nullable=True),
        sa.Column('old_status', complaint_status_enum, nullable=True),
        sa.Column('new_status', complaint_status_enum, nullable=False),
        sa.Column('remark', sa.Text(), nullable=True),
        sa.Column('progress_percentage', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            'progress_percentage >= 0 AND progress_percentage <= 100',
            name='chk_update_progress_percentage'
        ),
        sa.ForeignKeyConstraint(['complaint_id'], ['complaints.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['updated_by_user_id'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_complaint_updates_complaint_id', 'complaint_updates', ['complaint_id'], unique=False)
    op.create_index('ix_complaint_updates_updated_by_user_id', 'complaint_updates', ['updated_by_user_id'], unique=False)
    op.create_index('ix_complaint_updates_created_at', 'complaint_updates', ['created_at'], unique=False)

    # 7. Upvotes Table
    op.create_table(
        'upvotes',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('complaint_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['complaint_id'], ['complaints.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('complaint_id', 'user_id', name='uq_upvotes_complaint_id_user_id')
    )
    op.create_index('ix_upvotes_complaint_id', 'upvotes', ['complaint_id'], unique=False)
    op.create_index('ix_upvotes_user_id', 'upvotes', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_table('upvotes')
    op.drop_table('complaint_updates')
    op.drop_table('complaint_images')
    op.drop_table('complaints')
    op.drop_table('users')
    op.drop_table('departments')
    op.drop_table('cities')

    # Drop enums
    complaint_status_enum.drop(op.get_bind(), checkfirst=True)
    complaint_severity_enum.drop(op.get_bind(), checkfirst=True)
    complaint_category_enum.drop(op.get_bind(), checkfirst=True)
    user_role_enum.drop(op.get_bind(), checkfirst=True)