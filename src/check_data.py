import pandas as pd
from pathlib import Path

# --- Configuration ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data"
V1_FILE = "sample_learning_data.csv"
V2_FILE = "sample_learning_data_v2.csv"


def load_and_preprocess(filename: str) -> pd.DataFrame:
    path = DATA_PATH / filename
    if not path.exists():
        raise FileNotFoundError(f"Missing experimental data: {path}")
    df = pd.read_csv(path)
    return df


def calculate_metrics(df: pd.DataFrame, label="Group"):
    """
    Compute descriptive metrics for workflow comparison.
    """
    df = df.copy()
    df["is_completed"] = (df["status"] == "completed").astype(int)

    overall_cr = df["is_completed"].mean()

    country_stats = df.groupby("country")["is_completed"].mean().sort_values()
    dept_stats = df.groupby("department")["is_completed"].mean().sort_values()
    course_stats = df.groupby("course_name")["is_completed"].mean().sort_values()

    avg_hours = df["time_spent_hours"].mean()

    return {
        "cr": overall_cr,
        "country": country_stats,
        "dept": dept_stats,
        "course": course_stats,
        "hours": avg_hours
    }


def main():
    try:
        df_base = load_and_preprocess(V1_FILE)
        df_shift = load_and_preprocess(V2_FILE)
    except Exception as e:
        print(f"[Error] {e}")
        return

    res_v1 = calculate_metrics(df_base, "Baseline")
    res_v2 = calculate_metrics(df_shift, "Policy_Shift")

    print("-" * 60)
    print("Descriptive Statistics: Workflow Comparison Across Dataset Versions")
    print("-" * 60)
    print(f"Overall completion rate - V1: {res_v1['cr']:.2%}")
    print(f"Overall completion rate - V2: {res_v2['cr']:.2%}")

    if res_v1["cr"] != 0:
        rel_change = (res_v2["cr"] - res_v1["cr"]) / res_v1["cr"]
    else:
        rel_change = 0

    print(f"Relative change           : {rel_change:.2%}")
    print(f"Average time spent - V1   : {res_v1['hours']:.2f}")
    print(f"Average time spent - V2   : {res_v2['hours']:.2f}")

    print("\n[Hypothesis Check] Geographic Heterogeneity (Focus: Germany)")
    de_delta = res_v2["country"].get("Germany", 0) - res_v1["country"].get("Germany", 0)
    print(f"Germany completion delta  : {de_delta:.2%}")

    print("\n[Hypothesis Check] Departmental Variation (Focus: Sales Training West)")
    sw_delta = res_v2["dept"].get("Sales Training West", 0) - res_v1["dept"].get("Sales Training West", 0)
    print(f"Sales Training West delta : {sw_delta:.2%}")

    print("\n[Hypothesis Check] Course-Level Variation (Focus: Azure Basics)")
    az_delta = res_v2["course"].get("Azure Basics", 0) - res_v1["course"].get("Azure Basics", 0)
    print(f"Azure Basics delta        : {az_delta:.2%}")

    print("\nPreliminary Observation:")
    if res_v2["cr"] < res_v1["cr"]:
        print(">>> The updated dataset version shows a clear decline in completion outcomes.")
    else:
        print(">>> No overall decline is observed in the updated dataset version.")

    print("\nLowest completion rates in V2 by country:")
    print(res_v2["country"].head(3))

    print("\nLowest completion rates in V2 by department:")
    print(res_v2["dept"].head(3))

    print("\nLowest completion rates in V2 by course:")
    print(res_v2["course"].head(3))


if __name__ == "__main__":
    main()