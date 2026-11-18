#!/bin/sh
# Deploy del Centro de Aprendizaje en el servidor. Se corre como root en el
# servidor, después de subir la rama a main en GitHub:
#   git push origin integracion-deploy:main
#   ssh -i ~/.ssh/timboheep_ed25519 -p5440 root@138.36.238.175 'sh -s' < scripts/deploy_servidor.sh
# Todo lo de la app corre como el usuario del servicio, nunca como root.
set -eu
cd /var/www/timbo-capacitaciones/centroAprendizaje
COMO="sudo -u timbo-capacitaciones -H"
PY=.venv/bin/python

echo "== 1. Copia de la base"
$COMO sh -c "umask 077; mkdir -p ../copias && cp instance/centro_aprendizaje.sqlite3 ../copias/predeploy-$(date +%Y%m%d-%H%M).sqlite3"

echo "== 2. Código"
$COMO git pull --ff-only
git log --oneline -1

echo "== 3. Dependencias (Flask 3.1.3)"
$COMO .venv/bin/pip install -q --upgrade pip setuptools
$COMO .venv/bin/pip install -q -r requirements.txt

echo "== 3b. Esquema de la base (migraciones nuevas, si hay)"
$COMO env FLASK_APP=run.py .venv/bin/flask db upgrade

echo "== 4. Contenido (en este orden)"
for s in importar_mihospital importar_timbo_expedientes importar_timbo_compras importar_faq_chats importar_equivalencias; do
  $COMO $PY scripts/$s.py | tail -1
done
# Gestión de procesos: solo crea lo que falta (nunca pisa los circuitos).
$COMO $PY scripts/sembrar_procesos.py | tail -1

echo "== 5. Pruebas antes de reiniciar"
$COMO $PY scripts/bateria_chatbot.py | tail -1

echo "== 6. Reinicio"
systemctl restart timbo-capacitaciones
sleep 3
systemctl is-active timbo-capacitaciones

echo "== 7. Controles"
B=https://timboheep.duckdns.org
for u in / /recursos /recursos/roles /recursos/glosario /recursos/algoritmo /recursos/explicame /recursos/sistemas /admin/login; do
  echo "$(curl -s -o /dev/null -w '%{http_code}' "$B$u") $u"
done
echo "procesos sin sesión (tiene que dar 302): $(curl -s -o /dev/null -w '%{http_code}' $B/admin/procesos/)"
echo "ocultos (tienen que dar 404): $(curl -s -o /dev/null -w "%{http_code}" $B/recursos/simulador) $(curl -s -o /dev/null -w "%{http_code}" $B/recursos/checklists)"
echo "guía no oficial (tiene que dar 404): $(curl -s -o /dev/null -w '%{http_code}' $B/static/docs/timbo-compras/guia-busqueda-nomenclador-y-solicitud-sipaf.pdf)"
curl -sI $B/recursos | grep -ciE "content-security-policy|strict-transport" | sed 's/^/encabezados de seguridad: /'
