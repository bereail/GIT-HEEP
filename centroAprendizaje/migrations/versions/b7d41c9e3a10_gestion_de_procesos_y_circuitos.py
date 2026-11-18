"""gestión de procesos y circuitos

Solo crea tablas nuevas (procesos_*). No toca ninguna tabla existente.

Revision ID: b7d41c9e3a10
Revises: 8a3c4d2e1f07
Create Date: 2026-11-17 18:00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b7d41c9e3a10'
down_revision = '8a3c4d2e1f07'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'procesos_circuitos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('slug', sa.String(length=120), nullable=False),
        sa.Column('nombre', sa.String(length=200), nullable=False),
        sa.Column('clase', sa.String(length=20), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=False),
        sa.Column('borrador', sa.Text(), nullable=False),
        sa.Column('borrador_actualizado', sa.DateTime(), nullable=True),
        sa.Column('creado', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug'),
    )
    op.create_table(
        'procesos_versiones',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('circuito_id', sa.Integer(), nullable=False),
        sa.Column('numero', sa.Integer(), nullable=False),
        sa.Column('contenido', sa.Text(), nullable=False),
        sa.Column('motivo', sa.Text(), nullable=False),
        sa.Column('usuario', sa.String(length=80), nullable=False),
        sa.Column('cambios', sa.Text(), nullable=False),
        sa.Column('importante', sa.Boolean(), nullable=False),
        sa.Column('creado', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['circuito_id'], ['procesos_circuitos.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_procesos_versiones_circuito_id', 'procesos_versiones', ['circuito_id'])
    op.create_table(
        'procesos_comentarios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('circuito_id', sa.Integer(), nullable=False),
        sa.Column('elemento_id', sa.String(length=40), nullable=False),
        sa.Column('tipo', sa.String(length=20), nullable=False),
        sa.Column('texto', sa.Text(), nullable=False),
        sa.Column('resuelto', sa.Boolean(), nullable=False),
        sa.Column('creado', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['circuito_id'], ['procesos_circuitos.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_procesos_comentarios_circuito_id', 'procesos_comentarios', ['circuito_id'])
    op.create_table(
        'procesos_rangos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(length=200), nullable=False),
        sa.Column('minimo', sa.Numeric(precision=16, scale=2), nullable=True),
        sa.Column('maximo', sa.Numeric(precision=16, scale=2), nullable=True),
        sa.Column('moneda', sa.String(length=10), nullable=False),
        sa.Column('condicion', sa.Text(), nullable=False),
        sa.Column('autorizacion', sa.Text(), nullable=False),
        sa.Column('documentacion', sa.Text(), nullable=False),
        sa.Column('fuente_doc', sa.String(length=80), nullable=False),
        sa.Column('fuente_punto', sa.String(length=200), nullable=False),
        sa.Column('vigencia_desde', sa.Date(), nullable=True),
        sa.Column('vigencia_hasta', sa.Date(), nullable=True),
        sa.Column('estado', sa.String(length=20), nullable=False),
        sa.Column('actualizado', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'procesos_sugerencias',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('recurso', sa.String(length=20), nullable=False),
        sa.Column('pregunta', sa.Text(), nullable=False),
        sa.Column('texto', sa.Text(), nullable=False),
        sa.Column('clase', sa.String(length=20), nullable=False),
        sa.Column('estado', sa.String(length=20), nullable=False),
        sa.Column('nota', sa.Text(), nullable=False),
        sa.Column('reunion', sa.String(length=120), nullable=False),
        sa.Column('creado', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'procesos_auditoria',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('entidad', sa.String(length=40), nullable=False),
        sa.Column('entidad_id', sa.String(length=40), nullable=False),
        sa.Column('accion', sa.String(length=40), nullable=False),
        sa.Column('antes', sa.Text(), nullable=False),
        sa.Column('despues', sa.Text(), nullable=False),
        sa.Column('motivo', sa.Text(), nullable=False),
        sa.Column('usuario', sa.String(length=80), nullable=False),
        sa.Column('creado', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade():
    op.drop_table('procesos_auditoria')
    op.drop_table('procesos_sugerencias')
    op.drop_table('procesos_rangos')
    op.drop_index('ix_procesos_comentarios_circuito_id', table_name='procesos_comentarios')
    op.drop_table('procesos_comentarios')
    op.drop_index('ix_procesos_versiones_circuito_id', table_name='procesos_versiones')
    op.drop_table('procesos_versiones')
    op.drop_table('procesos_circuitos')
