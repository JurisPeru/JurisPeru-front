import logging
import streamlit as st

from app.config import get_settings
from app.services.utils import stream_data


# Configure logging
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

st.title("Preguntas y Respuesta sobre Códigos legales")

query = st.text_area("Realiza tu pregunta")
logger.debug(f"User query: {query}")

if st.button("Enviar") or query:
    show_response = True
    logger.info("Show response triggered")
else:
    show_response = False
    logger.debug("Show response not triggered")

if show_response:
    st.session_state.clear()
    logger.info("Session state cleared")
    try:
        logger.info("Calling stream_data")
        st.write_stream(stream_data(query, settings))
        logger.info("stream_data executed successfully")
        if "contexts" in st.session_state and st.session_state["contexts"]:
            logger.info(f"Found {len(st.session_state['contexts'])} contexts in session state")
            with st.expander("📚 Documentos utilizados"):
                for i, ctx in enumerate(st.session_state["contexts"], 1):
                    document = ctx.get("document")
                    st.markdown(f"### 🔎 Contexto {i}")
                    # Info en forma de columnas
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.caption(f"📄 **Archivo:** {document.get('source', 'N/A')}")
                    with col2:
                        st.caption(
                            f"📑 **Página:** {document.get('page', '?')} / {document.get('total_pages', '?')}"
                        )
                    with col3:
                        score = ctx.get("score")
                        if score is not None:
                            st.caption(f"⭐ **Relevancia:** {score:.3f}")

                    # Texto del chunk
                    st.write(document.get("text", ""))
                    st.divider()
        else:
            logger.info("No contexts found in session state")
    except InterruptedError as e:
        logger.error(f"InterruptedError occurred: {e}")
        st.error(str(e))
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        st.error(f"Unexpected error: {e}")
