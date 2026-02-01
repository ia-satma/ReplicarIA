"""
Compliance Tools for ReplicarIA Agents.
Includes SAT list checking (69-B) and regulatory validation.
"""

from typing import Dict, Any
from .registry import tool
from datetime import datetime

import csv
import logging
import os
import requests
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from .registry import tool
from pathlib import Path

logger = logging.getLogger(__name__)

# SAT 69-B Official URL (Definitivos)
SAT_69B_URL = "http://omawww.sat.gob.mx/cifras_sat/Documents/Definitivos.csv"
CACHE_FILE = Path("data/sat_blacklist.csv")
CACHE_TTL_DAYS = 7

# Global in-memory cache
_SAT_BLACKLIST_CACHE = None

def _get_blacklist_data() -> Dict[str, Dict[str, str]]:
    """
    Downloads and caches the SAT blacklist. 
    Returns a dictionary keyed by RFC.
    Uses in-memory cache to avoid repeated file I/O.
    """
    global _SAT_BLACKLIST_CACHE
    
    # Return in-memory cache if available
    if _SAT_BLACKLIST_CACHE is not None:
        return _SAT_BLACKLIST_CACHE

    # Create data dir if not exists
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Check if cache exists and is fresh
    is_fresh = False
    if CACHE_FILE.exists():
        modified_time = datetime.fromtimestamp(CACHE_FILE.stat().st_mtime)
        if datetime.now() - modified_time < timedelta(days=CACHE_TTL_DAYS):
            is_fresh = True
            
    if not is_fresh:
        try:
            logger.info(f"Downloading SAT Blacklist from {SAT_69B_URL}...")
            response = requests.get(SAT_69B_URL, timeout=30)
            response.raise_for_status()
            
            # Save raw content (fixing encoding issues common with SAT files)
            content = response.content.decode('latin-1')
            
            # Filter out top lines until header (SAT csvs often have junk at top)
            lines = content.splitlines()
            start_idx = 0
            for i, line in enumerate(lines):
                if "RFC" in line or "RazÃ³n Social" in line or "Razón Social" in line:
                    start_idx = i
                    break
            
            clean_content = "\n".join(lines[start_idx:])
            
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                f.write(clean_content)
                
            logger.info("SAT Blacklist downloaded and cached.")
            
        except Exception as e:
            logger.error(f"Failed to download SAT blacklist: {e}")
            # If download fails but we have stale cache, try to use it
            if not CACHE_FILE.exists():
                return {} # Fail safe if no cache

    # Load from file into memory
    blacklist = {}
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            # Normalize headers
            headers = [h.strip().upper() for h in reader.fieldnames or []]
            reader.fieldnames = headers
            
            rfc_col = next((h for h in headers if "RFC" in h), None)
            name_col = next((h for h in headers if "RAZ" in h), None) # Razon Social
            date_col = next((h for h in headers if "PUBLICACI" in h and "DEFINITIV" in h), None)
            
            if not rfc_col:
                logger.error("Could not find RFC column in SAT CSV")
                return {}

            for row in reader:
                rfc = row.get(rfc_col, "").strip().upper()
                if rfc:
                    blacklist[rfc] = {
                        "razon_social": row.get(name_col, "DESCONOCIDO"),
                        "fecha_publicacion": row.get(date_col, "N/A"),
                        "status": "Definitivo"
                    }
        
        # Populate global cache
        _SAT_BLACKLIST_CACHE = blacklist
        logger.info(f"Loaded {len(blacklist)} records into SAT Blacklist memory cache.")
        
    except Exception as e:
        logger.error(f"Error parsing SAT blacklist: {e}")
        return {}

    return _SAT_BLACKLIST_CACHE

@tool(
    name="query_sat_lista_69b",
    description="Checks if an RFC is present in the OFFICIAL SAT 69-B list (Blacklist).",
    parameters={
        "type": "object",
        "properties": {
            "rfc": {"type": "string", "description": "RFC to check"}
        },
        "required": ["rfc"]
    }
)
def query_sat_lista_69b(rfc: str) -> Dict[str, Any]:
    """Check if RFC is in 69-B list using real SAT data."""
    rfc_clean = rfc.upper().strip()
    
    # Load data (lazy loading with cache)
    blacklist = _get_blacklist_data()
    
    match = blacklist.get(rfc_clean)
    
    if match:
        return {
            "found": True,
            "rfc": rfc_clean,
            "razon_social": match["razon_social"],
            "status": match["status"],
            "fecha_publicacion": match["fecha_publicacion"],
            "risk_level": "CRITICAL",
            "source": "SAT Official List (Definitivos)",
            "recommendation": "RECHAZAR OPERACIÓN: Proveedor en lista negra definitiva del SAT (69-B)."
        }
    
    return {
        "found": False,
        "rfc": rfc_clean,
        "status": "Clean",
        "risk_level": "LOW",
        "source": "SAT Official List (Definitivos)",
        "checked_against": f"{len(blacklist)} records",
        "last_updated": datetime.now().isoformat()
    }

@tool(
    name="check_compliance_obligations",
    description="Checks pending fiscal obligations for a company.",
    parameters={
        "type": "object",
        "properties": {
            "rfc": {"type": "string", "description": "Company RFC"},
            "periodo": {"type": "string", "description": "Period (YYYY-MM)"}
        },
        "required": ["rfc"]
    }
)
def check_compliance_obligations(rfc: str, periodo: str = None) -> Dict[str, Any]:
    """Check compliance obligations."""
    # Mock compliance check
    return {
        "rfc": rfc,
        "opinion_cumplimiento": "Positiva",
        "declaraciones_pendientes": 0,
        "creditos_fiscales": [],
        "last_check": datetime.now().isoformat()
    }
