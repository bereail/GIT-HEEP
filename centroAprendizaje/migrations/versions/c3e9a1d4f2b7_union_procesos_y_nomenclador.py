"""unión de dos ramas de migraciones (procesos y nomenclador)

No cambia nada en la base: solo une las cabezas b7d41c9e3a10 (gestión de
procesos) y 5caa3d03c084 (nomenclador), que salieron de 8a3c4d2e1f07 en PCs
distintas.

Revision ID: c3e9a1d4f2b7
Revises: 5caa3d03c084, b7d41c9e3a10
Create Date: 2026-11-18 21:00:00

"""


# revision identifiers, used by Alembic.
revision = 'c3e9a1d4f2b7'
down_revision = ('5caa3d03c084', 'b7d41c9e3a10')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
