import os

from flask import Flask, render_template
from flask_wtf import CSRFProtect

from app.extensions import db, migrate

csrf = CSRFProtect()


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    os.makedirs(app.instance_path, exist_ok=True)

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
        app.instance_path, "centro_aprendizaje.sqlite3"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JSON_AS_ASCII"] = False

    app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8 MB por archivo subido

    # Secretos (SECRET_KEY, ADMIN_PASSWORD) desde variables de entorno, cookies
    # seguras, encabezados HTTP y proxy. Nunca hay contraseña por defecto.
    from app import seguridad

    seguridad.aplicar(app)

    # Para tests: pisa config (p. ej. SQLALCHEMY_DATABASE_URI) ANTES de
    # inicializar las extensiones, para que no quede ligado a la base real.
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    from app import models  # noqa: F401 — registra los modelos en SQLAlchemy

    from app.ui.routes import ui_bp

    app.register_blueprint(ui_bp)

    from app.admin.routes import admin_bp

    app.register_blueprint(admin_bp)

    from app.revision.routes import revision_bp

    app.register_blueprint(revision_bp)

    from app.models.revision_nomenclador import codigo_hospital, hora_ar

    app.add_template_filter(hora_ar, "hora_ar")
    app.add_template_filter(codigo_hospital, "codigo_hospital")

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

    @app.errorhandler(429)
    def demasiados_pedidos(_error):
        return render_template("error.html", titulo="Demasiados intentos",
                               mensaje="Hiciste muchos pedidos seguidos. Esperá unos minutos y probá de nuevo."), 429

    @app.errorhandler(500)
    def error_interno(_error):
        # Sin detalles técnicos: el detalle queda en el log del servidor.
        return render_template("error.html", titulo="Algo salió mal",
                               mensaje="Hubo un error al procesar el pedido. Probá de nuevo en un rato."), 500

    return app
