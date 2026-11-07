"""Add assignment uniqueness.

Revision ID: 9c2f0b5141a7
Revises: 624e696c0fae
"""

from alembic import op


revision = "9c2f0b5141a7"
down_revision = "624e696c0fae"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        DELETE FROM assignments older
        USING assignments newer
        WHERE older.id > newer.id
          AND older.user_id = newer.user_id
          AND older.event_id = newer.event_id
        """
    )
    with op.batch_alter_table("assignments", schema=None) as batch_op:
        batch_op.create_unique_constraint(
            "uq_assignment_user_event", ["user_id", "event_id"]
        )


def downgrade():
    with op.batch_alter_table("assignments", schema=None) as batch_op:
        batch_op.drop_constraint("uq_assignment_user_event", type_="unique")
