# Auditoría de seguridad

Fecha: 15/11/2026. Cubre el sitio público y el panel `/admin`.

Las correcciones están en el código local (commit `2dfad08` y siguientes).
**Producción todavía no tiene ninguna**: se aplican al deployar, con
autorización.

## 1. Cómo se probó

| Prueba | Herramienta | Resultado |
|---|---|---|
| 23 pruebas de seguridad de comportamiento (`tests/test_seguridad.py`) | pytest con el cliente de Flask | 23/23 bien |
| Pruebas funcionales que ya existían | pytest | 18/18 bien (41 en total) |
| Chatbot (88 preguntas) | `scripts/bateria_chatbot.py` | 88/88 bien |
| Páginas sin violaciones de CSP ni errores de JS (16 públicas y 9 del panel con sesión) | Chrome headless por CDP | 0 problemas |
| Ejercicios de ordenar con flechas, a 1366 px y a 390 px | Chrome headless | 7/7 bien en los dos anchos |
| Confirmación "¿Eliminar…?" del panel (sin JS en línea) | Chrome headless | Cancelar no envía el formulario |
| Accesibilidad de formularios (etiquetas, alt, nombres, idioma, h1) en 11 páginas | Chrome headless | 4 campos sin etiqueta → corregidos |
| Enlaces externos del contenido (57) | `probar_enlaces.py` (HTTP + oEmbed de YouTube) | 55 bien, 2 observados (sección 5) |
| Dependencias con vulnerabilidades conocidas | pip-audit (todas las librerías instaladas) | 1 en Flask 3.0.3 → actualizado a 3.1.3, 0 pendientes |
| Servidor en producción (solo lectura) | curl y ssh sin cambiar nada | Ver S-03, S-11 y S-12 |

## 2. Hallazgos

Gravedad: **Alta** (permite entrar o tomar el control), **Media** (expone o
facilita un ataque), **Baja** (endurecimiento), **Info**.

| ID | Gravedad | Hallazgo | Evidencia | Corrección | Prueba nueva |
|---|---|---|---|---|---|
| S-01 | **Alta** | El login del panel no limitaba los intentos: se podía probar contraseñas sin fin (es una sola contraseña compartida) | Código de `admin.login`: sin contador | 5 intentos fallidos por IP cada 15 minutos → 429, aunque después se acierte | `test_fuerza_bruta_bloquea_el_login_aunque_despues_acierte` ✅ |
| S-02 | **Alta** (latente) | Si faltaban las variables de entorno, el panel usaba la contraseña `admin123` y una SECRET_KEY conocida (se podían falsificar sesiones) | `create_app`: `os.environ.get("ADMIN_PASSWORD", "admin123")`. En producción las variables **están** definidas y no son las de prueba (se verificó sin mostrarlas) | Sin variables, el panel queda **cerrado** y la clave de sesión se genera al azar. Los valores de desarrollo solo los pone `run.py` en local | `test_sin_variable_de_entorno_no_hay_contrasena_por_defecto` ✅ |
| S-03 | Media | Sin encabezados de seguridad: el panel se podía meter en un iframe (clickjacking), no había CSP ni `nosniff` | `curl -I` a producción: ninguno | CSP con nonce por respuesta (sin JS en línea; los `onsubmit`/`onchange` del panel pasaron a `admin.js`), `X-Frame-Options: DENY`, `nosniff`, Referrer-Policy, Permissions-Policy, COOP, HSTS por HTTPS y `no-store` en el panel y en las consultas | `test_encabezados_de_seguridad`, `test_cada_script_en_linea_lleva_el_nonce_de_la_respuesta` ✅, y 25 páginas sin violaciones en el navegador |
| S-04 | Media | Cookie de sesión sin `Secure` ni `SameSite` | Producción: `Set-Cookie: session=…; HttpOnly; Path=/` | `Secure` (salvo en local), `HttpOnly`, `SameSite=Lax` y sesión de 8 horas | `test_cookies_de_sesion_seguras_por_defecto` ✅ |
| S-05 | Media | Formularios públicos sin límite: se podía llenar la base con consultas, opiniones o preguntas al chatbot | Código: sin límites | Límites por IP: consultas 5/10 min, respuestas 20/10 min, opiniones 10/10 min, chatbot 60/min, votos 30/10 min, mis-consultas 60/min | `test_spam_de_consultas_se_frena`, `test_spam_al_chatbot_se_frena` ✅ |
| S-06 | Baja | La contraseña se comparaba con `==`, que deja medir diferencias de tiempo | `auth.contrasena_correcta` | `hmac.compare_digest` | Cubierta por las pruebas de login ✅ |
| S-07 | Baja | Al entrar no se renovaba la sesión (fijación de sesión) y al salir quedaban datos | `session["admin_autenticado"] = True` sobre la sesión anterior | `session.clear()` al entrar y al salir | `test_login_correcto_renueva_la_sesion_y_logout_la_borra` ✅ |
| S-08 | Baja | La subida de imágenes del panel solo miraba la extensión (un HTML con nombre `.png` pasaba) | Código de `admin.imagenes` | Se verifican los primeros bytes reales (JPG, PNG, GIF, WEBP). Ya se usaba `secure_filename` | `test_solo_se_suben_imagenes_reales`, `test_borrar_imagen_no_sale_de_la_carpeta`, `test_archivo_demasiado_grande_se_rechaza` ✅ |
| S-09 | Baja | El chatbot daba error 500 si el cuerpo era JSON pero no un objeto (por ejemplo, `"texto"`) | Lo encontró `test_entradas_raras_no_dan_error_500` | `_json_objeto()`: todo lo que no sea un objeto cuenta como vacío | El mismo test ✅ |
| S-10 | Baja | Flask 3.0.3 con PYSEC-2026-2151: falta `Vary: Cookie` en un caso puntual. Afecta solo con un proxy de caché, que no hay | pip-audit | Flask 3.1.3 en `requirements.txt` (el deploy tiene que correr `pip install -r requirements.txt`) | pip-audit: 0 vulnerabilidades ✅ |
| S-11 | Baja | nginx muestra su versión (`Server: nginx/1.18.0 (Ubuntu)`) | `curl -I` a producción | **Pendiente: es configuración del servidor.** Propuesta: `server_tokens off;` | — |
| S-12 | Media | En el servidor, la base y 6 copias de respaldo en `instance/` tienen permisos `644` (las puede leer cualquier usuario del sistema). Contienen las consultas (nombre y mail son opcionales) y el servidor aloja otros sitios | `ls -la instance/` (solo lectura) | **Pendiente: es configuración del servidor.** Propuesta: `chmod 600` a la base y a las copias, y mover las copias viejas fuera de la carpeta de la app | — |
| S-13 | Info | No hay "recuperar contraseña": es una sola contraseña compartida, y no hay usuarios ni roles en el panel | Diseño actual | Se recupera cambiando `ADMIN_PASSWORD` en `/etc/timbo-capacitaciones.env` y reiniciando el servicio. Al haber un solo rol, no hay escalamiento de privilegios posible; el riesgo es que no queda registro de quién hizo cada cambio | Riesgo residual (sección 4) |

