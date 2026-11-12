import os
import tempfile

import pytest

from app import create_app
from app.extensions import db
from app.models import Categoria, Tema, Tutorial


@pytest.fixture(scope="session")
def app():
    db_fd, db_path = tempfile.mkstemp(suffix=".sqlite3")
    flask_app = create_app(test_config={
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
        "WTF_CSRF_ENABLED": False,
        "ADMIN_PASSWORD": "test-admin-pass",
    })
    assert flask_app.config["SQLALCHEMY_DATABASE_URI"] == f"sqlite:///{db_path}"
    yield flask_app
    with flask_app.app_context():
        db.engine.dispose()  # libera el archivo en Windows antes de borrarlo
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture(autouse=True)
def _base_de_datos_limpia(app):
    """Esquema nuevo y datos semilla (un tema/categoría/tutorial) antes de
    cada test; se tira todo al terminar, así ningún test ve datos de otro."""
    with app.app_context():
        db.create_all()
        tema = Tema(slug="demo", nombre="Demo", orden=0)
        db.session.add(tema)
        db.session.flush()
        categoria = Categoria(tema_id=tema.id, slug="modulo-1", titulo="Módulo 1", orden=0)
        db.session.add(categoria)
        db.session.flush()
        db.session.add(Tutorial(categoria_id=categoria.id, slug="leccion-1", titulo="Lección 1", orden=0))
        db.session.commit()
        yield
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def admin_client(client):
    client.post("/admin/login", data={"contrasena": "test-admin-pass"})
    return client
