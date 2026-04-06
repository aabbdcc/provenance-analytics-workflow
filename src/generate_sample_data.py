import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

SEED = 20260113
np.random.seed(SEED)


def sigmoid(x):
    return 1 / (1 + np.exp(-x))


def random_date(start: datetime, max_days: int) -> datetime:
    """
    Return a random datetime between start and end.
    """
    return start + timedelta(days=int(np.random.randint(0, max_days)))


def simulate_learning_data(n_obs=350, version="baseline"):
    """
    Simulate learning analytics data for a provenance/reproducibility demo.
    
    version:
        - "baseline"
        - "v2_policy_shift"
    """
    countries = ["France", "Germany", "Spain", "Italy", "Netherlands"]
    departments = [
        "Sales Training West",
        "Sales Training East",
        "HR Learning",
        "Operations Academy",
        "Digital Learning",
        "Leadership Programs"
    ]

    courses = {
        "Power BI Fundamentals": {"cat": "Analytics", "difficulty": 0.8},
        "Azure Basics": {"cat": "Cloud", "difficulty": 1.2},
        "Compliance Essentials": {"cat": "Compliance", "difficulty": 0.5},
        "Leadership 101": {"cat": "Management", "difficulty": 0.9},
        "Python for Business": {"cat": "Analytics", "difficulty": 1.5},
        "Data Storytelling": {"cat": "Analytics", "difficulty": 0.9},
    }

    course_names = list(courses.keys())
    rows = []

    base_start = datetime(2025, 9, 1)

    for i in range(n_obs):
        user_id = f"U{1000 + i}"
        country = np.random.choice(countries)
        department = np.random.choice(departments)
        course_name = np.random.choice(course_names)

        course_category = courses[course_name]["cat"]
        difficulty = courses[course_name]["difficulty"]

        # Base completion logic
        base_logit = 1.0 - 0.9 * difficulty + np.random.normal(0, 0.25)

        # Version-specific shifts
        if version == "v2_policy_shift":
            if country == "Germany":
                base_logit -= 0.7
            if department == "Sales Training West":
                base_logit -= 0.5
            if course_name == "Azure Basics":
                base_logit -= 0.4

        p_completed = sigmoid(base_logit)

        # Build 3-class probabilities safely
        p_completed = np.clip(p_completed, 0.15, 0.85)
        p_in_progress = np.clip(0.20 + np.random.normal(0, 0.03), 0.10, 0.30)
        p_not_started = 1 - p_completed - p_in_progress

        # Ensure valid probabilities
        if p_not_started < 0.05:
            p_not_started = 0.05
            total = p_completed + p_in_progress + p_not_started
            p_completed /= total
            p_in_progress /= total
            p_not_started /= total

        probs = np.array([p_completed, p_in_progress, p_not_started], dtype=float)
        probs = probs / probs.sum()

        status = np.random.choice(
            ["completed", "in_progress", "not_started"],
            p=probs
        )

        enrollment_date = random_date(base_start, 120)
        last_activity_date = enrollment_date + timedelta(days=int(np.random.randint(0, 45)))

        if status == "completed":
            progress_pct = int(np.random.randint(95, 101))
            completion_date = last_activity_date + timedelta(days=int(np.random.randint(1, 10)))
            time_spent_hours = round(np.random.gamma(shape=5, scale=2), 1)
        elif status == "in_progress":
            progress_pct = int(np.random.randint(20, 85))
            completion_date = pd.NaT
            time_spent_hours = round(np.random.uniform(2.0, 8.0), 1)
        else:
            progress_pct = int(np.random.randint(0, 15))
            completion_date = pd.NaT
            time_spent_hours = round(np.random.uniform(0.0, 2.0), 1)

        # Extra weakening in v2 for Azure Basics
        if version == "v2_policy_shift" and course_name == "Azure Basics":
            time_spent_hours = round(time_spent_hours * 0.7, 1)

        rows.append({
            "user_id": user_id,
            "country": country,
            "department": department,
            "course_name": course_name,
            "course_category": course_category,
            "status": status,
            "progress_pct": progress_pct,
            "completion_date": completion_date,
            "time_spent_hours": time_spent_hours,
            "last_activity_date": last_activity_date,
            "enrollment_date": enrollment_date,
            "dataset_version": "2026-01-05" if version == "baseline" else "2026-01-13"
        })

    df = pd.DataFrame(rows)

    # Inject 5% missing values only in time_spent_hours
    missing_mask = np.random.rand(len(df)) < 0.05
    df.loc[missing_mask, "time_spent_hours"] = np.nan

    # Convert dates to date-only format
    for col in ["completion_date", "last_activity_date", "enrollment_date"]:
        df[col] = pd.to_datetime(df[col]).dt.date

    return df


def quick_checks(df, label="DATA"):
    print(f"\n===== {label} =====")
    overall_completion = (df["status"] == "completed").mean()
    print(f"Overall completion rate: {overall_completion:.2%}")

    print("\nCompletion rate by country:")
    print(
        df.groupby("country")["status"]
        .apply(lambda x: (x == "completed").mean())
        .sort_values()
    )

    print("\nCompletion rate by department:")
    print(
        df.groupby("department")["status"]
        .apply(lambda x: (x == "completed").mean())
        .sort_values()
    )

    print("\nCompletion rate by course:")
    print(
        df.groupby("course_name")["status"]
        .apply(lambda x: (x == "completed").mean())
        .sort_values()
    )


def main():
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "data"
    data_dir.mkdir(exist_ok=True)

    df_v1 = simulate_learning_data(n_obs=350, version="baseline")
    df_v2 = simulate_learning_data(n_obs=350, version="v2_policy_shift")

    file_v1 = data_dir / "sample_learning_data.csv"
    file_v2 = data_dir / "sample_learning_data_v2.csv"

    df_v1.to_csv(file_v1, index=False)
    print(f"Saved: {file_v1}")
    quick_checks(df_v1, "V1 BASELINE")

    df_v2.to_csv(file_v2, index=False)
    print(f"\nSaved: {file_v2}")
    quick_checks(df_v2, "V2 POLICY SHIFT")


if __name__ == "__main__":
    main()