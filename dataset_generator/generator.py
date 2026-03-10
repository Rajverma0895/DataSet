import logging
import json
from itertools import cycle
from threading import Lock, local
from typing import Any, Dict, Optional
from urllib import error, request

from google import genai

from config import Settings
from prompts import SYSTEM_PROMPT, build_generation_prompt
from utils import backoff_sleep, extract_json_object
from validator import validate_entry


class GeminiDatasetGenerator:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._thread_local = local()
        ordered_models = [settings.model_name] + [
            model for model in settings.available_models if model != settings.model_name
        ]
        self._model_cycle = cycle(ordered_models)
        self._model_lock = Lock()

    def _get_client(self) -> genai.Client:
        client = getattr(self._thread_local, "client", None)
        if client is None:
            client = genai.Client(api_key=self.settings.gemini_api_key)
            self._thread_local.client = client
        return client

    def _next_model(self) -> str:
        with self._model_lock:
            return next(self._model_cycle)

    def _generate_raw_text(self, chapter: str, topic: str, model_name: str) -> str:
        prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            f"User request:\n{build_generation_prompt(chapter=chapter, topic=topic)}"
        )

        if self.settings.api_provider == "openrouter":
            body = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": build_generation_prompt(chapter=chapter, topic=topic),
                    },
                ],
                "max_tokens": 1200,
            }
            payload = json.dumps(body).encode("utf-8")
            endpoint = self.settings.openrouter_base_url.rstrip("/") + "/chat/completions"
            req = request.Request(
                endpoint,
                data=payload,
                method="POST",
                headers={
                    "Authorization": f"Bearer {self.settings.openrouter_api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://local.dataset.generator",
                    "X-Title": "dataset-generator",
                },
            )
            try:
                with request.urlopen(req, timeout=120) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
            except error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")
                raise RuntimeError(f"OpenRouter HTTP {exc.code}: {detail}") from exc
            except error.URLError as exc:
                raise RuntimeError(f"OpenRouter request failed: {exc.reason}") from exc

            choices = data.get("choices", [])
            if not choices:
                raise RuntimeError(f"OpenRouter response missing choices: {data}")

            message = choices[0].get("message", {})
            content = message.get("content", "")
            if isinstance(content, list):
                content = "".join(part.get("text", "") for part in content if isinstance(part, dict))
            return str(content).strip()

        response = self._get_client().models.generate_content(
            model=model_name,
            contents=prompt,
        )
        return (response.text or "").strip()

    def generate_topic_entry(self, chapter: str, topic: str) -> Optional[Dict[str, Any]]:
        for attempt in range(1, self.settings.max_retries + 1):
            model_name = self._next_model()
            try:
                logging.info(
                    "Generating topic... topic=%s attempt=%s model=%s",
                    topic,
                    attempt,
                    model_name,
                )
                raw_text = self._generate_raw_text(chapter=chapter, topic=topic, model_name=model_name)

                parsed = extract_json_object(raw_text)
                if not isinstance(parsed, dict):
                    logging.warning("JSON validation failed... topic=%s reason=Could not parse JSON", topic)
                    if attempt < self.settings.max_retries:
                        backoff_sleep(attempt, self.settings.retry_backoff_seconds)
                    continue

                is_valid, errors = validate_entry(parsed)
                if not is_valid:
                    logging.warning(
                        "JSON validation failed... topic=%s errors=%s",
                        topic,
                        "; ".join(errors),
                    )
                    if attempt < self.settings.max_retries:
                        backoff_sleep(attempt, self.settings.retry_backoff_seconds)
                    continue

                return parsed
            except Exception as exc:
                logging.warning(
                    "Generation attempt failed... topic=%s attempt=%s model=%s error=%s",
                    topic,
                    attempt,
                    model_name,
                    str(exc),
                )
                if attempt < self.settings.max_retries:
                    backoff_sleep(attempt, self.settings.retry_backoff_seconds)

        logging.error("Failed to generate valid entry after retries... topic=%s", topic)
        return None
