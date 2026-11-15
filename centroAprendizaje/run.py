import os

from app import create_app

if __name__ == "__main__":
    # Solo para desarrollo local (python run.py). En el servidor la app la
    # levanta gunicorn importando `run:app`, y los valores salen del entorno.
    os.environ.setdefault("SECRET_KEY", "clave-de-desarrollo-cambiar-en-produccion")
    os.environ.setdefault("ADMIN_PASSWORD", "admin123")
    os.environ.setdefault("COOKIE_SEGURA", "0")  # http://127.0.0.1 no es HTTPS
    os.environ.setdefault("DETRAS_DE_PROXY", "0")
    create_app().run(debug=True)
else:
    app = create_app()
