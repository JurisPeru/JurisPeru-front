import logging
import streamlit as st

from app.config import get_settings
from app.services.utils import stream_data


# -------------------------
# Configuración inicial
# -------------------------
def setup_logging():
    settings = get_settings()
    level = logging.INFO

    if settings.log_level == "ERROR":
        level = logging.ERROR
    elif settings.log_level == "DEBUG":
        level = logging.DEBUG

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler("app.log"), logging.StreamHandler()],
    )


logger = logging.getLogger(__name__)
settings = get_settings()
logger.info("Settings loaded successfully")

# -------------------------
# Configuración de página
# -------------------------
st.set_page_config(page_title="JurisPeru", page_icon="⚖️", layout="wide")

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
    enviar = st.button("🚀 Enviar pregunta", type="primary", use_container_width=True)

with col2:
    st.subheader("❓ Preguntas frecuentes")
    for faq in FAQS:
        st.button(faq, key=faq, on_click=set_query, args=(faq,))

# -------------------------
# Procesamiento de respuesta
# -------------------------
if enviar or query:
    st.write("---")
    col_resp, col_ctx = st.columns([2, 1])

    with col_resp:
        st.subheader("📌 Respuesta")
        try:
            with st.spinner("Generando respuesta..."):
                st.write_stream(stream_data(query, settings))
        except InterruptedError as e:
            st.error(str(e))
        except Exception as e:
            logger.exception(f"Unexpected error: {e}")
            st.error(f"Unexpected error: {e}")

    with col_ctx:
        st.subheader("📚 Documentos utilizados")
        if "contexts" in st.session_state and st.session_state["contexts"]:
            for i, ctx in enumerate(st.session_state["contexts"], 1):
                document = ctx.get("document")
                with st.container():
                    st.markdown(f"### 🔎 Contexto {i}")
                    st.caption(f"📄 **Archivo:** {document.get('source', 'N/A')}")
                    st.caption(
                        f"📑 **Página:** {document.get('page', '?')} / {document.get('total_pages', '?')}"
                    )
                    score = ctx.get("score")
                    if score is not None:
                        st.caption(f"⭐ **Relevancia:** {score:.3f}")
                    st.write(document.get("text", ""))
                    st.divider()
        else:
            st.info("No se encontraron documentos relacionados.")
