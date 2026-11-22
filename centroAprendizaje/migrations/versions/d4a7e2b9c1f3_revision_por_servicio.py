"""revisión de artículos por servicio: llaves, bodegas, respuestas y necesidades

Solo crea tablas nuevas: no toca equivalencias_articulos ni las tablas de la
revisión de Farmacia (revisores_nomenclador, observaciones_nomenclador).

Revision ID: d4a7e2b9c1f3
Revises: c3e9a1d4f2b7
Create Date: 2026-11-21 22:00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd4a7e2b9c1f3'
down_revision = 'c3e9a1d4f2b7'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('llaves_servicio',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('servicio', sa.String(length=120), nullable=False),
    sa.Column('token_hash', sa.String(length=64), nullable=False),
    sa.Column('activo', sa.Boolean(), nullable=False),
    sa.Column('creado_en', sa.DateTime(), nullable=True),
    sa.Column('ultimo_acceso', sa.DateTime(), nullable=True),
    sa.Column('finalizado_en', sa.DateTime(), nullable=True),
    sa.Column('finalizado_por', sa.String(length=160), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('llaves_servicio', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_llaves_servicio_token_hash'), ['token_hash'], unique=True)

    op.create_table('llaves_servicio_bodegas',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('llave_id', sa.Integer(), nullable=False),
    sa.Column('bodega', sa.String(length=120), nullable=False),
    sa.Column('asignada_en', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['llave_id'], ['llaves_servicio.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('llave_id', 'bodega', name='uq_llave_bodega')
    )
    with op.batch_alter_table('llaves_servicio_bodegas', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_llaves_servicio_bodegas_llave_id'), ['llave_id'], unique=False)

    op.create_table('llaves_servicio_registro',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('llave_id', sa.Integer(), nullable=False),
    sa.Column('accion', sa.String(length=80), nullable=False),
    sa.Column('detalle', sa.Text(), nullable=False),
    sa.Column('en', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['llave_id'], ['llaves_servicio.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('llaves_servicio_registro', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_llaves_servicio_registro_llave_id'), ['llave_id'], unique=False)

    op.create_table('revisiones_servicio',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('llave_id', sa.Integer(), nullable=False),
    sa.Column('codigo_interno', sa.String(length=40), nullable=False),
    sa.Column('nombre_item', sa.String(length=300), nullable=False),
    sa.Column('codigo_propuesto', sa.String(length=40), nullable=False),
    sa.Column('resultado', sa.String(length=20), nullable=True),
    sa.Column('observacion', sa.Text(), nullable=False),
    sa.Column('decision', sa.String(length=20), nullable=True),
    sa.Column('codigo_correcto', sa.String(length=40), nullable=False),
    sa.Column('persona', sa.String(length=160), nullable=False),
    sa.Column('creado_en', sa.DateTime(), nullable=True),
    sa.Column('actualizado_en', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['llave_id'], ['llaves_servicio.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('llave_id', 'codigo_interno', name='uq_revision_servicio_articulo')
    )
    with op.batch_alter_table('revisiones_servicio', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_revisiones_servicio_codigo_interno'), ['codigo_interno'], unique=False)
        batch_op.create_index(batch_op.f('ix_revisiones_servicio_llave_id'), ['llave_id'], unique=False)

    op.create_table('revisiones_servicio_historial',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('revision_id', sa.Integer(), nullable=False),
    sa.Column('resultado', sa.String(length=20), nullable=True),
    sa.Column('observacion', sa.Text(), nullable=False),
    sa.Column('decision', sa.String(length=20), nullable=True),
    sa.Column('codigo_correcto', sa.String(length=40), nullable=False),
    sa.Column('codigo_propuesto', sa.String(length=40), nullable=False),
    sa.Column('persona', sa.String(length=160), nullable=False),
    sa.Column('guardado_en', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['revision_id'], ['revisiones_servicio.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('revisiones_servicio_historial', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_revisiones_servicio_historial_revision_id'), ['revision_id'], unique=False)

    op.create_table('necesidades_servicio',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('llave_id', sa.Integer(), nullable=False),
    sa.Column('descripcion', sa.String(length=300), nullable=False),
    sa.Column('presentacion', sa.String(length=200), nullable=False),
    sa.Column('uso', sa.String(length=300), nullable=False),
    sa.Column('tipo', sa.String(length=20), nullable=False),
    sa.Column('catalogo', sa.String(length=20), nullable=False),
    sa.Column('codigo_catalogo', sa.String(length=40), nullable=False),
    sa.Column('observaciones', sa.Text(), nullable=False),
    sa.Column('persona', sa.String(length=160), nullable=False),
    sa.Column('creado_en', sa.DateTime(), nullable=True),
    sa.Column('actualizado_en', sa.DateTime(), nullable=True),
    sa.Column('quitada_en', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['llave_id'], ['llaves_servicio.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('necesidades_servicio', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_necesidades_servicio_llave_id'), ['llave_id'], unique=False)


def downgrade():
    for tabla in ('necesidades_servicio', 'revisiones_servicio_historial', 'revisiones_servicio',
                  'llaves_servicio_registro', 'llaves_servicio_bodegas', 'llaves_servicio'):
        op.drop_table(tabla)
