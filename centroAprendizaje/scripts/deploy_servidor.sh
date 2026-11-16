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
$COMO cp instance/centro_aprendizaje.sqlite3 "instance/centro_aprendizaje.sqlite3.bak-predeploy-$(date +%Y%m%d-%H%M)"

echo "== 2. Código"
$COMO git pull --ff-only
git log --oneline -1

echo "== 3. Dependencias (Flask 3.1.3)"
$COMO .venv/bin/pip install -q -r requirements.txt

echo "== 4. Contenido (en este orden)"
for s in importar_mihospital importar_timbo_expedientes importar_timbo_compras importar_faq_chats importar_equivalencias; do
  $COMO $PY scripts/$s.py | tail -1
done

echo "== 5. Pruebas antes de reiniciar"
$COMO $PY scripts/bateria_chatbot.py | tail -1

echo "== 6. Reinicio"
systemctl restart timbo-capacitaciones
sleep 3
systemctl is-active timbo-capacitaciones

echo "== 7. Controles"
B=https://timboheep.duckdns.org
for u in / /recursos /recursos/roles /recursos/glosario /recursos/algoritmo /recursos/simulador /recursos/explicame /recursos/sistemas /admin/login; do
  echo "$(curl -s -o /dev/null -w '%{http_code}' "$B$u") $u"
done
echo "guía no oficial (tiene que dar 404): $(curl -s -o /dev/null -w '%{http_code}' $B/static/docs/timbo-compras/guia-busqueda-nomenclador-y-solicitud-sipaf.pdf)"
curl -sI $B/recursos | grep -ciE "content-security-policy|strict-transport" | sed 's/^/encabezados de seguridad: /'
