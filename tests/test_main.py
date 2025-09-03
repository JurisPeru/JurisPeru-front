import json
import streamlit as st
from unittest.mock import patch, MagicMock
from app.config import get_settings
from app.main import stream_data
import streamlit.testing.v1 as st_test


def make_response(chunks):
    """Helper: simula la respuesta de requests.post con iter_content."""
    mock_resp = MagicMock()
    mock_resp.__enter__.return_value = mock_resp  # para usar "with"
    mock_resp.iter_content.return_value = [json.dumps(chunk).encode("utf-8") for chunk in chunks]
    return mock_resp


def test_stream_data_yields_tokens_and_stores_contexts(monkeypatch):
    # Datos simulados que vendrían del backend
    fake_chunks = [
        {"stage": "tok", "data": "Hola"},
        {"stage": "tok", "data": "Mundo"},
        {"stage": "end", "contexts": [{"document": {"source": "doc.pdf"}}]},
    ]

    mock_response = make_response(fake_chunks)

    # parcheamos requests.post para que devuelva nuestro fake
    with patch("app.services.utils.requests.post", return_value=mock_response):
        settings = get_settings()
        tokens = list(stream_data("hola", settings))

    # Verificamos que los yields salieron bien
    assert tokens == ["Hola", "Mundo"]

    # Y que contexts se guardó en session_state

    assert "contexts" in st.session_state
    assert st.session_state["contexts"][0]["document"]["source"] == "doc.pdf"


def test_app_renders():
    app = st_test.AppTest.from_file("src/app/main.py").run()
    assert app.title[0].value == "Preguntas y Respuesta sobre Códigos legales"
    assert app.text_area[0].label == "Realiza tu pregunta"
    assert app.button[0].label == "Enviar"


def test_contexts_render():
    def fake_stream(query, settings):
        _ = (query, settings)
        yield "respuesta simulada"
        st.session_state["contexts"] = [{"document": {"source": "doc.pdf", "text": "contenido"}}]

    # Debug: ver qué función está enlazada en main.py
    print("ANTES DEL PATCH:", stream_data)

    with patch("app.services.utils.stream_data", fake_stream):
        print("DESPUÉS DEL PATCH:", stream_data)

        app = st_test.AppTest.from_file("src/app/main.py")
        app.run()
        app.text_area[0].input("pregunta")
        app.button[0].click()
        app.run()

        assert any("📚 Documentos utilizados" in e.label for e in app.expander)
        assert any("### 🔎 Contexto 1" in m.value for m in app.markdown)
        assert any("📄 **Archivo:** doc.pdf" in c.value for c in app.caption)
