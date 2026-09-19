import os
import django
import sys

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

sys.path.insert(0, PROJECT_ROOT)



os.environ.setdefault("DJANGO_SETTINGS_MODULE", "TrafficAI.settings")
django.setup()

from predictions.services import update_all_locations

try:
    print("Starting TrafficAI update...")
    update_all_locations()
    print("Finished.")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    input("Press Enter to close...")  # keeps window open so you can read the error