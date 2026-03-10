import json
import logging
import random
import time
from json import JSONDecodeError
from typing import Any, Optional


def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(message)s",
    )


def extract_json_object(text: str) -> Optional[Any]:
    stripped = (text or "").strip()
    if not stripped:
        return None

    try:
        return json.loads(stripped)
    except JSONDecodeError:
        pass

    decoder = json.JSONDecoder()
    for index, char in enumerate(stripped):
        if char != "{":
            continue
        try:
            obj, end = decoder.raw_decode(stripped[index:])
            trailing = stripped[index + end :].strip()
            if trailing:
                return obj
            return obj
        except JSONDecodeError:
            continue

    return None


def backoff_sleep(attempt: int, base_seconds: float) -> None:
    jitter = random.uniform(0.0, 0.5)
    delay = base_seconds * (2 ** (attempt - 1)) + jitter
    time.sleep(delay)
