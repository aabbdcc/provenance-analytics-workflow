import pandas as pd

from pathlib import Path
from provenance import create_run, add_step, save_record

# --- Configuration ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "outputs"

FILES = {
    "country": ("v1_country_metrics.csv", "v2_country_metrics.csv"),
    "department": ("v1_department_metrics.csv", "v2_department_metrics.csv"),
    "course": ("v1_course_metrics.csv", "v2_course_metrics.csv"),
}


def load_metrics(filename: str) -> pd.DataFrame:
    """
    Load an aggregated metrics file from the outputs directory.
    """
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        raise FileNotFoundError(f"Missing aggregated file: {file_path}")
    return pd.read_csv(file_path)


def compare_dimension(df_v1: pd.DataFrame, df_v2: pd.DataFrame, key_col: str) -> pd.DataFrame:
    """
    Compare aggregated metrics across two dataset versions.

    Main output:
    - metric values in v1 and v2
    - absolute deltas
    """
    merged = pd.merge(
        df_v1,
        df_v2,
        on=key_col,
        how="outer",
        suffixes=("_v1", "_v2")
    )

    numeric_metrics = [
        "learner_count",
        "completion_rate",
        "completion_gap_vs_overall",
        "active_learner_ratio",
        "avg_progress_pct",
        "avg_time_spent_hours",
        "missing_hours_ratio",
    ]

    for metric in numeric_metrics:
        col_v1 = f"{metric}_v1"
        col_v2 = f"{metric}_v2"
        delta_col = f"{metric}_delta"

        merged[delta_col] = merged[col_v2] - merged[col_v1]

    # Main sorting logic: strongest negative completion shift first
    merged = merged.sort_values(by="completion_rate_delta", ascending=True)

    return merged


def save_compare_output(df: pd.DataFrame, name: str) -> None:
    """
    Save comparison output to outputs directory.
    """
    output_path = OUTPUT_DIR / f"compare_{name}_metrics.csv"
    df.to_csv(output_path, index=False)


def print_compare_block(df: pd.DataFrame, label: str, key_col: str) -> None:
    """
    Print a compact comparison summary for a given dimension.
    """
    print("\n" + "=" * 70)
    print(f"Comparison by {label}")
    print("=" * 70)

    print("\nLargest completion rate declines:")
    print(
        df[[key_col, "completion_rate_v1", "completion_rate_v2", "completion_rate_delta"]]
        .head(5)
        .to_string(index=False)
    )

    print("\nLargest drops in active learner ratio:")
    print(
        df.sort_values(by="active_learner_ratio_delta", ascending=True)[
            [key_col, "active_learner_ratio_v1", "active_learner_ratio_v2", "active_learner_ratio_delta"]
        ]
        .head(5)
        .to_string(index=False)
    )

    print("\nLargest increases in missing hours ratio:")
    print(
        df.sort_values(by="missing_hours_ratio_delta", ascending=False)[
            [key_col, "missing_hours_ratio_v1", "missing_hours_ratio_v2", "missing_hours_ratio_delta"]
        ]
        .head(5)
        .to_string(index=False)
    )


def print_key_observations(country_df: pd.DataFrame, dept_df: pd.DataFrame, course_df: pd.DataFrame) -> None:
    """
    Print a few direct observations from the comparisons.
    """
    worst_country = country_df.iloc[0]
    worst_department = dept_df.iloc[0]
    worst_course = course_df.iloc[0]

    print("\n" + "-" * 70)
    print("Preliminary observations")
    print("-" * 70)

    print(
        f"Country with the strongest completion decline: "
        f"{worst_country['country']} ({worst_country['completion_rate_delta']:.2%})"
    )

    print(
        f"Department with the strongest completion decline: "
        f"{worst_department['department']} ({worst_department['completion_rate_delta']:.2%})"
    )

    print(
        f"Course with the strongest completion decline: "
        f"{worst_course['course_name']} ({worst_course['completion_rate_delta']:.2%})"
    )


