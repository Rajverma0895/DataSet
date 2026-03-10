from typing import Any, Dict, List, Tuple


REQUIRED_TOP_LEVEL_KEYS = {
    "chapter",
    "topic",
    "explanation",
    "formulas",
    "solved_problems",
    "unsolved_problems",
}


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _has_reasoning_template(solution: str) -> bool:
    step1 = solution.find("Step 1:")
    step2 = solution.find("Step 2:")
    step3 = solution.find("Step 3:")
    final_step = solution.find("Final Answer:")

    return -1 not in (step1, step2, step3, final_step) and step1 < step2 < step3 < final_step


def validate_entry(entry: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errors: List[str] = []

    if not isinstance(entry, dict):
        return False, ["Entry is not a JSON object."]

    missing_keys = REQUIRED_TOP_LEVEL_KEYS - set(entry.keys())
    if missing_keys:
        errors.append(f"Missing required keys: {sorted(missing_keys)}")
        return False, errors

    if not _is_non_empty_string(entry.get("chapter")):
        errors.append("'chapter' must be a non-empty string.")

    if not _is_non_empty_string(entry.get("topic")):
        errors.append("'topic' must be a non-empty string.")

    if not _is_non_empty_string(entry.get("explanation")):
        errors.append("'explanation' must be a non-empty string.")

    formulas = entry.get("formulas")
    if not isinstance(formulas, list) or not formulas:
        errors.append("'formulas' must be a non-empty list of strings.")
    elif not all(_is_non_empty_string(item) for item in formulas):
        errors.append("All 'formulas' items must be non-empty strings.")

    solved = entry.get("solved_problems")
    if not isinstance(solved, list):
        errors.append("'solved_problems' must be a list.")
    else:
        if len(solved) != 10:
            errors.append("'solved_problems' must contain exactly 10 items.")
        for index, item in enumerate(solved):
            if not isinstance(item, dict):
                errors.append(f"Solved problem at index {index} must be an object.")
                continue
            for key in ("problem", "solution", "final_answer"):
                if not _is_non_empty_string(item.get(key)):
                    errors.append(f"Solved problem {index} has invalid '{key}'.")

            solution_text = item.get("solution", "")
            if _is_non_empty_string(solution_text) and not _has_reasoning_template(solution_text):
                errors.append(
                    f"Solved problem {index} solution must include 'Step 1:', 'Step 2:', 'Step 3:', and 'Final Answer:' in order."
                )

    unsolved = entry.get("unsolved_problems")
    if not isinstance(unsolved, list):
        errors.append("'unsolved_problems' must be a list.")
    else:
        if len(unsolved) != 10:
            errors.append("'unsolved_problems' must contain exactly 10 items.")
        for index, item in enumerate(unsolved):
            if not _is_non_empty_string(item):
                errors.append(f"Unsolved problem at index {index} must be a non-empty string.")

    return len(errors) == 0, errors
