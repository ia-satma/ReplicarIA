from typing import Dict, List, Tuple
import re

# --- Imports con fallbacks robustos ---
try:
    from services.query_router import route as classify_intent
except Exception:
    def classify_intent(text: str) -> str:
        t = (text or '').lower()
        if re.search(r"\bselect\b|\bfrom\b|\bjoin\b|\bkpi\b|\bventa", t):
            return "sql"
        if re.search(r"(art[íi]c|art\.|articulo|artículo|lisr|cff|regla\s*\d)", t):
            return "kg"
        return "rag"

try:
    from services.sql_prompting import llm_generate_sql
except Exception:
    def llm_generate_sql(q: str) -> str:
        qt = (q or '').lower()
        if 'kpi' in qt:
            return 'SELECT mes, kpi, valor FROM kpis_2025 ORDER BY mes;'
        if 'venta' in qt or 'roi' in qt:
            return 'SELECT mes, producto, unidades, importe FROM ventas_2025 ORDER BY mes, producto;'
        return 'SELECT mes, kpi, valor FROM kpis_2025 ORDER BY mes;'

try:
    from services.sql_engine_service import query as sql_query
except Exception:
    def sql_query(sql_text: str):
        import pandas as pd
        return pd.DataFrame([{'mes':'2025-11','kpi':'Test','valor':100000}])

try:
    from services.kg_enhanced import build_chain_context
except Exception:
    def build_chain_context(agent_id: str, user_text: str) -> Tuple[str, Dict]:
        return ('[KG no disponible]', {'metadatas':[[]],'distances':[[1.0]]})

try:
    from services.rag_repository import RagRepository
    rag_repo = RagRepository()
    def query_hybrid(agent_id: str, user_query: str, top_k: int = 10):
        return rag_repo.query(agent_id, user_query, top_k)
except Exception:
    def query_hybrid(agent_id: str, user_query: str, top_k: int = 10):
        return {'metadatas':[[]],'distances':[[1.0]]}

try:
    from services.answer_decorator import add_citations_if_missing
except Exception:
    def add_citations_if_missing(text, hits):
        return text

def _sql_metas(agent_id: str, sql_text: str) -> List[Dict]:
    tables = []
    for m in re.finditer(r'(?:from|join)\s+([a-zA-Z_][a-zA-Z0-9_\.]*)', sql_text or '', re.I):
        t = m.group(1)
        if t not in tables:
            tables.append(t)
    if not tables:
        tables = ['kpis_2025']
    return [{'doc_title':f'SQL {t}','created_at':'','webViewLink':f'sql://{t}','owner':agent_id,'status':'OK'} for t in tables]

async def analyze(agent_id: str, user_text: str) -> Dict:
    route = classify_intent(user_text)
    
    if route == 'sql':
        sql_text = llm_generate_sql(user_text)
        df = sql_query(sql_text)
        try:
            llm_context = 'RESULTADOS SQL:\n' + df.head(20).to_csv(index=False)
        except:
            llm_context = 'RESULTADOS SQL: (sin datos)'
        metas = _sql_metas(agent_id, sql_text)
        rag_hits = {'metadatas':[metas],'distances':[[0.0]*len(metas)]}
        draft = f"Consulta:\n```sql\n{sql_text}\n```\n\n{llm_context}"
        answer = add_citations_if_missing(draft, rag_hits)
        return {'route':'sql','answer':answer,'context':llm_context,'rag_hits':rag_hits}
    
    if route == 'kg':
        llm_context, rag_hits = build_chain_context(agent_id, user_text)
        answer = add_citations_if_missing(llm_context, rag_hits)
        return {'route':'kg','answer':answer,'context':llm_context,'rag_hits':rag_hits}
    
    # RAG
    hits = query_hybrid(agent_id=agent_id, user_query=user_text, top_k=10)
    docs = hits.get('documents',[[]])[0]
    metas = hits.get('metadatas',[[]])[0]
    
    lines = []
    for d, m in zip(docs[:10], metas[:10]):
        lines.append(f"Fuente: {m.get('doc_title','')}")
        lines.append(d[:200])
        lines.append('')
    
    llm_context = '\n'.join(lines)
    draft = f"{llm_context}\n---\nPregunta: {user_text}"
    answer = add_citations_if_missing(draft, hits)
    
    return {'route':'rag','answer':answer,'context':llm_context,'rag_hits':hits}