def main():
    # --- Initialize provenance record ---
    record = create_run(
        run_id="run_compare_v1_v2",
        workflow_name="learning_reporting_comparison",
        workflow_version="v1.0",
        dataset_version="v1_vs_v2",
        input_files=[
            "v1_country_metrics.csv", "v2_country_metrics.csv",
            "v1_department_metrics.csv", "v2_department_metrics.csv",
            "v1_course_metrics.csv", "v2_course_metrics.csv"
        ]
    )

    # Country comparison
    country_v1, country_v2 = FILES["country"]
    df_country_v1 = load_metrics(country_v1)
    df_country_v2 = load_metrics(country_v2)
    country_compare = compare_dimension(df_country_v1, df_country_v2, key_col="country")
    save_compare_output(country_compare, "country")
    print_compare_block(country_compare, "country", "country")

    record = add_step(
        record=record,
        step_name="compare_country_metrics",
        step_type="comparison",
        input_files=[country_v1, country_v2],
        output_files=["compare_country_metrics.csv"],
        parameters={"key_col": "country"},
        row_count_in=len(df_country_v1) + len(df_country_v2),
        row_count_out=len(country_compare),
        observations={
            "largest_country_decline": country_compare.iloc[0]["country"],
            "largest_country_completion_rate_delta": float(country_compare.iloc[0]["completion_rate_delta"])
        }
    )

    # Department comparison
    dept_v1, dept_v2 = FILES["department"]
    df_dept_v1 = load_metrics(dept_v1)
    df_dept_v2 = load_metrics(dept_v2)
    dept_compare = compare_dimension(df_dept_v1, df_dept_v2, key_col="department")
    save_compare_output(dept_compare, "department")
    print_compare_block(dept_compare, "department", "department")

    record = add_step(
        record=record,
        step_name="compare_department_metrics",
        step_type="comparison",
        input_files=[dept_v1, dept_v2],
        output_files=["compare_department_metrics.csv"],
        parameters={"key_col": "department"},
        row_count_in=len(df_dept_v1) + len(df_dept_v2),
        row_count_out=len(dept_compare),
        observations={
            "largest_department_decline": dept_compare.iloc[0]["department"],
            "largest_department_completion_rate_delta": float(dept_compare.iloc[0]["completion_rate_delta"])
        }
    )

    # Course comparison
    course_v1, course_v2 = FILES["course"]
    df_course_v1 = load_metrics(course_v1)
    df_course_v2 = load_metrics(course_v2)
    course_compare = compare_dimension(df_course_v1, df_course_v2, key_col="course_name")
    save_compare_output(course_compare, "course")
    print_compare_block(course_compare, "course", "course_name")

    record = add_step(
        record=record,
        step_name="compare_course_metrics",
        step_type="comparison",
        input_files=[course_v1, course_v2],
        output_files=["compare_course_metrics.csv"],
        parameters={"key_col": "course_name"},
        row_count_in=len(df_course_v1) + len(df_course_v2),
        row_count_out=len(course_compare),
        observations={
            "largest_course_decline": course_compare.iloc[0]["course_name"],
            "largest_course_completion_rate_delta": float(course_compare.iloc[0]["completion_rate_delta"])
        }
    )

    # Short overall note
    print_key_observations(country_compare, dept_compare, course_compare)

    record = add_step(
        record=record,
        step_name="summarize_comparison_observations",
        step_type="inspection",
        input_files=[
            "compare_country_metrics.csv",
            "compare_department_metrics.csv",
            "compare_course_metrics.csv"
        ],
        output_files=[],
        parameters={"sorting_metric": "completion_rate_delta"},
        row_count_in=len(country_compare) + len(dept_compare) + len(course_compare),
        row_count_out=3,
        observations={
            "country_with_strongest_decline": country_compare.iloc[0]["country"],
            "country_decline_value": float(country_compare.iloc[0]["completion_rate_delta"]),
            "department_with_strongest_decline": dept_compare.iloc[0]["department"],
            "department_decline_value": float(dept_compare.iloc[0]["completion_rate_delta"]),
            "course_with_strongest_decline": course_compare.iloc[0]["course_name"],
            "course_decline_value": float(course_compare.iloc[0]["completion_rate_delta"])
        }
    )

    provenance_path = save_record(record, "provenance_compare.json")
    print(f"\nSaved provenance record: {provenance_path.name}")

if __name__ == "__main__":
    main()