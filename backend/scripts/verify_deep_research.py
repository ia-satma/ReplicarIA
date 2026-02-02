import sys
import os
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO)

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

print("--- Verifying Deep Research Service Import ---")

try:
    from services.deep_research_service import deep_research_service, DeepResearchService
    print("✅ SUCCESS: Module imported successfully")
    
    if deep_research_service:
        print(f"✅ SUCCESS: deep_research_service instance created")
        print(f"   - Available: {deep_research_service.available}")
        print(f"   - Provider: {deep_research_service.provider}")
        
        # Verify the critical method exists
        if hasattr(deep_research_service, '_extraer_datos_con_regex'):
             print("✅ SUCCESS: Method '_extraer_datos_con_regex' found")
        else:
             print("❌ FAILURE: Method '_extraer_datos_con_regex' is MISSING")
    else:
        print("❌ FAILURE: deep_research_service is None")

except Exception as e:
    print(f"❌ CRITICAL FAILURE during import: {e}")
    import traceback
    traceback.print_exc()
