import sys
import os
# import verification_utils removed
import datetime

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from services.pcloud_onboarding_service import pcloud_onboarding_service
from services.pcloud_service import pcloud_service

def verify_onboarding_loading():
    print("=== 1. Verifying Service Loading ===")
    try:
        if pcloud_onboarding_service:
            print("✅ Service loaded successfully")
        else:
            print("❌ Service failed to load")
    except Exception as e:
        print(f"❌ Error loading service: {e}")

def verify_watcher_config():
    print("\n=== 2. Verifying Watcher Configuration ===")
    from services.pcloud_onboarding_service import pcloud_onboarding_watcher
    status = pcloud_onboarding_watcher.status
    print(f"Watcher Status: {status}")
    if status['interval_seconds'] == 300:
        print("✅ Default interval correct (300s)")
    else:
        print(f"❌ Default interval incorrect: {status['interval_seconds']}")

def verify_pcloud_methods():
    print("\n=== 3. Verifying required pCloud methods ===")
    methods = [
        'move_folder',
        'rename_folder',
        'get_or_create_folder',
        'list_folder'
    ]
    
    for method in methods:
        if hasattr(pcloud_service, method):
            print(f"✅ pcloud_service has method: {method}")
        else:
            print(f"❌ pcloud_service missing method: {method}")

if __name__ == "__main__":
    print(f"Starting Verification at {datetime.datetime.now()}")
    verify_onboarding_loading()
    verify_watcher_config()
    verify_pcloud_methods()
    print("\nVerification Complete.")
