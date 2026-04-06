import pandas as pd

from pathlib import Path
from provenance import create_run, add_step, save_record

# --- Configuration ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

V1_FILE = "sample_learning_data.csv"
V2_FILE = "sample_learning_data_v2.csv"


def load_dataset(filename: str) -> pd.DataFrame:
    """
    Load a dataset from the data directory.
    """
    file_path = DATA_DIR / filename
    if not file_path.exists():
        raise FileNotFoundError(f"Dataset not found: {file_path}")

    df = pd.read_csv(file_path)
    return df


def preprocess_learning_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Minimal preprocessing before aggregation.

    Research note:
    This corresponds to a lightweight transformation step in the workflow,
    preparing the dataset for consistent KPI computation.
    """
    df = df.copy()

    # Binary outcome for completion
    df["is_completed"] = (df["status"] == "completed").astype(int)

    # Active learner = completed or in progress
    df["is_active"] = df["status"].isin(["completed", "in_progress"]).astype(int)

    # Numeric normalization
    df["time_spent_hours"] = pd.to_numeric(df["time_spent_hours"], errors="coerce")
    df["progress_pct"] = pd.to_numeric(df["progress_pct"], errors="coerce")

    # Missing flag for hours spent
    df["hours_missing"] = df["time_spent_hours"].isna().astype(int)

    return df


def aggregate_by_dimension(df: pd.DataFrame, group_col: str, overall_completion_rate: float) -> pd.DataFrame:
    """
    Aggregate key metrics by a single dimension.

    Metrics:
    - learner_count
    - completion_rate
    - completion_gap_vs_overall
    - active_learner_ratio
    - avg_progress_pct
    - avg_time_spent_hours
    - missing_hours_ratio
    """
    agg_df = (
        df.groupby(group_col, dropna=False)
        .agg(
            learner_count=("user_id", "count"),
            completion_rate=("is_completed", "mean"),
            active_learner_ratio=("is_active", "mean"),
            avg_progress_pct=("progress_pct", "mean"),
            avg_time_spent_hours=("time_spent_hours", "mean"),
            missing_hours_ratio=("hours_missing", "mean"),
        )
        .reset_index()
    )

    agg_df["completion_gap_vs_overall"] = agg_df["completion_rate"] - overall_completion_rate

    # Reorder columns for readability
    agg_df = agg_df[
        [
            group_col,
            "learner_count",
            "completion_rate",
            "completion_gap_vs_overall",
            "active_learner_ratio",
            "avg_progress_pct",
            "avg_time_spent_hours",
            "missing_hours_ratio",
        ]
    ]

    # Sort by completion rate ascending so weaker performers appear first
    agg_df = agg_df.sort_values(by="completion_rate", ascending=True)

    return agg_df


def compute_overall_summary(df: pd.DataFrame) -> dict:
    """
    Compute high-level overall metrics for the dataset.
    """
    summary = {
        "dataset_version": df["dataset_version"].iloc[0] if "dataset_version" in df.columns else "unknown",
        "row_count": len(df),
        "completion_rate": df["is_completed"].mean(),
        "active_learner_ratio": df["is_active"].mean(),
        "avg_progress_pct": df["progress_pct"].mean(),
        "avg_time_spent_hours": df["time_spent_hours"].mean(),
        "missing_hours_ratio": df["hours_missing"].mean(),
    }
    return summary


def extract_top_anomalies(country_df: pd.DataFrame, dept_df: pd.DataFrame, course_df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract a compact anomaly table from the weakest-performing entities.

    Current logic:
    - lowest completion country
    - lowest completion department
    - lowest completion course
    """
    anomalies = []

    weakest_country = country_df.iloc[0]
    anomalies.append({
        "dimension": "country",
        "entity": weakest_country["country"],
        "issue_type": "lowest_completion_rate",
        "completion_rate": weakest_country["completion_rate"],
        "completion_gap_vs_overall": weakest_country["completion_gap_vs_overall"],
        "missing_hours_ratio": weakest_country["missing_hours_ratio"],
    })

    weakest_department = dept_df.iloc[0]
    anomalies.append({
        "dimension": "department",
        "entity": weakest_department["department"],
        "issue_type": "lowest_completion_rate",
        "completion_rate": weakest_department["completion_rate"],
        "completion_gap_vs_overall": weakest_department["completion_gap_vs_overall"],
        "missing_hours_ratio": weakest_department["missing_hours_ratio"],
    })

    weakest_course = course_df.iloc[0]
    anomalies.append({
        "dimension": "course",
        "entity": weakest_course["course_name"],
        "issue_type": "lowest_completion_rate",
        "completion_rate": weakest_course["completion_rate"],
        "completion_gap_vs_overall": weakest_course["completion_gap_vs_overall"],
        "missing_hours_ratio": weakest_course["missing_hours_ratio"],
    })

    anomalies_df = pd.DataFrame(anomalies)
    return anomalies_df


