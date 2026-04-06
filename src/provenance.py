import json
from pathlib import Path
from datetime import datetime


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "outputs"


def _now_iso():
    """
    Return a simple ISO timestamp.
    """
    return datetime.now().isoformat(timespec="seconds")


def create_run(
    run_id: str,
    workflow_name: str,
    workflow_version: str,
    dataset_version: str,
    input_files: list
) -> dict:
    """
    Initialize a provenance record for one workflow run.
    """
    record = {
        "run_id": run_id,
        "timestamp": _now_iso(),
        "workflow_name": workflow_name,
        "workflow_version": workflow_version,
        "dataset_version": dataset_version,
        "input_files": input_files,
        "steps": []
    }
    return record


def add_step(
    record: dict,
    step_name: str,
    step_type: str,
    input_files: list = None,
    output_files: list = None,
    parameters: dict = None,
    row_count_in: int = None,
    row_count_out: int = None,
    observations: dict = None
) -> dict:
    """
    Append one workflow step to the provenance record.
    """
    step = {
        "step_name": step_name,
        "step_type": step_type,
        "timestamp": _now_iso(),
        "input_files": input_files or [],
        "output_files": output_files or [],
        "parameters": parameters or {},
        "row_count_in": row_count_in,
        "row_count_out": row_count_out,
        "observations": observations or {}
    }

    record["steps"].append(step)
    return record


def save_record(record: dict, filename: str) -> Path:
    """
    Save provenance record as JSON in the outputs directory.
    """
    OUTPUT_DIR.mkdir(exist_ok=True)

    file_path = OUTPUT_DIR / filename
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)

    return file_path


def build_basic_observations_from_compare(
    dimension: str,
    entity: str,
    delta_value: float
) -> dict:
    """
    Helper to standardize simple comparison observations.
    """
    return {
        "dimension": dimension,
        "entity": entity,
        "completion_rate_delta": delta_value
    }