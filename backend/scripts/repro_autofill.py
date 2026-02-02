
import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.deep_research_service import deep_research_service
from services.anthropic_provider import is_configured

async def test_autofill():
    print("Testing Deep Research Service directly...")
    
    if not deep_research_service:
        print("❌ Deep Research Service NOT loaded (ImportError check failed)")
        return

    try:
        print("🔍 Starting investigation for 'fortezza.mx'...")
        result = await deep_research_service.investigar_empresa(
            nombre="Grupo Fortezza",
            sitio_web="https://fortezza.mx/"
        )
        print("✅ Result received:")
        print(result)
        
    except Exception as e:
        print(f"❌ Error during investigation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_autofill())
