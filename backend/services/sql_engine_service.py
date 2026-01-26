import os
import re
import duckdb
import pandas as pd
import logging

logger = logging.getLogger(__name__)

DB_PATH = os.environ.get('DUCKDB_PATH', '/tmp/sql/satma_finanzas.duckdb')
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

con = duckdb.connect(DB_PATH, read_only=False)

def _is_valid_identifier(name: str) -> bool:
    """Validate that a name is safe to use as a SQL identifier."""
    return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name))

def refresh_catalog(csv_dir='./sql_sources'):
    os.makedirs(csv_dir, exist_ok=True)
    tables_loaded = []
    for f in os.listdir(csv_dir):
        if f.lower().endswith('.csv'):
            t = os.path.splitext(f)[0]
            if not _is_valid_identifier(t):
                logger.warning(f"⚠️  Skipping {f}: invalid table name (use only alphanumeric and underscore)")
                continue
            p = os.path.join(csv_dir, f)
            try:
                con.execute(f"CREATE OR REPLACE VIEW {t} AS SELECT * FROM read_csv_auto('{p}')")
                tables_loaded.append(t)
                logger.info(f"✅ SQL view created: {t}")
            except Exception as e:
                logger.error(f"Error loading {f}: {str(e)}")
    return {"success": True, "tables_loaded": tables_loaded}

def query(sql: str) -> pd.DataFrame:
    if not sql.strip().lower().startswith('select'):
        return pd.DataFrame()
    try:
        return con.execute(sql).df()
    except Exception as e:
        logger.error(f"SQL error: {str(e)}")
        return pd.DataFrame()

def list_tables() -> list:
    try:
        tables = con.execute("SHOW TABLES").df()
        return tables['name'].tolist() if 'name' in tables.columns else []
    except:
        return []