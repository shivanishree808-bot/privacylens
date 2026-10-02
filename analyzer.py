import json
import time
import streamlit as st
from google import genai
from google.genai import types
from prompt import SYSTEM_PROMPT

# Tried in order. If the first is busy or missing, the next one is used.
MODEL_NAMES = ["gemini-3.5-flash", "gemini-2.5-flash"]

RETRIES_PER_MODEL = 3
BUSY_SIGNS = ("503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED", "overloaded")
MISSING_SIGNS = ("404", "NOT_FOUND")


def _get_client():
    return genai.Client(api_key=st.secrets["GEMINI_API_KEY"])


def _clean_and_parse(raw_text):
    # Gemini sometimes wraps JSON in ```json fences, so we strip them first
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
    return json.loads(cleaned.strip())


def _config():
    return types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        response_mime_type="application/json",
    )


def _generate(contents):
    client = _get_client()
    last_error = None

    for model in MODEL_NAMES:
        for attempt in range(RETRIES_PER_MODEL):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=_config(),
                )
                return _clean_and_parse(response.text)
            except Exception as e:
                last_error = e
                message = str(e)
                if any(sign in message for sign in MISSING_SIGNS):
                    break  # this model name doesn't exist, try the next one
                if any(sign in message for sign in BUSY_SIGNS):
                    time.sleep(2 * (attempt + 1))  # wait 2s, 4s, 6s, then retry
                    continue
                raise  # a different error (bad key, bad JSON), so show it

    raise last_error


def analyze_text(text):
    return _generate([text])


def analyze_image(image_bytes, mime_type):
    image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    return _generate([image_part, "Analyze this image for privacy-sensitive information."])