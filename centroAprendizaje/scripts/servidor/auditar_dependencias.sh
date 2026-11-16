#!/bin/sh
# Revisión mensual de dependencias con pip-audit. La corre cron como
# timbo-capacitaciones. pip-audit vive en su propio entorno para no mezclarse
# con el del sitio. El resultado lo muestra el panel /admin (primera línea:
# fecha; el resto, la salida de pip-audit).
set -u
APP=/var/www/timbo-capacitaciones/centroAprendizaje
HERRAMIENTA=/var/www/timbo-capacitaciones/.pip-audit
SALIDA="$APP/instance/auditoria_dependencias.txt"
umask 077
[ -x "$HERRAMIENTA/bin/pip-audit" ] || python3 -m venv "$HERRAMIENTA"
"$HERRAMIENTA/bin/pip" install -q --upgrade pip-audit
SITIO=$("$APP/.venv/bin/python" -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')
{ date +%d/%m/%Y; "$HERRAMIENTA/bin/pip-audit" --path "$SITIO" 2>&1; } > "$SALIDA.tmp"
mv "$SALIDA.tmp" "$SALIDA"
