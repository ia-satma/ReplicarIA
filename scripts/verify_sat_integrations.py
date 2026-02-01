
import asyncio
import json
import logging
import os
from services.tools.registry import registry
# Import tools to register them
import services.tools.financial_tools
import services.tools.compliance_tools

# Configure logging to see what's happening
logging.basicConfig(level=logging.INFO)

async def test_real_tools():
    print("Testing Real Tools...")
    
    # 1. Test SAT 69-B (Downloads ~15MB CSV, might take a moment)
    print("\n--- Testing SAT 69-B Download & Search ---")
    
    # Test with a known random RFC likely NOT in the list
    start_rfc = "AAA010101AAA" # Generic Test RFC
    print(f"Checking {start_rfc} (Should be clean)...")
    res_clean = await registry.invoke("query_sat_lista_69b", {"rfc": start_rfc})
    print(f"Result: {json.dumps(res_clean, indent=2)}")
    
    # Note: Validating a positive hit is hard without a known bad RFC that is currently in the list
    # The list is dynamic. But if the download worked, the 'checked_against' field will show > 0 records.
    
    if res_clean.get("checked_against", "").replace(" records", "") == "0":
         print("⚠️ WARNING: Blacklist seems empty. Download might have failed.")
    
    # 2. Test SAT SOAP CFDI
    print("\n--- Testing SAT CFDI SOAP Service ---")
    
    # Uses a testing UUID/RFC/Totals. 
    # Since we don't have a real valid UUID handy that matches exact amounts, 
    # we expect "No Encontrado" but NOT "Error de Conexión".
    
    test_cfdi = {
        "uuid": "5fb0985f-8c01-49ae-9372-8f9293817345", # Random UUID
        "monto": 100.00,
        "rfc_emisor": "AAA010101AAA",
        "rfc_receptor": "XXX010101000"
    }
    
    print(f"Checking random CFDI (Expect 'No Encontrado' but successful connection)...")
    res_cfdi = await registry.invoke("validate_cfdi", test_cfdi)
    print(f"Result: {json.dumps(res_cfdi, indent=2)}")

    if res_cfdi.get("status_sat") == "Error de Conexión":
        print("❌ SOAP Connection Failed")
    else:
        print("✅ SOAP Connection Successful (Response received)")

if __name__ == "__main__":
    asyncio.run(test_real_tools())
