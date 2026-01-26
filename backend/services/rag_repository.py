import os
import hashlib
import pickle
from typing import Dict, Any, List, Optional
import chromadb
from chromadb.config import Settings
import logging

try:
    from routes.metrics import track_embedding_cache
except ImportError:
    def track_embedding_cache(hit: bool):
        pass

logger = logging.getLogger(__name__)

EMB_PROVIDER = os.environ.get('EMBEDDINGS_PROVIDER', 'openai').lower()
EMB_MODEL = os.environ.get('EMBEDDINGS_MODEL', 'text-embedding-3-small')
PERSIST_DIR = os.environ.get('CHROMA_PERSIST_DIR', '/tmp/vector_store/satma_prod')

_ST_model = None
_OAI = None


class EmbeddingCache:
    """Caché persistente de embeddings para evitar regeneración"""
    
    def __init__(self, cache_file: str = "/tmp/embedding_cache.pkl"):
        self.cache_file = cache_file
        self.cache = self._load_cache()
        logger.info(f"Embedding cache initialized with {len(self.cache)} entries")
    
    def _load_cache(self) -> Dict[str, List[float]]:
        """Carga caché desde disco"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'rb') as f:
                    return pickle.load(f)
        except Exception as e:
            logger.warning(f"Could not load embedding cache: {e}")
        return {}
    
    def _save_cache(self):
        """Guarda caché a disco"""
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self.cache, f)
        except Exception as e:
            logger.error(f"Could not save embedding cache: {e}")
    
    def get_hash(self, text: str) -> str:
        """Genera hash único para el texto"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def get(self, text: str) -> Optional[List[float]]:
        """Recupera embedding del caché"""
        text_hash = self.get_hash(text)
        return self.cache.get(text_hash)
    
    def set(self, text: str, embedding: List[float]):
        """Guarda embedding en caché"""
        text_hash = self.get_hash(text)
        self.cache[text_hash] = embedding
        
        if len(self.cache) % 10 == 0:
            self._save_cache()


_embedding_cache = EmbeddingCache()


def _embed_batch(texts: List[str]) -> List[List[float]]:
    """Genera embeddings con caché para evitar regeneración"""
    global _ST_model, _OAI, _embedding_cache
    
    cached_results = []
    texts_to_embed = []
    cache_hits = 0
    
    for text in texts:
        cached_emb = _embedding_cache.get(text)
        if cached_emb is not None:
            cached_results.append(cached_emb)
            cache_hits += 1
        else:
            cached_results.append(None)
            texts_to_embed.append(text)
    
    if cache_hits > 0:
        logger.info(f"📦 Embedding Cache: {cache_hits}/{len(texts)} hits ({cache_hits*100//len(texts)}% saved)")
    
    for text in texts:
        is_hit = _embedding_cache.get(text) is not None
        track_embedding_cache(is_hit)
    
    if not texts_to_embed:
        return cached_results
    
    if EMB_PROVIDER == 'sentence_transformers':
        if _ST_model is None:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading sentence-transformers model: {EMB_MODEL}")
            _ST_model = SentenceTransformer(EMB_MODEL)
        new_embeddings = _ST_model.encode(texts_to_embed, normalize_embeddings=True).tolist()
    else:
        if _OAI is None:
            from langchain_openai import OpenAIEmbeddings
            _OAI = OpenAIEmbeddings(model=EMB_MODEL)
        new_embeddings = _OAI.embed_documents(texts_to_embed)
    
    for text, emb in zip(texts_to_embed, new_embeddings):
        _embedding_cache.set(text, emb)
    
    result = []
    new_idx = 0
    for cached_emb in cached_results:
        if cached_emb is not None:
            result.append(cached_emb)
        else:
            result.append(new_embeddings[new_idx])
            new_idx += 1
    
    return result


class RagRepository:
    def __init__(self, persist_dir: Optional[str] = None, collection_prefix: str = 'satma_prod_'):
        self.persist_dir = persist_dir or PERSIST_DIR
        os.makedirs(self.persist_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=Settings(anonymized_telemetry=False)
        )
        self.prefix = collection_prefix
        self._cache = {}
        
        logger.info(f"✅ RagRepository initialized at {self.persist_dir} (provider: {EMB_PROVIDER})")

    def _colname(self, agent_id: str) -> str:
        short = (agent_id or 'default').split('_')[0]
        return f"{self.prefix}{short}"

    def _get_collection(self, agent_id: str):
        name = self._colname(agent_id)
        if name in self._cache:
            return self._cache[name]
        try:
            col = self.client.get_collection(name)
        except Exception as e:
            logger.info(f"Collection {name} not found, creating new: {str(e)[:50]}")
            col = self.client.create_collection(name)
        self._cache[name] = col
        return col

    def _make_id(self, metadata: Dict[str, Any], text: str) -> str:
        base = f"{metadata.get('doc_id','')}-{metadata.get('chunk_id','0')}".encode('utf-8','ignore')
        h = hashlib.md5(base + text.encode('utf-8','ignore')).hexdigest()
        return f"{metadata.get('doc_id','unknown')}-{metadata.get('chunk_id','0')}-{h[:8]}"

    def upsert_document(self, agent_id: str, text: str, metadata: Dict[str, Any]) -> str:
        text = (text or '').strip()
        if not text:
            return ''
        
        col = self._get_collection(agent_id)
        _id = self._make_id(metadata, text)
        
        try:
            vec = _embed_batch([text])[0]
            
            try:
                col.delete(ids=[_id])
            except Exception as e:
                logger.debug(f"No existing doc to delete (id={_id}): {str(e)[:30]}")
            
            col.add(
                documents=[text],
                metadatas=[metadata],
                ids=[_id],
                embeddings=[vec]
            )
            
            logger.info(f"✅ Upserted chunk {_id} to {col.name}")
            return _id
            
        except Exception as e:
            logger.error(f"Error upserting: {str(e)}")
            return ''

    def query(self, agent_id: str, query_text: str, top_k: int = 10) -> Dict[str, Any]:
        col = self._get_collection(agent_id)
        
        try:
            embs = _embed_batch([query_text])
            res = col.query(
                query_embeddings=embs,
                n_results=top_k,
                include=['metadatas','documents','distances']
            )
            return res
        except Exception as e:
            logger.error(f"Error querying: {str(e)}")
            return {"documents": [], "metadatas": [], "distances": []}

    def count(self, agent_id: str) -> int:
        col = self._get_collection(agent_id)
        try:
            return col.count()
        except Exception as e:
            logger.error(f"[RAG COUNT ERROR] Failed to count documents for {agent_id}: {str(e)}")
            return 0