def save_outputs(
    country_df: pd.DataFrame,
    dept_df: pd.DataFrame,
    course_df: pd.DataFrame,
    anomalies_df: pd.DataFrame,
    summary_dict: dict,
    prefix: str
) -> None:
    """
    Save aggregation outputs to the outputs directory.
    """
    OUTPUT_DIR.mkdir(exist_ok=True)

    country_df.to_csv(OUTPUT_DIR / f"{prefix}_country_metrics.csv", index=False)
    dept_df.to_csv(OUTPUT_DIR / f"{prefix}_department_metrics.csv", index=False)
    course_df.to_csv(OUTPUT_DIR / f"{prefix}_course_metrics.csv", index=False)
    anomalies_df.to_csv(OUTPUT_DIR / f"{prefix}_top_anomalies.csv", index=False)

    summary_df = pd.DataFrame([summary_dict])
    summary_df.to_csv(OUTPUT_DIR / f"{prefix}_overall_summary.csv", index=False)


def print_summary_block(summary_dict: dict) -> None:
    """
    Pretty-print the overall summary.
    """
    print("\n[Descriptive Statistics] Overall Workflow Summary")
    print(f"Dataset version       : {summary_dict['dataset_version']}")
    print(f"Row count             : {summary_dict['row_count']}")
    print(f"Completion rate       : {summary_dict['completion_rate']:.2%}")
    print(f"Active learner ratio  : {summary_dict['active_learner_ratio']:.2%}")
    print(f"Average progress      : {summary_dict['avg_progress_pct']:.2f}")
    print(f"Average time spent    : {summary_dict['avg_time_spent_hours']:.2f}")
    print(f"Missing hours ratio   : {summary_dict['missing_hours_ratio']:.2%}")


def print_anomaly_block(country_df: pd.DataFrame, dept_df: pd.DataFrame, course_df: pd.DataFrame) -> None:
    """
    Print lightweight anomaly inspection blocks.
    """
    print("\n[Hypothesis-Oriented Inspection] Lowest-performing countries")
    print(country_df.head(3).to_string(index=False))

    print("\n[Hypothesis-Oriented Inspection] Lowest-performing departments")
    print(dept_df.head(3).to_string(index=False))

    print("\n[Hypothesis-Oriented Inspection] Lowest-performing courses")
    print(course_df.head(3).to_string(index=False))


