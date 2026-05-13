"""add borrow_time to books

Revision ID: 0002_add_borrow_time_to_books
Revises: 0001_create_library_tables
Create Date: 2026-05-13 00:10:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0002_add_borrow_time_to_books"
down_revision = "0001_create_library_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("books", sa.Column("borrow_time", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("books", "borrow_time")
