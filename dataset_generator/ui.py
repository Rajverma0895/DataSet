import json
import os
from itertools import islice
from pathlib import Path
from typing import Dict, List

import streamlit as st

from config import get_settings
from generator import GeminiDatasetGenerator
from storage import append_jsonl
from topic_list import iter_topic_records_cycled, load_topic_records_from_taxonomy


st.set_page_config(page_title="Math Dataset Generator", layout="wide")


def count_records(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8") as file:
        return sum(1 for line in file if line.strip())


def get_last_record(path: Path) -> Dict[str, str]:
    if not path.exists():
        return {}
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        return {}
    try:
        return json.loads(lines[-1])
    except json.JSONDecodeError:
        return {}


def sync_pretty_json(jsonl_path: Path, pretty_path: Path) -> int:
    rows: List[Dict[str, object]] = []
    if jsonl_path.exists():
        with jsonl_path.open("r", encoding="utf-8") as file:
            for line in file:
                stripped = line.strip()
                if not stripped:
                    continue
                rows.append(json.loads(stripped))

    pretty_path.parent.mkdir(parents=True, exist_ok=True)
    pretty_path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    return len(rows)


def run_batch(batch_size: int, resume_from_output: bool) -> Dict[str, int]:
    settings = get_settings()
    topic_records = load_topic_records_from_taxonomy(settings.taxonomy_path)
    iterator = iter_topic_records_cycled(topic_records)

    existing_records = count_records(settings.output_path)
    start_index = existing_records if resume_from_output else 0
    end_index = start_index + batch_size

    generator = GeminiDatasetGenerator(settings)

    saved_count = 0
    failed_count = 0

    progress = st.progress(0)
    status = st.empty()

    for index, record in enumerate(islice(iterator, start_index, end_index), start=1):
        chapter = record.get("chapter", settings.chapter_name)
        topic = record.get("topic", "")

        status.info(f"Generating {index}/{batch_size}: {chapter} -> {topic}")

        if not topic:
            failed_count += 1
            continue

        entry = generator.generate_topic_entry(chapter=chapter, topic=topic)
        if entry is None:
            failed_count += 1
            progress.progress(index / batch_size)
            continue

        append_jsonl(settings.output_path, entry)
        saved_count += 1
        progress.progress(index / batch_size)

    status.success("Batch run completed")

    return {
        "saved": saved_count,
        "failed": failed_count,
        "start_index": start_index,
        "end_index": end_index,
        "topic_pool": len(topic_records),
    }


st.title("Math Dataset Generator UI")
st.caption("Generate topic-wise math dataset entries with Gemini and append to JSONL.")

with st.sidebar:
    st.header("Run Settings")
    preview_settings = get_settings()
    model_options = list(preview_settings.available_models)
    current_model = os.getenv("GEMINI_MODEL", preview_settings.model_name).strip() or preview_settings.model_name

    if current_model not in model_options:
        model_choices = [current_model] + model_options
    else:
        model_choices = model_options

    model_name = st.selectbox(
        "Gemini model",
        options=model_choices,
        index=model_choices.index(current_model),
    )
    batch_size = st.number_input("Topics per run", min_value=1, max_value=500, value=5, step=1)
    max_retries = st.number_input("Max retries", min_value=1, max_value=10, value=int(os.getenv("MAX_RETRIES", "3")), step=1)
    resume = st.checkbox("Resume from existing dataset.jsonl", value=True)

    if st.button("Apply Settings", use_container_width=True):
        os.environ["GEMINI_MODEL"] = str(model_name).strip()
        os.environ["MAX_RETRIES"] = str(max_retries)
        os.environ["RESUME_FROM_OUTPUT"] = "true" if resume else "false"
        st.success("Settings applied for this UI session.")

try:
    settings = get_settings()
except Exception as exc:
    st.error(f"Configuration error: {exc}")
    st.stop()

col1, col2, col3 = st.columns(3)
record_count = count_records(settings.output_path)
last_record = get_last_record(settings.output_path)

col1.metric("Current JSONL records", record_count)
col2.metric("Model", settings.model_name)
col3.metric("Taxonomy file", settings.taxonomy_path.name)

if last_record:
    st.write(
        f"Last topic: {last_record.get('chapter', 'N/A')} -> {last_record.get('topic', 'N/A')}"
    )

run_col, sync_col = st.columns(2)

with run_col:
    if st.button("Generate Next Batch", type="primary", use_container_width=True):
        result = run_batch(batch_size=int(batch_size), resume_from_output=resume)
        st.success(
            "Saved {saved}, Failed {failed}, Window {start_index} -> {end_index} (pool={topic_pool})".format(**result)
        )

with sync_col:
    if st.button("Sync dataset_pretty.json", use_container_width=True):
        pretty_path = settings.output_path.parent / "dataset_pretty.json"
        total = sync_pretty_json(settings.output_path, pretty_path)
        st.success(f"Updated {pretty_path} with {total} records")

st.subheader("Paths")
st.code(
    "\n".join(
        [
            f"JSONL: {settings.output_path}",
            f"Taxonomy: {settings.taxonomy_path}",
            f"Pretty JSON: {settings.output_path.parent / 'dataset_pretty.json'}",
        ]
    )
)
