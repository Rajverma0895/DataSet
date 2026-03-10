import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import islice
from pathlib import Path

from tqdm import tqdm

from config import get_settings
from generator import GeminiDatasetGenerator
from storage import append_jsonl
from topic_list import iter_topic_records_cycled, load_topic_records_from_taxonomy
from utils import setup_logging


def _count_existing_records(path: Path) -> int:
    if not path.exists():
        return 0

    count = 0
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                count += 1
    return count


def main() -> None:
    settings = get_settings()
    setup_logging(settings.log_level)

    total_to_process = max(settings.target_entries, settings.min_topics_per_run)

    generator = GeminiDatasetGenerator(settings)
    topic_records = load_topic_records_from_taxonomy(settings.taxonomy_path)
    topic_iterator = iter_topic_records_cycled(topic_records)

    resume_offset = _count_existing_records(settings.output_path) if settings.resume_from_output else 0
    start_index = resume_offset
    end_index = resume_offset + total_to_process

    logging.info("Loaded topics from taxonomy... count=%s source=%s", len(topic_records), settings.taxonomy_path)
    logging.info(
        "Run window... start_index=%s end_index=%s resume=%s",
        start_index,
        end_index,
        settings.resume_from_output,
    )
    logging.info(
        "Generation config... model=%s models=%s max_workers=%s",
        settings.model_name,
        ",".join(settings.available_models),
        settings.max_workers,
    )

    saved_count = 0
    failed_count = 0

    records = list(islice(topic_iterator, start_index, end_index))

    with ThreadPoolExecutor(max_workers=settings.max_workers) as executor:
        future_to_topic = {}

        for record in records:
            chapter = record.get("chapter", settings.chapter_name)
            topic = record.get("topic", "")
            if not topic:
                failed_count += 1
                logging.warning("JSON validation failed... reason=Empty topic record")
                continue

            future = executor.submit(generator.generate_topic_entry, chapter, topic)
            future_to_topic[future] = topic

        for future in tqdm(as_completed(future_to_topic), total=len(future_to_topic), desc="Generating dataset"):
            topic = future_to_topic[future]
            try:
                entry = future.result()
            except Exception as exc:
                logging.error("Topic generation crashed... topic=%s error=%s", topic, str(exc))
                failed_count += 1
                continue

            if entry is None:
                failed_count += 1
                continue

            append_jsonl(settings.output_path, entry)
            saved_count += 1
            logging.info("Saved entry... topic=%s saved=%s", topic, saved_count)

    logging.info(
        "Run completed. requested=%s saved=%s failed=%s output=%s",
        total_to_process,
        saved_count,
        failed_count,
        settings.output_path,
    )


if __name__ == "__main__":
    main()
