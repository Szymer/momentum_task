"""use library card number as reader identifier

Revision ID: 0002_reader_card_fk
Revises: 0001_create_library_tables
Create Date: 2026-05-13 12:00:00.000000

"""

# revision identifiers, used by Alembic.
revision = "0002_reader_card_fk"
down_revision = "0001_create_library_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # This revision is intentionally a no-op in the current branch state.
    # The actual type conversion to string identifiers is handled in 0003.
    pass


def downgrade() -> None:
    pass