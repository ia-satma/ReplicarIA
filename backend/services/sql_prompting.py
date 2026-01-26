import re

def llm_generate_sql(user_query: str) -> str:
    q = (user_query or '').lower()
    if 'kpi' in q or 'tendencia' in q:
        return "SELECT mes, kpi, valor FROM kpis_2025 ORDER BY mes;"
    if 'ventas' in q or 'roi' in q:
        return "SELECT mes, producto, unidades, importe FROM ventas_2025 ORDER BY mes, producto;"
    return "SELECT mes, kpi, valor FROM kpis_2025 ORDER BY mes;"