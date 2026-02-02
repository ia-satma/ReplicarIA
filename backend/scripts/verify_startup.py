import asyncio
from unittest.mock import MagicMock, patch
import logging

# Mock logging to avoid clutter
logging.basicConfig(level=logging.INFO)

async def test_startup():
    print("🧪 Testing Startup Logic...")
    
    # Mock services
    with patch('services.pcloud_service.pcloud_service') as mock_pcloud:
        mock_pcloud.is_available.return_value = True
        mock_pcloud.initialize_folder_structure.return_value = {
            "success": True, 
            "created_folders": ["A"], 
            "existing_folders": ["B"]
        }
        
        with patch('services.pcloud_onboarding_service.pcloud_onboarding_watcher') as mock_watcher:
            print("🚀 Importing app lifespan...")
            from server import lifespan
            
            # Simulate lifespan
            app_mock = MagicMock()
            async with lifespan(app_mock):
                print("✅ Startup complete")
                
                # Verify pCloud init was called
                if mock_pcloud.initialize_folder_structure.called:
                    print("✅ pCloud structure initialization triggered")
                else:
                    print("❌ pCloud structure initialization NOT triggered")
                    
                # Verify Watcher started
                if mock_watcher.start.called:
                    print("✅ Onboarding Watcher started")
                else:
                    print("❌ Onboarding Watcher NOT started")

            print("✅ Shutdown complete")
            # Verify Watcher stopped
            if mock_watcher.stop.called:
                print("✅ Onboarding Watcher stopped")

if __name__ == "__main__":
    asyncio.run(test_startup())
