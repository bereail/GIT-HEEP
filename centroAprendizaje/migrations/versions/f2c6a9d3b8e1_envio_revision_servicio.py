"""Envío definitivo de la revisión por servicio (enviado_en / enviado_por).

Solo agrega columnas: no toca datos.

Revision ID: f2c6a9d3b8e1
Revises: e8b3c5d1a2f4
"""
from alembic import op
import sqlalchemy as sa

revision = "f2c6a9d3b8e1"
down_revision = "e8b3c5d1a2f4"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("llaves_servicio") as t:
        t.add_column(sa.Column("enviado_en", sa.DateTime(), nullable=True))
        t.add_column(sa.Column("enviado_por", sa.String(160), nullable=True))


def downgrade():
    with op.batch_alter_table("llaves_servicio") as t:
        t.drop_column("enviado_por")
        t.drop_column("enviado_en")
