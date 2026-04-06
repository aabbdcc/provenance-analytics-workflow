import json
import pandas as pd
from pathlib import Path

# --- Configuration ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "outputs"


def load_csv(filename: str) -> pd.DataFrame:
    """
    Load a CSV file from outputs/.
    """
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        raise FileNotFoundError(f"Missing file: {file_path}")
    return pd.read_csv(file_path)


def load_json(filename: str) -> dict:
    """
    Load a JSON file from outputs/.
    """
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        raise FileNotFoundError(f"Missing file: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_main_findings():
    """
    Read workflow outputs and extract the main findings needed for summary writing.
    """
    v1_summary = load_csv("v1_overall_summary.csv")
    v2_summary = load_csv("v2_overall_summary.csv")

    country_compare = load_csv("compare_country_metrics.csv")
    dept_compare = load_csv("compare_department_metrics.csv")
    course_compare = load_csv("compare_course_metrics.csv")

    provenance_compare = load_json("provenance_compare.json")

    overall_v1 = float(v1_summary.loc[0, "completion_rate"])
    overall_v2 = float(v2_summary.loc[0, "completion_rate"])
    overall_delta = overall_v2 - overall_v1

    avg_hours_v1 = float(v1_summary.loc[0, "avg_time_spent_hours"])
    avg_hours_v2 = float(v2_summary.loc[0, "avg_time_spent_hours"])
    avg_hours_delta = avg_hours_v2 - avg_hours_v1

    strongest_country = country_compare.iloc[0]
    strongest_department = dept_compare.iloc[0]
    strongest_course = course_compare.iloc[0]

    findings = {
        "completion_rate_v1": overall_v1,
        "completion_rate_v2": overall_v2,
        "completion_rate_delta": overall_delta,
        "avg_hours_v1": avg_hours_v1,
        "avg_hours_v2": avg_hours_v2,
        "avg_hours_delta": avg_hours_delta,
        "country_name": strongest_country["country"],
        "country_delta": float(strongest_country["completion_rate_delta"]),
        "department_name": strongest_department["department"],
        "department_delta": float(strongest_department["completion_rate_delta"]),
        "course_name": strongest_course["course_name"],
        "course_delta": float(strongest_course["completion_rate_delta"]),
        "provenance_run_id": provenance_compare.get("run_id", "unknown"),
    }

    return findings


def build_summary_text(findings: dict) -> str:
    """
    Build a short text summary from extracted findings.
    """
    lines = []

    lines.append("Workflow comparison summary")
    lines.append("-" * 40)

    lines.append(
        f"Overall completion rate moved from {findings['completion_rate_v1']:.2%} "
        f"to {findings['completion_rate_v2']:.2%} "
        f"({findings['completion_rate_delta']:.2%})."
    )

    lines.append(
        f"Average time spent moved from {findings['avg_hours_v1']:.2f} "
        f"to {findings['avg_hours_v2']:.2f} hours "
        f"({findings['avg_hours_delta']:.2f})."
    )

    lines.append(
        f"The strongest country-level decline is observed in {findings['country_name']} "
        f"({findings['country_delta']:.2%})."
    )

    lines.append(
        f"The strongest department-level decline is observed in {findings['department_name']} "
        f"({findings['department_delta']:.2%})."
    )

    lines.append(
        f"The strongest course-level decline is observed in {findings['course_name']} "
        f"({findings['course_delta']:.2%})."
    )

    lines.append(
        f"These results are associated with comparison run: {findings['provenance_run_id']}."
    )

    return "\n".join(lines)


def save_summary(text: str, filename: str = "management_summary.txt") -> Path:
    """
    Save summary text to outputs/.
    """
    output_path = OUTPUT_DIR / filename
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)
    return output_path


def main():
    findings = extract_main_findings()
    summary_text = build_summary_text(findings)

    output_path = save_summary(summary_text)

    print("\nGenerated summary")
    print("-" * 40)
    print(summary_text)

    print(f"\nSaved summary file: {output_path.name}")


if __name__ == "__main__":
    main()