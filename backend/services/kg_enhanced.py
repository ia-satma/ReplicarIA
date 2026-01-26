import os
import json
import re
import logging
from typing import Tuple, Dict
import networkx as nx
from services.rag_repository import RagRepository

logger = logging.getLogger(__name__)

KG_PATH = os.environ.get('KG_GRAPH_PATH', './kg_graph/graph.gpickle')

class KGService:
    def __init__(self):
        self.G = nx.DiGraph()
        self.repo = RagRepository()
        os.makedirs(os.path.dirname(KG_PATH), exist_ok=True)
        self.load()
    
    def load(self):
        if os.path.exists(KG_PATH):
            import pickle
            with open(KG_PATH, 'rb') as f:
                self.G = pickle.load(f)
            logger.info(f"✅ KG cargado: {len(self.G.nodes())} nodos")
    
    def save(self):
        import pickle
        with open(KG_PATH, 'wb') as f:
            pickle.dump(self.G, f)
        logger.info(f"✅ KG guardado: {len(self.G.nodes())} nodos")
    
    def populate_from_agent(self, agent_id: str, limit: int = 2000) -> Dict:
        """Extrae triples desde chunks RAG"""
        
        # Obtener collection
        col = self.repo._get_collection(agent_id)
        all_data = col.get(include=['documents', 'metadatas'])
        
        docs = all_data.get('documents', [])
        metas = all_data.get('metadatas', [])
        
        self.G = nx.DiGraph()
        
        art_rx = re.compile(r"(?:art[íi]culo\s*(\d+[A-Za-z]?))", re.IGNORECASE)
        norm_rx = re.compile(r"\b(LISR|CFF|Ley\s+del\s+ISR)\b", re.IGNORECASE)
        
        for doc, meta in zip(docs, metas):
            doc_id = meta.get('doc_id', '')
            title = meta.get('doc_title', doc_id)
            link = meta.get('webViewLink', '')
            created = meta.get('created_at', '')
            
            if doc_id:
                self.G.add_node(doc_id, type='document', title=title, link=link, created=created)
            
            arts = set(art_rx.findall(doc))
            norms = set(n.upper() for n in norm_rx.findall(doc))
            
            if arts:
                base_norm = next(iter(norms), 'NORMA_DESCONOCIDA')
                for a in sorted(arts):
                    norm_node = f"{base_norm}_ART_{a}"
                    if not self.G.has_node(norm_node):
                        self.G.add_node(norm_node, type='norma', label=norm_node)
                    if doc_id:
                        self.G.add_edge(doc_id, norm_node, rel='cita')
        
        self.save()
        
        return {
            'nodes': self.G.number_of_nodes(),
            'edges': self.G.number_of_edges()
        }
    
    def explain_chain(self, user_text: str, agent_id: str, max_steps: int = 3) -> Tuple[str, Dict]:
        """Explica cadena de citas de un artículo"""
        
        m = re.search(r"(art[íi]culo\s*(\d+[A-Za-z]?))", user_text, re.IGNORECASE)
        if not m:
            return (
                "[REQUIERE VALIDACIÓN HUMANA]\nNo identifiqué el artículo en la consulta.",
                {'metadatas': [[]], 'distances': [[1.0]]}
            )
        
        art = m.group(2)
        target = f"LISR_ART_{art}"
        
        if not self.G.has_node(target):
            return (
                f"[REQUIERE VALIDACIÓN HUMANA]\nNo encontré {target} en el grafo.",
                {'metadatas': [[]], 'distances': [[1.0]]}
            )
        
        preds = list(self.G.predecessors(target))
        
        if not preds:
            return (
                f"[REQUIERE VALIDACIÓN HUMANA]\nNo hay documentos que citen {target}.",
                {'metadatas': [[]], 'distances': [[1.0]]}
            )
        
        lines = [f"Cadena de citas hacia {target}:"]
        metas = []
        
        for doc_id in preds[:max_steps]:
            d = self.G.nodes[doc_id]
            lines.append(f"• {d.get('title')} → {target}")
            metas.append({
                'doc_title': d.get('title'),
                'created_at': d.get('created'),
                'webViewLink': d.get('link'),
                'owner': agent_id,
                'status': 'OK'
            })
        
        return ('\n'.join(lines), {'metadatas': [metas], 'distances': [[0.0 for _ in metas]]})

KG = KGService()

def build_chain_context(agent_id: str, user_text: str):
    """Helper para agent_service"""
    return KG.explain_chain(user_text, agent_id)
