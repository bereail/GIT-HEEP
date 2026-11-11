from functools import wraps

from flask import current_app, redirect, session, url_for


def sesion_admin_activa():
    return session.get("admin_autenticado") is True


def requiere_admin(vista):
    @wraps(vista)
    def envoltorio(*args, **kwargs):
        if not sesion_admin_activa():
            return redirect(url_for("admin.login"))
        return vista(*args, **kwargs)

    return envoltorio


def contrasena_correcta(contrasena):
    return contrasena == current_app.config["ADMIN_PASSWORD"]