## 3. Controles revisados sin hallazgos

| Control | Qué se comprobó |
|---|---|
| Rutas del panel | Las **53 combinaciones de ruta y método** (40 rutas) de `/admin`, todas menos el login, redirigen al login sin sesión. El test recorre el mapa de rutas, así que una ruta nueva sin proteger lo hace fallar |
| CSRF | Activo en todos los formularios. Sin token: login, consultas y opiniones responden 400. Exentos a propósito: 4 pedidos JSON anónimos que no cambian nada sensible (chatbot, votos y mis-consultas), con límites, y la previsualización del panel, que pide sesión y no guarda nada |
| XSS | Jinja escapa todo y no hay `|safe` en ninguna plantilla. Un código malicioso enviado en una consulta, una opinión, la búsqueda, el chatbot o `?contexto=` sale escapado (4 tests) |
| Inyección SQL | Solo ORM (SQLAlchemy), sin SQL escrito a mano. Probado con `' OR 1=1; DROP TABLE…` en el chatbot, la búsqueda, los tokens y la URL |
| IDOR | Las consultas se ven solo con su token: 96 bits al azar, imposible de adivinar. Con un token cambiado da 404. `mis-consultas.json` devuelve solo los tokens pedidos |
| CORS | La app no manda `Access-Control-Allow-Origin`: ningún otro sitio puede leer sus respuestas |
| Errores | En producción no hay modo debug (gunicorn). La página 500 nueva no muestra detalles (`test_error_interno_no_muestra_detalles`). Los 404 no revelan nada |
| HTTPS | http → 301 a https. El certificado es válido (curl lo acepta) |
| Archivos estáticos y PDF | Los sirve nginx desde `app/static`. Intentar salir de la carpeta (`../`) da 404 o 400. Desde la web no se pueden subir PDF |
| Secretos | No hay secretos en el repositorio. En el servidor: archivo de entorno con permisos `600`, del usuario root |
| Separación pública/privada | El sitio público no usa nada de `/admin`. Lo de `/admin` exige sesión y no se guarda en caché |

## 4. Riesgos residuales

1. **Límites en memoria:** cada worker de gunicorn cuenta por separado, así
   que el límite real se multiplica por la cantidad de workers. Para un
   límite compartido, conviene `limit_req` en nginx sobre `/admin/login` y
   los POST públicos. Es un cambio en el servidor y necesita autorización.
2. **Una sola contraseña para el panel**, sin registro de quién hace qué. Si
   más personas van a administrar, conviene tener usuarios individuales.
3. **CSP con `style-src 'unsafe-inline'`**, porque hay estilos en atributos
   `style=""`. El riesgo es bajo, ya que los scripts están cerrados con
   nonce.
4. **Producción sin las correcciones** hasta que se haga el deploy.
5. S-11 y S-12 quedan pendientes, porque se corrigen en el servidor.

## 5. Enlaces observados

| Enlace | Estado | Qué pasa |
|---|---|---|
| app.santafe.gov.ar/normativa (SIN) | No resuelve desde internet | Es esperable: el SIN solo funciona desde la red institucional, y el contenido ya lo aclara |
| youtu.be/QH7zvgZ7sbQ (Capacitación en Compras directas, 70 min) | La página de YouTube dice "OK", pero el dueño desactivó la reproducción en otros sitios | El portal usa un enlace directo, no un video insertado, así que debería abrir. **Falta verificarlo a mano** en un navegador |

## 6. Para deployar estas correcciones (cuando se autorice)

1. `pip install -r requirements.txt` en la `.venv` del servidor (Flask 3.1.3).
2. El archivo de entorno ya tiene `SECRET_KEY` y `ADMIN_PASSWORD`. No hace
   falta agregar nada: `COOKIE_SEGURA` y `DETRAS_DE_PROXY` están activas por
   defecto.
3. Después de reiniciar, comprobar con `curl -I` que aparecen los
   encabezados, y entrar al panel para ver que la cookie `Secure` funciona
   por HTTPS.
4. Opcional, con autorización: `server_tokens off`, `limit_req` y
   `chmod 600` (S-11, S-12 y riesgo residual 1).
