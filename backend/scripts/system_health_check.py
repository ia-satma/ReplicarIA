
import asyncio
import os
import sys
import logging
import requests
import asyncpg
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("SystemHealth")

# Add backend to path to import services
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# Load Env (Mocking for script if needed, but assuming env vars are set or .env is present)
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

DATABASE_URL = os.getenv("DATABASE_URL")
SAT_69B_URL = "http://omawww.sat.gob.mx/cifras_sat/Documents/Listado_Completo_69-B.csv"

async def check_database():
    logger.info("--- 1. Checking Database Connectivity ---")
    if not DATABASE_URL:
        logger.error("❌ DATABASE_URL not found in env.")
        return False
    
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        version = await conn.fetchval("SELECT version()")
        await conn.close()
        logger.info(f"✅ Database Connected: {version}")
        return True
    except Exception as e:
        logger.error(f"❌ Database Connection Failed: {e}")
        return False

def check_sat_connectivity():
    logger.info("--- 2. Checking SAT Connectivity ---")
    try:
        start = datetime.now()
        # Head request to check availability without downloading all
        response = requests.head(SAT_69B_URL, timeout=10)
        duration = (datetime.now() - start).total_seconds()
        
        if response.status_code == 200:
            logger.info(f"✅ SAT LISTA 69-B Endpoint Reachable ({duration:.2f}s)")
            return True
        else:
            logger.warning(f"⚠️ SAT Endpoint returned status: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ SAT Connectivity Failed: {e}")
        return False

async def check_agents():
    logger.info("--- 3. Checking Agent Configuration ---")
    try:
        from backend.services.agent_orchestrator import AGENTS_CONFIG, get_orchestrator
        
        orchestrator = get_orchestrator()
        agent_count = len(orchestrator.agents)
        logger.info(f"✅ Agent Orchestrator Loaded. Agents Configured: {agent_count}")
        
        # Verify critical agents exist
        critical_agents = ["A1_RECEPCION", "A2_ANALISIS", "A3_NORMATIVO", "A9_SINTESIS"]
        missing = [a for a in critical_agents if a not in orchestrator.agents]
        
        if missing:
            logger.error(f"❌ Missing Critical Agents: {missing}")
            return False
            
        for agent_id, config in orchestrator.agents.items():
            if not config.get("system_prompt"):
                logger.error(f"❌ Agent {agent_id} has no system_prompt")
                return False
        
        logger.info(f"✅ All {agent_count} Agents have valid configurations.")
        return True
        
    except ImportError as e:
        logger.error(f"❌ Could not import Agent Orchestrator: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Agent Check Failed: {e}")
        return False

async def main():
    logger.info("Starting System Health Check...")
    print("-" * 50)
    
    db_ok = await check_database()
    sat_ok = check_sat_connectivity()
    agents_ok = await check_agents()
    
    print("-" * 50)
    if db_ok and sat_ok and agents_ok:
        logger.info("🟢 SYSTEM STATUS: HEALTHY")
        sys.exit(0)
    else:
        logger.error("🔴 SYSTEM STATUS: UNHEALTHY")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
