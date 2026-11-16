"""revisión del nomenclador: revisores, observaciones e historial

Solo crea tablas nuevas: no toca equivalencias_articulos ni ninguna otra.

Revision ID: 5e1f0a7c2b90
Revises: 32218c012f25
Create Date: 2026-11-16 15:00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5e1f0a7c2b90'
down_revision = '32218c012f25'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('revisores_nomenclador',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nombre', sa.String(length=100), nullable=False),
    sa.Column('token_hash', sa.String(length=64), nullable=False),
    sa.Column('activo', sa.Boolean(), nullable=False),
    sa.Column('creado_en', sa.DateTime(), nullable=True),
    sa.Column('ultimo_acceso', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('revisores_nomenclador', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_revisores_nomenclador_token_hash'), ['token_hash'], unique=True)

    op.create_table('observaciones_nomenclador',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('revisor_id', sa.Integer(), nullable=False),
    sa.Column('clave_item', sa.String(length=300), nullable=False),
    sa.Column('nombre_item', sa.String(length=300), nullable=False),
    sa.Column('texto', sa.Text(), nullable=False),
    sa.Column('creado_en', sa.DateTime(), nullable=True),
    sa.Column('actualizado_en', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['revisor_id'], ['revisores_nomenclador.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('revisor_id', 'clave_item', name='uq_observacion_revisor_item')
    )
    with op.batch_alter_table('observaciones_nomenclador', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_observaciones_nomenclador_clave_item'), ['clave_item'], unique=False)
        batch_op.create_index(batch_op.f('ix_observaciones_nomenclador_revisor_id'), ['revisor_id'], unique=False)

    op.create_table('observaciones_nomenclador_historial',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('observacion_id', sa.Integer(), nullable=False),
    sa.Column('texto', sa.Text(), nullable=False),
    sa.Column('guardado_en', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['observacion_id'], ['observaciones_nomenclador.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('observaciones_nomenclador_historial', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_observaciones_nomenclador_historial_observacion_id'), ['observacion_id'], unique=False)


def downgrade():
    with op.batch_alter_table('observaciones_nomenclador_historial', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_observaciones_nomenclador_historial_observacion_id'))
    op.drop_table('observaciones_nomenclador_historial')
    with op.batch_alter_table('observaciones_nomenclador', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_observaciones_nomenclador_revisor_id'))
        batch_op.drop_index(batch_op.f('ix_observaciones_nomenclador_clave_item'))
    op.drop_table('observaciones_nomenclador')
    with op.batch_alter_table('revisores_nomenclador', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_revisores_nomenclador_token_hash'))
    op.drop_table('revisores_nomenclador')
