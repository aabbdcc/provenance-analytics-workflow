from pathlib import Path
import subprocess
import sys

# --- Configuration ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"

SCRIPTS = [
    "generate_sample_data.py",
    "check_data.py",
    "aggregate.py",
    "compare_aggregates.py",
    "summarize.py",
]


def run_script(script_name: str) -> None:
    """
    Run one Python script from the src directory.
    Stop the pipeline if the script fails.
    """
    script_path = SRC_DIR / script_name

    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")

    print("\n" + "=" * 70)
    print(f"Running: {script_name}")
    print("=" * 70)

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(PROJECT_ROOT),
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"Step failed: {script_name}")

    print(f"\nFinished: {script_name}")


def main():
    print("\nStarting workflow pipeline")
    print("-" * 70)

    for script in SCRIPTS:
        run_script(script)

    print("\n" + "-" * 70)
    print("Pipeline completed successfully.")
    print("Main outputs are available in the outputs/ directory.")
    print("-" * 70)


if __name__ == "__main__":
    main()