import os
import networkx as nx
import logging

logger = logging.getLogger(__name__)

KG_PATH = os.environ.get('KG_GRAPH_PATH', './kg_graph/graph.gpickle')
os.makedirs(os.path.dirname(KG_PATH), exist_ok=True)

G = nx.DiGraph()

def upsert_triple(h, rel, t, meta=None):
    G.add_node(h, **(meta or {}))
    G.add_node(t, **(meta or {}))
    G.add_edge(h, t, rel=rel)
    logger.info(f"Triple: ({h}) --{rel}--> ({t})")
    return True

def save():
    """Guarda grafo en disco"""
    import pickle
    with open(KG_PATH, 'wb') as f:
        pickle.dump(G, f)
    logger.info(f"✅ KG guardado: {len(G.nodes())} nodos, {len(G.edges())} aristas")
    return True

def load():
    """Carga grafo desde disco"""
    global G
    if os.path.exists(KG_PATH):
        import pickle
        with open(KG_PATH, 'rb') as f:
            G = pickle.load(f)
        logger.info(f"✅ KG cargado: {len(G.nodes())} nodos")
        return True
    return False

def kg_query(question: str):
    nodes = list(G.nodes())
    ans = {"paths": [], "explanation": "", "metas": [[{"doc_title": "KG", "created_at": "", "webViewLink": "(KG)"}]]}
    if len(nodes) > 1:
        try:
            s = nodes[0]
            t = nodes[-1]
            if nx.has_path(G, s, t):
                path = nx.shortest_path(G, s, t)
                ans["paths"].append(path)
        except Exception as e:
            logger.warning(f"Error finding KG path: {e}")
            pass
    ans["explanation"] = f"KG: {len(G.nodes())} entidades, {len(G.edges())} relaciones"
    return ans

def get_stats():
    return {"nodes": len(G.nodes()), "edges": len(G.edges()), "is_empty": len(G.nodes()) == 0}