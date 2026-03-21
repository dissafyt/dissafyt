import os
import urllib.parse
from typing import Any, Dict, List, Optional

import requests
from django.conf import settings


def slugify_business_name(name: Optional[str]) -> str:
    """Convert a business name into a simple slug for subdomains.

    Example:
        >>> slugify_business_name('Joe\'s Plumbing')
        "joes-plumbing"
    """

    if not name:
        return ""

    return (
        name
        .strip()
        .lower()
        .replace("'", "")
        .replace("&", "and")
        .replace(" ", "-")
    )


def build_whatsapp_link(phone_number: str, message: str) -> str:
    """Build a wa.me link that opens WhatsApp with a prefilled message."""

    encoded = urllib.parse.quote(message)
    clean_phone = phone_number.strip().lstrip("+")
    return f"https://wa.me/{clean_phone}?text={encoded}"


def generate_human_summary(conversation: List[Dict[str, str]]) -> str:
    """Create a short summary of the conversation for a human handoff."""

    if not conversation:
        return "No conversation history available."

    # Take the last few messages to avoid overly long summaries.
    snippet = conversation[-6:]
    lines = []
    for item in snippet:
        if "user" in item:
            lines.append(f"User: {item['user']}")
        if "assistant" in item:
            lines.append(f"Assistant: {item['assistant']}")

    return "\n".join(lines)


def _extract_agent_text(data: Any) -> str:
    if isinstance(data, str):
        return data.strip()

    if isinstance(data, dict):
        preferred_keys = [
            "output",
            "response",
            "text",
            "answer",
            "message",
            "content",
        ]
        for key in preferred_keys:
            if key in data:
                extracted = _extract_agent_text(data[key])
                if extracted:
                    return extracted

        for value in data.values():
            extracted = _extract_agent_text(value)
            if extracted:
                return extracted

    if isinstance(data, list):
        for item in data:
            extracted = _extract_agent_text(item)
            if extracted:
                return extracted

    return ""


def _query_agent_engine(prompt: str, history: Optional[List[Dict[str, str]]] = None) -> Optional[str]:
    query_url = getattr(settings, "MARKETING_AGENT_QUERY_URL", "")
    if not query_url:
        return None

    credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not credentials_path or not os.path.exists(credentials_path):
        return None

    try:
        from google.auth.transport.requests import Request
        from google.oauth2 import service_account

        credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
        credentials.refresh(Request())

        payload = {
            "input": {
                "prompt": prompt,
                "query": prompt,
                "message": prompt,
                "text": prompt,
                "history": history or [],
            }
        }

        response = requests.post(
            query_url,
            json=payload,
            headers={
                "Authorization": f"Bearer {credentials.token}",
                "Content-Type": "application/json",
            },
            timeout=25,
        )
        response.raise_for_status()

        data = response.json()
        extracted = _extract_agent_text(data)
        if extracted:
            return extracted

        return str(data)
    except Exception:
        return None


def generate_llm_response(prompt: str, history: Optional[List[Dict[str, str]]] = None) -> str:
    """Generate an LLM-style response.

    Priority:
      1) If Agent Engine is configured, query Vertex AI Agent Engine.
      2) Else if `GOOGLE_API_KEY` is configured, use Google GenAI.
      3) Else if `LLM_MODEL_PATH` is configured, use a local llama-cpp model.
      4) Otherwise return a placeholder response.
    """

    # 1) Vertex AI Agent Engine
    agent_response = _query_agent_engine(prompt=prompt, history=history)
    if agent_response:
        return agent_response

    # 2) Google GenAI (requires GOOGLE_API_KEY)
    google_api_key = os.environ.get("GOOGLE_API_KEY")
    if google_api_key:
        try:
            from google.genai import Client

            client = Client(api_key=google_api_key)
            raw_prompt = prompt
            if history:
                # Include a small window of history for context
                convo = []
                for item in history[-6:]:
                    if "user" in item:
                        convo.append(f"User: {item['user']}")
                    if "assistant" in item:
                        convo.append(f"Assistant: {item['assistant']}")
                convo.append(f"User: {prompt}")
                raw_prompt = "\n".join(convo)

            result = client.generate(
                model="models/text-bison-001",
                prompt=raw_prompt,
                temperature=0.7,
                max_output_tokens=256,
            )
            return result.text.strip()
        except Exception:
            # If something goes wrong, continue to the next option.
            pass

    # 3) Local llama-cpp model
    model_path = os.environ.get("LLM_MODEL_PATH")
    if model_path:
        try:
            from llama_cpp import Llama

            llm = Llama(model_path=model_path)
            prompt_parts = []
            if history:
                for item in history[-6:]:
                    if "user" in item:
                        prompt_parts.append(f"User: {item['user']}")
                    if "assistant" in item:
                        prompt_parts.append(f"Assistant: {item['assistant']}")
            prompt_parts.append(f"User: {prompt}")
            prompt_parts.append("Assistant:")
            full_prompt = "\n".join(prompt_parts)

            output = llm(prompt=full_prompt, max_tokens=256, stop=["User:"])
            return output["choices"][0]["text"].strip()
        except Exception:
            pass

    # 4) Placeholder fallback.
    return (
        "[LLM placeholder] "
        "This is a simulated assistant response. "
        "To enable a real model, set GOOGLE_API_KEY or LLM_MODEL_PATH.\n\n"
        f"User prompt: {prompt}"
    )
