import subprocess
import sys


def run_script(script):
    print()
    print("=" * 60)
    print(f"RUNNING: {script}")
    print("=" * 60)

    subprocess.run(
        [sys.executable, script],
        check=True
    )


try:
    # 1. Get fresh API data
    run_script("scripts/run_update.py")

    # 2. Build/update ML dataset
    run_script("scripts/prepare_dataset.py")

    # 3. Train models
    run_script("scripts/train_model.py")

    # 4. Generate predictions
    run_script("scripts/predict_traffic.py")

    print()
    print("=" * 60)
    print("TRAFFICAI PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 60)

except subprocess.CalledProcessError as error:

    print()
    print("=" * 60)
    print("TRAFFICAI PIPELINE FAILED")
    print("=" * 60)

    print(f"Script exited with code: {error.returncode}")