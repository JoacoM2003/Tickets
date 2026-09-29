import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from google import genai
from .models import Ticket

MODELO = os.environ.get('GEMINI_MODEL', 'gemini-3.8-flash')
TIMEOUT_SEGUNDOS = 8  # bien por debajo de los 30 s de gunicorn

_executor = ThreadPoolExecutor(max_workers=2)


def _consultar_gemini(prompt):
    client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY'))
    response = client.models.generate_content(model=MODELO, contents=prompt)
    return response.text.strip().lower()


def sugerir_prioridad(titulo, descripcion):
    """
    Le pide a Gemini que sugiera una prioridad para el ticket.
    Espera como máximo TIMEOUT_SEGUNDOS; si no hay respuesta o falla,
    devuelve MEDIA para no bloquear la creación del ticket.
    """
    prompt = f"""Analiza este ticket de soporte y sugerí una prioridad.
Título: {titulo}
Descripción: {descripcion}

Respondé ÚNICAMENTE con una palabra, sin explicación: baja, media o alta."""

    mapping = {
        'baja': Ticket.Prioridad.BAJA,
        'media': Ticket.Prioridad.MEDIA,
        'alta': Ticket.Prioridad.ALTA,
    }

    try:
        futuro = _executor.submit(_consultar_gemini, prompt)
        texto = futuro.result(timeout=TIMEOUT_SEGUNDOS)
        print(f'Gemini sugirió prioridad "{texto}" para el ticket "{titulo}"')
        return mapping.get(texto, Ticket.Prioridad.MEDIA)
    except FutureTimeout:
        print(f'Gemini no respondió en {TIMEOUT_SEGUNDOS}s: se usa prioridad MEDIA.')
    except Exception as e:
        print(f'Error al consultar Gemini: {e}')
    return Ticket.Prioridad.MEDIA