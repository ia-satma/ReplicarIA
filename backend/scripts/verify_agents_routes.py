
import asyncio
import sys
import os
from datetime import datetime

# Add backend to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from routes.agents_stats_routes import get_agent_stats, get_stats_by_agent, get_recent_deliberations

async def verify():
    print("--- Verifying get_agent_stats ---")
    stats = await get_agent_stats()
    print(stats)

    print("\n--- Verifying get_stats_by_agent ---")
    by_agent = await get_stats_by_agent()
    print(by_agent)
    
    print("\n--- Verifying get_recent_deliberations ---")
    recent = await get_recent_deliberations(limit=5)
    print(recent)

if __name__ == "__main__":
    asyncio.run(verify())
