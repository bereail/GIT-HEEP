#!/bin/sh
# Cambios de seguridad del servidor (2026-11). Se corre UNA vez, como root.
# El panel queda con su contraseña de siempre (la usuaria no quiso otra):
# nginx solo limita los intentos de login.
#   ssh ... root@138.36.238.175 'sh -s' < scripts/servidor/aplicar_seguridad.sh
# Solo toca el sitio de TIMBÓ: los otros sitios de nginx no cambian.
set -eu
APP=/var/www/timbo-capacitaciones/centroAprendizaje
SITIO=/etc/nginx/sites-enabled/timbo-capacitaciones
COMO="sudo -u timbo-capacitaciones -H"

echo "== 1. Base y copias: solo las lee el servicio"
mkdir -p /var/www/timbo-capacitaciones/copias
for f in "$APP"/instance/centro_aprendizaje.sqlite3.bak*; do
  [ -e "$f" ] && mv "$f" /var/www/timbo-capacitaciones/copias/
done
chown -R timbo-capacitaciones:timbo-capacitaciones "$APP/instance" /var/www/timbo-capacitaciones/copias
chmod 700 "$APP/instance" /var/www/timbo-capacitaciones/copias
find "$APP/instance" /var/www/timbo-capacitaciones/copias -type f -exec chmod 600 {} +
ls -la "$APP/instance" /var/www/timbo-capacitaciones/copias

echo "== 2. Copia diaria y revisión mensual de dependencias"
cat > /etc/cron.d/timbo-capacitaciones <<EOF
# Centro de Aprendizaje: copia diaria de la base y revisión mensual de dependencias.
15 3 * * * timbo-capacitaciones sh $APP/scripts/servidor/copia_diaria.sh
30 4 1 * * timbo-capacitaciones sh $APP/scripts/servidor/auditar_dependencias.sh
EOF
chmod 644 /etc/cron.d/timbo-capacitaciones
$COMO sh "$APP/scripts/servidor/copia_diaria.sh" && ls -la /var/www/timbo-capacitaciones/copias | tail -2
$COMO sh "$APP/scripts/servidor/auditar_dependencias.sh"; cat "$APP/instance/auditoria_dependencias.txt"

echo "== 3. nginx: sin versión y límite de intentos en el login del panel"
cp "$SITIO" "/root/timbo-capacitaciones.nginx.bak-$(date +%Y%m%d-%H%M)"
echo 'limit_req_zone $binary_remote_addr zone=timbo_login:10m rate=10r/m;' > /etc/nginx/conf.d/timbo-limites.conf
python3 - "$SITIO" <<'EOF'
import sys
ruta = sys.argv[1]
s = open(ruta).read()
if "server_tokens off" not in s:
    s = s.replace("    server_name timboheep.duckdns.org;\n", "    server_name timboheep.duckdns.org;\n    server_tokens off;\n")
proxy = """        proxy_pass http://127.0.0.1:8003;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
"""
assert proxy in s, "no encontré el bloque location / esperado"
if "timbo_login" not in s:
    nuevo = f"""    # Login del panel: como mucho 10 intentos por minuto por IP.
    location = /admin/login {{
        limit_req zone=timbo_login burst=5 nodelay;
{proxy}    }}

    location / {{
"""
    s = s.replace("    location / {\n", nuevo, 1)
open(ruta, "w").write(s)
EOF
if nginx -t; then
  systemctl reload nginx
else
  echo "nginx -t falló: vuelvo a la configuración anterior"
  cp "$(ls -1t /root/timbo-capacitaciones.nginx.bak-* | head -1)" "$SITIO"; rm -f /etc/nginx/conf.d/timbo-limites.conf
  nginx -t && systemctl reload nginx; exit 1
fi

echo "== 4. Controles"
B=https://timboheep.duckdns.org
echo "inicio: $(curl -s -o /dev/null -w '%{http_code}' $B/)  (200)"
echo "login del panel: $(curl -s -o /dev/null -w '%{http_code}' $B/admin/login)  (200)"
echo "versión de nginx a la vista: $(curl -sI $B/ | grep -i '^server:')  (sin número)"
for s in ailonline.com.ar institutoalborada.com.ar; do echo "otro sitio $s: $(curl -s -o /dev/null -w '%{http_code}' https://$s/)"; done
