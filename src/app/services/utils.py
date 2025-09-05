import logging
import json
import requests
import streamlit as st

# Cliente global
session = requests.Session()
session.headers.update({"Connection": "keep-alive"})


def stream_data(query, settings):
    logger = logging.getLogger(__name__)
    contexts = []
    payload = {
        "query": query,
        "k": settings.retrieve.k,
        "temperature": settings.retrieve.temperature,
    }
    logger.info(
        f"Sending POST request to {settings.api_url}/ask/ with payload: {payload}"
    )
    try:
        with session.post(
            f"{settings.api_url}/ask/", json=payload, stream=True, timeout=300
        ) as r:
            logger.info(f"Received response with status code: {r.status_code}")
            for line in r.iter_lines():
                if line:
                    try:
                        response = json.loads(line.decode("utf-8"))
                        logger.debug(f"Received line: {response}")
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON decode error: {e}")
                        raise InterruptedError(
                            "Lo sentimos, hubo un problema al procesar la respuesta. Por favor, intenta nuevamente."
                        )

                    stage = response.get("stage")
                    data = response.get("data")
                    if stage == "tok":
                        logger.debug(f"Yielding data: {data}")
                        yield data
                    elif stage == "end":
                        contexts = response.get("contexts", [])
                        logger.debug(f"End of stream. Contexts: {contexts}")
                        st.session_state["contexts"] = contexts
    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")
        raise
