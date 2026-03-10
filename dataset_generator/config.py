import os
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Settings:
    api_provider: str
    gemini_api_key: str
    openrouter_api_key: str
    openrouter_base_url: str
    model_name: str
    available_models: Tuple[str, ...]
    max_workers: int
    output_path: Path
    taxonomy_path: Path
    resume_from_output: bool
    chapter_name: str
    target_entries: int
    min_topics_per_run: int
    max_retries: int
    retry_backoff_seconds: float
    log_level: str


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name, str(default)).strip()
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"Environment variable {name} must be an integer, got: {value}") from exc


def _float_env(name: str, default: float) -> float:
    value = os.getenv(name, str(default)).strip()
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"Environment variable {name} must be a float, got: {value}") from exc


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    return normalized in {"1", "true", "yes", "y", "on"}


def _list_env(name: str, default_values: Tuple[str, ...]) -> Tuple[str, ...]:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default_values

    items = tuple(item.strip() for item in raw.split(",") if item.strip())
    return items if items else default_values


def get_settings() -> Settings:
    load_dotenv()

    api_provider = os.getenv("API_PROVIDER", "gemini").strip().lower() or "gemini"
    if api_provider not in {"gemini", "openrouter"}:
        raise ValueError("API_PROVIDER must be either 'gemini' or 'openrouter'.")

    gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    openrouter_base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").strip()

    if api_provider == "gemini" and not gemini_api_key:
        raise ValueError("GEMINI_API_KEY is missing. Set it in your environment or .env file.")
    if api_provider == "openrouter" and not openrouter_api_key:
        raise ValueError("OPENROUTER_API_KEY is missing. Set it in your environment or .env file.")

    default_models: Tuple[str, ...] = (
        "gemini-2.5-flash",
        "gemini-3-flash-preview",
        "gemini-flash-latest",
    )
    if api_provider == "openrouter":
        default_models = (
            "google/gemini-2.5-flash",
            "openai/gpt-4o-mini",
            "meta-llama/llama-3.1-70b-instruct",
        )
        available_models = _list_env("OPENROUTER_MODELS", default_models)
        model_name = os.getenv("OPENROUTER_MODEL", available_models[0]).strip()
    else:
        available_models = _list_env("GEMINI_MODELS", default_models)
        model_name = os.getenv("GEMINI_MODEL", available_models[0]).strip()

    if model_name not in available_models:
        raise ValueError(
            f"Selected model '{model_name}' is not in configured models: {', '.join(available_models)}"
        )
    chapter_name = os.getenv("DATASET_CHAPTER", "General Mathematics").strip() or "General Mathematics"

    target_entries = max(1, _int_env("TARGET_ENTRIES", 40000))
    min_topics_per_run = max(1, _int_env("MIN_TOPICS_PER_RUN", 10))
    max_workers = max(1, _int_env("MAX_WORKERS", max(1, len(available_models) * 2)))
    max_retries = max(1, _int_env("MAX_RETRIES", 3))
    retry_backoff_seconds = max(0.1, _float_env("RETRY_BACKOFF_SECONDS", 1.5))

    output_path = Path(os.getenv("OUTPUT_PATH", "data/dataset.jsonl")).expanduser()
    taxonomy_path = Path(
        os.getenv("TAXONOMY_PATH", "data/math_subject_chapters_topics.json")
    ).expanduser()

    if not output_path.is_absolute():
        output_path = BASE_DIR / output_path
    if not taxonomy_path.is_absolute():
        taxonomy_path = BASE_DIR / taxonomy_path

    output_path = output_path.resolve()
    taxonomy_path = taxonomy_path.resolve()
    resume_from_output = _bool_env("RESUME_FROM_OUTPUT", True)
    log_level = os.getenv("LOG_LEVEL", "INFO").strip().upper() or "INFO"

    return Settings(
        api_provider=api_provider,
        gemini_api_key=gemini_api_key,
        openrouter_api_key=openrouter_api_key,
        openrouter_base_url=openrouter_base_url,
        model_name=model_name,
        available_models=available_models,
        max_workers=max_workers,
        output_path=output_path,
        taxonomy_path=taxonomy_path,
        resume_from_output=resume_from_output,
        chapter_name=chapter_name,
        target_entries=target_entries,
        min_topics_per_run=min_topics_per_run,
        max_retries=max_retries,
        retry_backoff_seconds=retry_backoff_seconds,
        log_level=log_level,
    )
