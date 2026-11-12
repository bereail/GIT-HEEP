"""Cubre los escenarios pedidos para la mejora de Feedback y Consultas."""

from app.extensions import db
from app.models import Consulta, Feedback, Tema


def _crear_consulta(client, **extra):
    datos = {"tipo": "consulta", "mensaje": "Tengo una duda"}
    datos.update(extra)
    resp = client.post("/temas/demo/consultas/nueva", data=datos, follow_redirects=False)
    assert resp.status_code == 302
    # Location: /consultas/<token>?nueva=1 — el token va en el path, no en la query.
    path = resp.headers["Location"].split("?")[0]
    token = path.rstrip("/").rsplit("/", 1)[-1]
    return token


def test_feedback_cinco_estrellas_sin_comentario(client, app):
    resp = client.post("/temas/demo/feedback", data={"puntuacion": "5"}, follow_redirects=False)
    assert resp.status_code == 302
    with app.app_context():
        f = Feedback.query.one()
        assert f.puntuacion == 5
        assert f.comentario is None


def test_feedback_sugerencia_con_comentario_sin_puntuacion(client, app):
    resp = client.post(
        "/temas/demo/feedback",
        data={"categoria": "sugerencia", "comentario": "Estaría bueno un modo oscuro"},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    with app.app_context():
        f = Feedback.query.one()
        assert f.puntuacion is None
        assert f.categoria == "sugerencia"
        assert f.comentario == "Estaría bueno un modo oscuro"


def test_feedback_vacio_no_se_guarda(client, app):
    resp = client.post("/temas/demo/feedback", data={}, follow_redirects=True)
    assert resp.status_code == 200
    with app.app_context():
        assert Feedback.query.count() == 0


def test_usuario_crea_consulta_queda_pendiente(client, app):
    token = _crear_consulta(client, email="user@example.com")
    with app.app_context():
        c = Consulta.query.filter_by(token=token).first()
        assert c is not None
        assert c.estado == "abierta"  # "Pendiente"
        assert c.email == "user@example.com"
        assert c.mensajes[0].autor == "usuario"


def test_admin_responde_y_usuario_encuentra_la_respuesta_en_mis_consultas(client, admin_client, app):
    token = _crear_consulta(client)

    detalle = admin_client.get(f"/admin/consultas/{token}")
    assert detalle.status_code == 200

    resp = admin_client.post(
        f"/admin/consultas/{token}/responder",
        data={"mensaje": "Ya lo resolvimos, mirá el instructivo."},
        follow_redirects=False,
    )
    assert resp.status_code == 302

    with app.app_context():
        c = Consulta.query.filter_by(token=token).first()
        assert c.estado == "respondida"
        assert c.mensajes[-1].autor == "admin"

    # "Mis consultas": el token se resuelve y aparece la respuesta
    r = client.post("/mis-consultas.json", json={"tokens": [token]})
    assert r.status_code == 200
    datos = r.get_json()
    assert len(datos) == 1
    assert datos[0]["token"] == token
    assert datos[0]["estado"] == "respondida"
    assert datos[0]["ultimo_autor"] == "admin"


def test_usuario_puede_continuar_la_conversacion(client, admin_client, app):
    token = _crear_consulta(client)
    admin_client.post(f"/admin/consultas/{token}/responder", data={"mensaje": "Probá esto"})

    resp = client.post(f"/consultas/{token}/responder", data={"mensaje": "Sigo sin poder"}, follow_redirects=False)
    assert resp.status_code == 302

    with app.app_context():
        c = Consulta.query.filter_by(token=token).first()
        assert len(c.mensajes) == 3
        assert c.estado == "abierta"  # vuelve a quedar pendiente de respuesta


def test_mensaje_nuevo_del_usuario_se_marca_no_leido_por_admin(client, admin_client, app):
    token = _crear_consulta(client)
    admin_client.get(f"/admin/consultas/{token}")  # el admin ya la vio una vez

    with app.app_context():
        c = Consulta.query.filter_by(token=token).first()
        assert c.no_leida_por_admin is False  # la vio, no hay mensaje de usuario posterior

    client.post(f"/consultas/{token}/responder", data={"mensaje": "Una pregunta más"})

    with app.app_context():
        c = Consulta.query.filter_by(token=token).first()
        assert c.no_leida_por_admin is True  # mensaje nuevo después de la última vista del admin


def test_usuario_no_accede_a_consultas_de_otro(client):
    token_propio = _crear_consulta(client)
    token_ajeno = "aaaaaaaaaaaaaaaaaaaa"  # no existe / no es propio

    r = client.post("/mis-consultas.json", json={"tokens": [token_ajeno]})
    assert r.status_code == 200
    assert r.get_json() == []  # no devuelve nada si el token no existe

    # el propio sigue siendo accesible por su link
    detalle = client.get(f"/consultas/{token_propio}")
    assert detalle.status_code == 200
    # un token inventado da 404, no filtra datos de nadie
    assert client.get(f"/consultas/{token_ajeno}").status_code == 404


def test_consultas_existentes_siguen_accesibles_sin_email(client, app):
    """Simula una consulta creada antes de agregar el campo email (solo
    nombre_contacto) — tiene que seguir funcionando igual que antes."""
    token = _crear_consulta(client, nombre_contacto="Alguien", email="")
    with app.app_context():
        c = Consulta.query.filter_by(token=token).first()
        assert c.email is None
    detalle = client.get(f"/consultas/{token}")
    assert detalle.status_code == 200


def test_admin_marca_feedback_revisado(admin_client, app):
    with app.app_context():
        tema = Tema.query.filter_by(slug="demo").first()
        f = Feedback(tema_id=tema.id, puntuacion=2, comentario="No encontré lo que buscaba")
        db.session.add(f)
        db.session.commit()
        feedback_id = f.id

    resp = admin_client.post(f"/admin/feedback/{feedback_id}/revisar", follow_redirects=False)
    assert resp.status_code == 302
    with app.app_context():
        assert db.session.get(Feedback, feedback_id).revisado is True


def test_admin_cambia_estado_a_en_revision(client, admin_client, app):
    token = _crear_consulta(client)
    resp = admin_client.post(f"/admin/consultas/{token}/estado", data={"estado": "en_revision"}, follow_redirects=False)
    assert resp.status_code == 302
    with app.app_context():
        c = Consulta.query.filter_by(token=token).first()
        assert c.estado == "en_revision"
        assert c.estado_label == "En revisión"
