import time
import logging
import requests
import streamlit as st
from app.config import Settings
from app.services.api import stream_data


logger = logging.getLogger(__name__)


def check_api(settings: Settings, timeout=3):
    """
    Check rápido al endpoint /health. Devuelve True si status 200.
    Atrapa RequestException (ConnectionError, Timeout, etc).
    """
    url = f"{settings.api_url}/health/"
    try:
        r = requests.get(url, timeout=timeout)
        ok = r.status_code == 200
        logger.debug(f"check_api -> {url} status={r.status_code}")
        return ok
    except requests.exceptions.RequestException as e:
        logger.debug(f"check_api failed: {e}")
        return False


def wakeup_api(settings: Settings):
    """
    Ping sin bloquear: intenta despertar el servicio (no importa si falla).
    """
    url = f"{settings.api_url}/health/"
    try:
        # Intento rápido para que Render reciba tráfico y comience el cold start
        requests.get(url, timeout=3)
        logger.info("Wakeup ping enviado al API")
    except requests.exceptions.RequestException as e:
        logger.debug(f"Wakeup ping falló (esperado si está dormido): {e}")


def wait_until_api_ready(settings: Settings, timeout_seconds=60, interval_seconds=5):
    """
    Espera hasta que el API responda o se agote el timeout.
    Actualiza st.session_state['api_ready'].
    Devuelve True si API quedó listo, False si no.
    """
    attempts = max(1, int(timeout_seconds // interval_seconds))
    logger.info(
        f"Esperando API hasta {timeout_seconds}s (intervalo {interval_seconds}s), intentos={attempts}"
    )

    wakeup_api(settings)

    progress_bar = st.progress(0)
    for i in range(attempts):
        if check_api(settings):
            st.session_state["api_ready"] = True
            progress_bar.progress(100)
            logger.info("API respondió correctamente")
            return True
        progress = int((i / attempts) * 100)
        progress_bar.progress(progress)
        logger.debug(
            f"API no responde, intento {i + 1}/{attempts}. Dormir {interval_seconds}s"
        )
        time.sleep(interval_seconds)
        wakeup_api(settings)

    st.session_state["api_ready"] = False
    progress_bar.progress(100)
    logger.warning("API no respondió dentro del timeout configurado")
    return False


# -------------------------
# Función helper: ejecutar stream con retry en caso de InterruptedError
# -------------------------
def perform_stream_with_retries(
    query_text, settings, max_wait_seconds=60, interval_seconds=5
):
    """
    Intenta ejecutar stream_data(query, settings) y:
      - Si ocurre InterruptedError, espera hasta max_wait_seconds (polling interval_seconds)
        para que el API responda (wakeup + check).
      - Si el API queda listo, reintenta la stream una vez.
      - Si falla después del reintento, informa al usuario.
    """
    try:
        # Primer intento normal (puede fallar y lanzar InterruptedError)
        st.write_stream(stream_data(query_text, settings))
        return True
    except InterruptedError as e:
        # Este es el caso que nos interesa: la stream se interrumpió (p. ej. JSON decode o conexión)
        logger.warning(f"InterruptedError al hacer stream: {e}")
        st.warning(
            "La conexión con el API se interrumpió. Intentando reactivar el servicio y reintentar..."
        )

        # Esperar / reintentar hasta max_wait_seconds para que Render levante el servicio
        ready = wait_until_api_ready(
            settings,
            timeout_seconds=max_wait_seconds,
            interval_seconds=interval_seconds,
        )
        if not ready:
            st.error(
                "No se pudo reactivar el servicio en el tiempo esperado. Intenta recargar la página más tarde."
            )
            return False

        # Si API quedó listo, reintentar una vez
        try:
            st.info("API activado — reintentando la consulta...")
            st.write_stream(stream_data(query_text, settings))
            return True
        except InterruptedError as e2:
            logger.error(f"Segundo InterruptedError al reintentar stream: {e2}")
            st.error(
                "No se pudo completar la solicitud después de reintentar. Por favor intenta de nuevo más tarde."
            )
            return False
        except Exception as e2:
            logger.exception(f"Error inesperado en reintento del stream: {e2}")
            st.error(f"Error al reintentar la solicitud: {e2}")
            return False
    except Exception as e:
        logger.exception(f"Error inesperado durante stream inicial: {e}")
        st.error(f"Unexpected error: {e}")
        return False
