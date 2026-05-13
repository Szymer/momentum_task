"""convert identifiers to fixed 6-char strings

Revision ID: 0003_id_str6
Revises: 0002_reader_card_fk
Create Date: 2026-05-13 13:30:00.000000

"""

# revision identifiers, used by Alembic.
revision = "0003_id_str6"
down_revision = "0002_reader_card_fk"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Initial revision 0001 now creates the final schema directly.
    pass


def downgrade() -> None:
    pass
