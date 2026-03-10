import json
import shutil
from pathlib import Path

JSONL_PATH = Path("data/dataset.jsonl")
PRETTY_DIR_PATH = Path("data/dataset_pretty_records")


def export_jsonl_to_pretty_records(jsonl_path: Path, output_dir: Path) -> None:
    if not jsonl_path.exists():
        raise FileNotFoundError(f"Input file not found: {jsonl_path}")

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    with jsonl_path.open("r", encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                record = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number}: {exc}") from exc

            count += 1
            record_path = output_dir / f"record_{count:06d}.json"
            with record_path.open("w", encoding="utf-8") as target:
                json.dump(record, target, indent=2, ensure_ascii=False)

    print(f"Exported {count} records")
    print(f"Source: {jsonl_path}")
    print(f"Pretty records directory: {output_dir}")


if __name__ == "__main__":
    export_jsonl_to_pretty_records(JSONL_PATH, PRETTY_DIR_PATH)
