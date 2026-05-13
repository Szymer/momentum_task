"""create library tables

Revision ID: 0001_create_library_tables
Revises:
Create Date: 2026-05-13 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0001_create_library_tables"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "editions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("isbn", sa.String(length=32), nullable=False, unique=True),
        sa.Column("author", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
    )

    op.create_table(
        "readers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("library_card_number", sa.String(length=6), nullable=False, unique=True),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.CheckConstraint(
            "length(library_card_number) = 6",
            name="ck_readers_library_card_number_six_digits",
        ),
    )

    op.create_table(
        "books",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("serial_number", sa.String(length=6), nullable=False, unique=True),
        sa.Column("available", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("edition_id", sa.Integer(), sa.ForeignKey("editions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column(
            "library_card_number",
            sa.String(length=6),
            sa.ForeignKey("readers.library_card_number", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.CheckConstraint(
            "length(serial_number) = 6",
            name="ck_books_serial_number_six_digits",
        ),
    )

    op.create_index("ix_books_available", "books", ["available"])
    op.create_index("ix_books_edition_id", "books", ["edition_id"])
    op.create_index("ix_books_library_card_number", "books", ["library_card_number"])
    op.create_index("ix_books_serial_number", "books", ["serial_number"])


def downgrade() -> None:
    op.drop_index("ix_books_available", table_name="books")
    op.drop_index("ix_books_serial_number", table_name="books")
    op.drop_index("ix_books_library_card_number", table_name="books")
    op.drop_index("ix_books_edition_id", table_name="books")
    op.drop_table("books")
    op.drop_table("readers")
    op.drop_table("editions")
