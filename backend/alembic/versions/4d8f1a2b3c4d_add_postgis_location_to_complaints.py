"""add_postgis_location_to_complaints

Revision ID: 4d8f1a2b3c4d
Revises: 3a7f8e91d012
Create Date: 2026-09-11 16:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision: str = '4d8f1a2b3c4d'
down_revision: Union[str, None] = '3a7f8e91d012'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Enable PostGIS extension
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis;")

    # 2. Add location column (POINT, SRID 4326) and location_source
    op.add_column(
        'complaints',
        sa.Column(
            'location',
            geoalchemy2.types.Geometry(geometry_type='POINT', srid=4326, from_text=False),
            nullable=True,
        )
    )
    op.add_column(
        'complaints',
        sa.Column('location_source', sa.String(length=50), server_default='MANUAL', nullable=False)
    )

    # 3. Backfill location from legacy latitude/longitude if data exists
    op.execute(
        "UPDATE complaints SET location = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326) WHERE location IS NULL;"
    )

    # 4. Enforce NOT NULL on location
    op.alter_column('complaints', 'location', nullable=False)

    # 5. Create spatial GiST index
    op.create_index('ix_complaints_location', 'complaints', ['location'], postgresql_using='gist')

    # 6. Drop redundant persistent latitude/longitude columns and constraints
    op.drop_constraint('chk_complaint_latitude', 'complaints', type_='check')
    op.drop_constraint('chk_complaint_longitude', 'complaints', type_='check')
    op.drop_column('complaints', 'latitude')
    op.drop_column('complaints', 'longitude')


def downgrade() -> None:
    # 1. Re-add latitude and longitude columns
    op.add_column('complaints', sa.Column('latitude', sa.Numeric(precision=9, scale=6), nullable=True))
    op.add_column('complaints', sa.Column('longitude', sa.Numeric(precision=9, scale=6), nullable=True))

    # 2. Populate latitude and longitude from PostGIS location
    op.execute("UPDATE complaints SET latitude = ST_Y(location), longitude = ST_X(location);")

    # 3. Restore constraints and NOT NULL
    op.alter_column('complaints', 'latitude', nullable=False)
    op.alter_column('complaints', 'longitude', nullable=False)
    op.create_check_constraint('chk_complaint_latitude', 'complaints', 'latitude >= -90.0 AND latitude <= 90.0')
    op.create_check_constraint('chk_complaint_longitude', 'complaints', 'longitude >= -180.0 AND longitude <= 180.0')

    # 4. Drop spatial index and location columns
    op.drop_index('ix_complaints_location', table_name='complaints')
    op.drop_column('complaints', 'location_source')
    op.drop_column('complaints', 'location')
