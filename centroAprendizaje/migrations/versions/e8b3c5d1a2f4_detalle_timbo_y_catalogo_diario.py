"""revisión por servicio: detalle para TIMBÓ (ítem general) y registro de la
comparación diaria con el Catálogo WEB

Solo agrega una columna (con valor por defecto) a las tablas de la revisión
por servicio y crea una tabla nueva. No toca las tablas de Farmacia.

Revision ID: e8b3c5d1a2f4
Revises: d4a7e2b9c1f3
Create Date: 2026-11-22 00:30:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e8b3c5d1a2f4'
down_revision = 'd4a7e2b9c1f3'
branch_labels = None
depends_on = None


def upgrade():
    for tabla in ('revisiones_servicio', 'revisiones_servicio_historial'):
        with op.batch_alter_table(tabla, schema=None) as batch_op:
            batch_op.add_column(sa.Column('detalle_timbo', sa.String(length=300), nullable=False, server_default=''))

    op.create_table('actualizaciones_catalogo',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('en', sa.DateTime(), nullable=False),
    sa.Column('estado', sa.String(length=20), nullable=False),
    sa.Column('mensaje', sa.Text(), nullable=False),
    sa.Column('archivo', sa.String(length=200), nullable=False),
    sa.Column('items', sa.Integer(), nullable=False),
    sa.Column('nuevos', sa.Integer(), nullable=False),
    sa.Column('quitados', sa.Integer(), nullable=False),
    sa.Column('cambiados', sa.Integer(), nullable=False),
    sa.Column('no_utilizar', sa.Integer(), nullable=False),
    sa.Column('afectados', sa.Integer(), nullable=False),
    sa.Column('respuestas', sa.Integer(), nullable=False),
    sa.Column('detalle', sa.Text(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('actualizaciones_catalogo')
    for tabla in ('revisiones_servicio_historial', 'revisiones_servicio'):
        with op.batch_alter_table(tabla, schema=None) as batch_op:
            batch_op.drop_column('detalle_timbo')