def run_aggregation(filename: str, prefix: str) -> None:
    """
    Full aggregation pipeline for one dataset version.
    """
    print(f"\n--- Running aggregation for: {filename} ---")

    df = load_dataset(filename)
    df = preprocess_learning_data(df)

    dataset_version = df["dataset_version"].iloc[0] if "dataset_version" in df.columns else "unknown"

    # --- Initialize provenance record ---
    record = create_run(
        run_id=f"run_aggregate_{prefix}",
        workflow_name="learning_reporting_aggregation",
        workflow_version="v1.0",
        dataset_version=dataset_version,
        input_files=[filename]
    )

    record = add_step(
        record=record,
        step_name="load_and_preprocess_dataset",
        step_type="transformation",
        input_files=[filename],
        output_files=[],
        parameters={
            "derived_columns": ["is_completed", "is_active", "hours_missing"]
        },
        row_count_in=None,
        row_count_out=len(df),
        observations={
            "dataset_version": dataset_version
        }
    )

    overall_summary = compute_overall_summary(df)
    overall_completion_rate = overall_summary["completion_rate"]

    country_metrics = aggregate_by_dimension(df, "country", overall_completion_rate)
    department_metrics = aggregate_by_dimension(df, "department", overall_completion_rate)
    course_metrics = aggregate_by_dimension(df, "course_name", overall_completion_rate)

    anomalies_df = extract_top_anomalies(country_metrics, department_metrics, course_metrics)

    save_outputs(
        country_df=country_metrics,
        dept_df=department_metrics,
        course_df=course_metrics,
        anomalies_df=anomalies_df,
        summary_dict=overall_summary,
        prefix=prefix
    )

    # --- Add aggregation steps to provenance ---
    record = add_step(
        record=record,
        step_name="aggregate_country_metrics",
        step_type="aggregation",
        input_files=[filename],
        output_files=[f"{prefix}_country_metrics.csv"],
        parameters={"group_by": "country"},
        row_count_in=len(df),
        row_count_out=len(country_metrics),
        observations={
            "lowest_country": country_metrics.iloc[0]["country"],
            "lowest_country_completion_rate": float(country_metrics.iloc[0]["completion_rate"])
        }
    )

    record = add_step(
        record=record,
        step_name="aggregate_department_metrics",
        step_type="aggregation",
        input_files=[filename],
        output_files=[f"{prefix}_department_metrics.csv"],
        parameters={"group_by": "department"},
        row_count_in=len(df),
        row_count_out=len(department_metrics),
        observations={
            "lowest_department": department_metrics.iloc[0]["department"],
            "lowest_department_completion_rate": float(department_metrics.iloc[0]["completion_rate"])
        }
    )

    record = add_step(
        record=record,
        step_name="aggregate_course_metrics",
        step_type="aggregation",
        input_files=[filename],
        output_files=[f"{prefix}_course_metrics.csv"],
        parameters={"group_by": "course_name"},
        row_count_in=len(df),
        row_count_out=len(course_metrics),
        observations={
            "lowest_course": course_metrics.iloc[0]["course_name"],
            "lowest_course_completion_rate": float(course_metrics.iloc[0]["completion_rate"])
        }
    )

    record = add_step(
        record=record,
        step_name="extract_top_anomalies",
        step_type="inspection",
        input_files=[
            f"{prefix}_country_metrics.csv",
            f"{prefix}_department_metrics.csv",
            f"{prefix}_course_metrics.csv"
        ],
        output_files=[f"{prefix}_top_anomalies.csv"],
        parameters={"selection_rule": "lowest completion rate per dimension"},
        row_count_in=len(country_metrics) + len(department_metrics) + len(course_metrics),
        row_count_out=len(anomalies_df),
        observations={
            "top_anomalies_count": int(len(anomalies_df))
        }
    )

    record = add_step(
        record=record,
        step_name="save_aggregation_outputs",
        step_type="export",
        input_files=[filename],
        output_files=[
            f"{prefix}_country_metrics.csv",
            f"{prefix}_department_metrics.csv",
            f"{prefix}_course_metrics.csv",
            f"{prefix}_top_anomalies.csv",
            f"{prefix}_overall_summary.csv"
        ],
        parameters={"output_dir": "outputs"},
        row_count_in=len(df),
        row_count_out=None,
        observations={
            "completion_rate": float(overall_summary["completion_rate"]),
            "active_learner_ratio": float(overall_summary["active_learner_ratio"]),
            "missing_hours_ratio": float(overall_summary["missing_hours_ratio"])
        }
    )

    provenance_path = save_record(record, f"provenance_{prefix}_aggregation.json")

    print_summary_block(overall_summary)
    print_anomaly_block(country_metrics, department_metrics, course_metrics)

    print(f"\nSaved aggregation outputs with prefix: {prefix}")
    print(f"Saved provenance record: {provenance_path.name}")

def main():
    run_aggregation(V1_FILE, prefix="v1")
    run_aggregation(V2_FILE, prefix="v2")


if __name__ == "__main__":
    main()