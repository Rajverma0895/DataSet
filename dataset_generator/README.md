# Math Dataset Generator (Gemini)

Automated pipeline for generating a structured math dataset topic-by-topic using Gemini Flash.

Note: `data/dataset.jsonl` is intentionally one JSON object per line (JSONL format) for scalable append writes.
For human-readable output without creating one huge JSON array, run:

```bash
python format_dataset.py
```

This creates per-record pretty files in `data/dataset_pretty_records/`.

Solved problems are enforced to follow this reasoning template:

```
Step 1: ...
Step 2: ...
Step 3: ...
Final Answer: ...
```

## Run Instructions

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set your API key:

macOS/Linux:

```bash
export GEMINI_API_KEY=your_key
```

Windows PowerShell:

```powershell
$env:GEMINI_API_KEY="your_key"
```

Windows CMD:

```bat
set GEMINI_API_KEY=your_key
```

3. Run the pipeline:

```bash
python main.py
```

## Run With UI (Recommended)

Launch the Streamlit UI:

```bash
streamlit run ui.py
```

From the UI you can:

- Generate next N topics in one click
- Resume from current `dataset.jsonl`
- Change model and retry settings
- Sync `dataset_pretty.json` from `dataset.jsonl`

The pipeline reads chapter/topic pairs from `data/math_subject_chapters_topics.json`.
If the file is missing, it falls back to the small built-in topic list.

## Optional Environment Variables

- `GEMINI_MODEL` (default: `gemini-2.5-flash`)
- `GEMINI_MODELS` (default: `gemini-2.5-flash,gemini-3-flash-preview,gemini-flash-latest`)
- `MAX_WORKERS` (default: `len(GEMINI_MODELS) * 2`)
- `TARGET_ENTRIES` (default: `40000`)
- `MIN_TOPICS_PER_RUN` (default: `10`)
- `MAX_RETRIES` (default: `3`)
- `RETRY_BACKOFF_SECONDS` (default: `1.5`)
- `OUTPUT_PATH` (default: `data/dataset.jsonl`)
- `TAXONOMY_PATH` (default: `data/math_subject_chapters_topics.json`)
- `DATASET_CHAPTER` (default: `General Mathematics`)
- `LOG_LEVEL` (default: `INFO`)
