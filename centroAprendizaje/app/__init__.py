import os

from flask import Flask, render_template
from flask_wtf import CSRFProtect

from app.extensions import db

csrf = CSRFProtect()


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    os.makedirs(app.instance_path, exist_ok=True)

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
        app.instance_path, "centro_aprendizaje.sqlite3"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JSON_AS_ASCII"] = False

    # SECRET_KEY firma la cookie de sesión del panel de administración.
    # ADMIN_PASSWORD es la contraseña compartida para entrar al panel — en
    # desarrollo usa un valor por defecto, pero en producción hay que
    # definir las dos variables de entorno antes de exponer el sitio.
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "clave-de-desarrollo-cambiar-en-produccion")
    app.config["ADMIN_PASSWORD"] = os.environ.get("ADMIN_PASSWORD", "admin123")
    app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8 MB por archivo subido

    db.init_app(app)
    csrf.init_app(app)

    from app import models  # noqa: F401 — registra los modelos en SQLAlchemy

    with app.app_context():
        db.create_all()

    from app.ui.routes import ui_bp

    app.register_blueprint(ui_bp)

    from app.admin.routes import admin_bp

    app.register_blueprint(admin_bp)

    @app.template_global()
    def tutoriales_para_js(categoria):
        """Lista mínima [{slug}, ...] que progreso.js necesita para calcular
        el % de avance de una categoría leyendo localStorage."""
        return [{"slug": t.slug} for t in categoria.tutoriales]

    @app.template_global()
    def categorias_para_js(tema):
        """Igual que `tutoriales_para_js`, pero para todas las categorías de
        un tema (usado para la barra de progreso total)."""
        return [
            {"slug": c.slug, "tutoriales": tutoriales_para_js(c)}
            for c in tema.categorias
        ]

    @app.errorhandler(404)
    def no_encontrado(_error):
        return render_template("404.html"), 404

    return app
