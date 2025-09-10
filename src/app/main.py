import logging
import streamlit as st

from app.config import get_settings, setup_logging
from app.services.utils import perform_stream_with_retries, wait_until_api_ready


setup_logging()
logger = logging.getLogger(__name__)
settings = get_settings()

st.set_page_config(page_title="JurisPeru", page_icon="⚖️", layout="wide")
logger.info("Settings loaded successfully")


if "api_ready" not in st.session_state:
    st.session_state["api_ready"] = False
    st.session_state["startup_checked"] = False

# Solo ejecutar la comprobación inicial una vez por sesión (o cuando explicitamente quieras reintentar)
if not st.session_state.get("startup_checked", False):
    st.session_state["startup_checked"] = True
    st.subheader("Verificando disponibilidad del API...")
    ready = wait_until_api_ready(settings, timeout_seconds=60, interval_seconds=5)
    if ready:
        st.success("✅ API lista, ya puedes usar la aplicación")
    else:
        st.warning(
            "El servicio backend no responde por ahora. La funcionalidad de consulta estará deshabilitada hasta que se reactive."
        )

# -------------------------
# UI principal
# -------------------------
st.title("⚖️ JurisPeru")
st.markdown(
    """
    #### Asistente legal para el Perú  
    JurisPeru es una aplicación que te ayuda a **resolver dudas legales en el Perú** 
    a partir de los **Códigos Civil, Penal y otras normativas relevantes**.  
    Realiza tu consulta y obtén **respuestas fundamentadas** con los documentos de referencia.
    """
)

# -------------------------
# Preguntas frecuentes
# -------------------------
FAQS = [
    "¿Qué dice el Código Civil sobre el matrimonio?",
    "¿Cuáles son las penas por hurto en el Perú?",
    "¿Qué normas regulan los contratos laborales?",
    "¿Cómo se regula la herencia en el Código Civil?",
    "¿Qué procedimientos existen para el divorcio?",
]

if "query_input" not in st.session_state:
    st.session_state.query_input = ""


def set_query(faq):
    st.session_state.query_input = faq


st.write("---")
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📝 Realiza tu consulta")
    query = st.text_area("Escribe tu pregunta aquí", key="query_input", height=120)
    enviar = st.button(
        "🚀 Enviar pregunta",
        type="primary",
        use_container_width=True,
        disabled=not st.session_state.get("api_ready", False),
    )

with col2:
    st.subheader("❓ Preguntas frecuentes")
    for faq in FAQS:
        st.button(faq, key=faq, on_click=set_query, args=(faq,))


# -------------------------
# Procesamiento de respuesta cuando el usuario presiona enviar
# -------------------------
if enviar and query:
    st.write("---")
    col_resp, col_ctx = st.columns([2, 1])

    with col_resp:
        st.subheader("📌 Respuesta")
        # Ejecutar stream con lógica de retry profesional
        with st.spinner("Generando respuesta..."):
            success = perform_stream_with_retries(
                query, settings, max_wait_seconds=60, interval_seconds=5
            )
            if success:
                st.success("Respuesta completada.")
            else:
                # Si falló (ej. no se despertó el API), deshabilitar el botón por seguridad
                st.session_state["api_ready"] = False

    with col_ctx:
        st.subheader("📚 Fuentes utilizadas")
        if "contexts" in st.session_state and st.session_state["contexts"]:
            for i, ctx in enumerate(st.session_state["contexts"], 1):
                document = ctx.get("document")
                with st.container():
                    st.markdown(f"### 🔎 Fuente {i}")
                    st.caption(f"📄 **Archivo:** {document.get('source', 'N/A')}")
                    st.caption(
                        f"📑 **Página:** {document.get('page', '?')} / {document.get('total_pages', '?')}"
                    )
                    score = ctx.get("score")
                    if score is not None:
                        st.caption(f"⭐ **Relevancia:** {score:.3f}")
                    st.divider()
        else:
            st.info("No se encontraron documentos relacionados.")
