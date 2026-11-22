#!/bin/sh
# Programa la comparación diaria con el Catálogo WEB: todos los días a las
# 6:00 de Argentina. Cron la llama cada hora y el script solo trabaja a esa
# hora y una vez por día (no depende de la zona horaria del servidor).
# Se corre UNA vez, como root, después del deploy que la trae:
#   ssh ... root@138.36.238.175 'sh -s' < scripts/servidor/instalar_catalogo_diario.sh
# No toca las otras tareas de /etc/cron.d/timbo-capacitaciones.
set -eu
APP=/var/www/timbo-capacitaciones/centroAprendizaje
cat > /etc/cron.d/timbo-catalogo <<EOF
# Centro de Aprendizaje: comparación diaria con el Catálogo WEB de TIMBÓ.
5 * * * * timbo-capacitaciones cd $APP && .venv/bin/python scripts/actualizar_catalogo.py --diario >> /var/www/timbo-capacitaciones/copias/catalogo.log 2>&1
EOF
chmod 644 /etc/cron.d/timbo-catalogo
echo "== Primera corrida (deja la copia inicial del catálogo)"
sudo -u timbo-capacitaciones -H sh -c "cd $APP && .venv/bin/python scripts/actualizar_catalogo.py" || true
