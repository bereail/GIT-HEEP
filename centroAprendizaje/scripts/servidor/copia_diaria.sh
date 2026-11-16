#!/bin/sh
# Copia diaria de la base. La corre cron como timbo-capacitaciones
# (/etc/cron.d/timbo-capacitaciones). Usa la copia en caliente de SQLite, así
# que sirve aunque el sitio esté en uso. Guarda 14 días; la PC de la usuaria
# se trae la última todos los días (scripts/traer_copia.sh).
set -eu
APP=/var/www/timbo-capacitaciones/centroAprendizaje
DESTINO=/var/www/timbo-capacitaciones/copias
umask 077
mkdir -p "$DESTINO"
ARCHIVO="$DESTINO/centro_aprendizaje-$(date +%Y%m%d).sqlite3"
"$APP/.venv/bin/python" - "$APP/instance/centro_aprendizaje.sqlite3" "$ARCHIVO.tmp" <<'EOF'
import sqlite3, sys
origen, destino = sqlite3.connect(sys.argv[1]), sqlite3.connect(sys.argv[2])
with destino:
    origen.backup(destino)
EOF
mv "$ARCHIVO.tmp" "$ARCHIVO"
find "$DESTINO" -name 'centro_aprendizaje-*.sqlite3' -mtime +14 -delete
