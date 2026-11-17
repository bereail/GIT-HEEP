"""revisión del nomenclador: respuesta sí / no / dudas

Solo agrega una columna opcional (validacion) a las observaciones y a su
historial. Las observaciones existentes quedan igual, sin respuesta.

Revision ID: 8a3c4d2e1f07
Revises: 5e1f0a7c2b90
Create Date: 2026-11-17 10:00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8a3c4d2e1f07'
down_revision = '5e1f0a7c2b90'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('observaciones_nomenclador', schema=None) as batch_op:
        batch_op.add_column(sa.Column('validacion', sa.String(length=10), nullable=True))
    with op.batch_alter_table('observaciones_nomenclador_historial', schema=None) as batch_op:
        batch_op.add_column(sa.Column('validacion', sa.String(length=10), nullable=True))


def downgrade():
    with op.batch_alter_table('observaciones_nomenclador_historial', schema=None) as batch_op:
        batch_op.drop_column('validacion')
    with op.batch_alter_table('observaciones_nomenclador', schema=None) as batch_op:
        batch_op.drop_column('validacion')
