
import asyncio
import os
import sys
import logging
import time

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VerifyRemediation")

async def verify_pdf_export_non_blocking():
    logger.info("--- Testing PDF Export (Non-blocking) ---")
    try:
        from backend.services.defense_file_export_service import defense_file_export_service
        
        # Mock data
        data = {
            "project_id": "TEST-001", 
            "titulo": "Test Project",
            "secciones": {
                "contexto": {"razon_negocios_descripcion": "Test"},
                "contractual": {"monto_total": 1000},
            }
        }
        
        start_time = time.time()
        
        # Start PDF generation
        task = asyncio.create_task(defense_file_export_service.generate_defense_file_pdf(data))
        
        # Check if event loop is blocked
        accumulated_sleep = 0
        while not task.done():
            sleep_start = time.time()
            await asyncio.sleep(0.1)
            sleep_duration = time.time() - sleep_start
            accumulated_sleep += 0.1
            
            # If sleep takes significantly longer than 0.1s + overhead, loop was blocked
            if sleep_duration > 0.5: 
                logger.error(f"Event loop blocked! Sleep(0.1) took {sleep_duration:.2f}s")
                return False
                
        # await task
        pdf_buffer = await task
        duration = time.time() - start_time
        logger.info(f"PDF generated in {duration:.2f}s without blocking event loop.")
        return True
        
    except Exception as e:
        logger.error(f"PDF Export Test Failed: {e}")
        return False

async def verify_sat_cache():
    logger.info("--- Testing SAT Cache ---")
    try:
        from backend.services.tools.compliance_tools import query_sat_lista_69b
        
        # First call (might hit disk/network)
        start1 = time.time()
        res1 = query_sat_lista_69b("AAA010101AAA")
        dur1 = time.time() - start1
        logger.info(f"Call 1 (Cold/Disk): {dur1:.4f}s")
        
        # Second call (should be Memory RAW)
        start2 = time.time()
        res2 = query_sat_lista_69b("BBB010101AAA")
        dur2 = time.time() - start2
        logger.info(f"Call 2 (Warm/Memory): {dur2:.4f}s")
        
        if dur2 > 0.1: # Should be microsecond level if in memory
            logger.error("Cache might not be working efficiently (>100ms for memory fetch)")
            return False
            
        logger.info("SAT Cache working correctly.")
        return True
        
    except Exception as e:
        logger.error(f"SAT Cache Test Failed: {e}")
        return False

async def main():
    logger.info("Starting Verification...")
    
    pdf_ok = await verify_pdf_export_non_blocking()
    sat_ok = await verify_sat_cache()
    
    if pdf_ok and sat_ok:
        logger.info("✅ ALL REMEDIATION CHECKS PASSED")
    else:
        logger.error("❌ SOME CHECKS FAILED")

if __name__ == "__main__":
    asyncio.run(main())
