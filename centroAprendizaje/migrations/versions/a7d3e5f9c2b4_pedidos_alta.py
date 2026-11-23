"""Artículos cuya alta ya se pidió en TIMBÓ (pedidos_alta).

Solo crea una tabla nueva: no toca datos.

Revision ID: a7d3e5f9c2b4
Revises: f2c6a9d3b8e1
"""
from alembic import op
import sqlalchemy as sa

revision = "a7d3e5f9c2b4"
down_revision = "f2c6a9d3b8e1"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "pedidos_alta",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("llave_id", sa.Integer(), sa.ForeignKey("llaves_servicio.id"), nullable=False),
        sa.Column("codigo_interno", sa.String(40), nullable=False, server_default=""),
        sa.Column("nombre", sa.String(500), nullable=False),
        sa.Column("sdo", sa.String(60), nullable=False, server_default=""),
        sa.Column("pedido_por", sa.String(120), nullable=False, server_default=""),
        sa.Column("pedido_en", sa.DateTime(), nullable=False),
        sa.Column("codigo_asignado", sa.String(40), nullable=False, server_default=""),
        sa.UniqueConstraint("llave_id", "nombre", name="uq_pedido_alta_llave_nombre"),
    )
    op.create_index("ix_pedidos_alta_llave_id", "pedidos_alta", ["llave_id"])
    op.create_index("ix_pedidos_alta_codigo_interno", "pedidos_alta", ["codigo_interno"])


def downgrade():
    op.drop_index("ix_pedidos_alta_codigo_interno", table_name="pedidos_alta")
    op.drop_index("ix_pedidos_alta_llave_id", table_name="pedidos_alta")
    op.drop_table("pedidos_alta")
