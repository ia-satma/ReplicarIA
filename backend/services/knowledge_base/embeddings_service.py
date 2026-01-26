"""
Embeddings Service for Bibliotecar.IA
Generates 1536-dimensional embeddings using OpenAI or Voyage AI.
Note: Anthropic AI Integrations does not support embeddings API, so we use OpenAI/Voyage.
"""
import os
import logging
import httpx
import asyncio
from typing import List, Optional

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
VOYAGE_API_KEY = os.environ.get('VOYAGE_API_KEY')


class EmbeddingsService:
    """Service for generating text embeddings with 1536 dimensions."""
    
    def __init__(self):
        self.openai_key = OPENAI_API_KEY
        self.voyage_key = VOYAGE_API_KEY
        self._dimension = 1536
    
    @property
    def dimension(self) -> int:
        """Return the embedding dimension (1536)."""
        return self._dimension
    
    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate a single 1536-dimensional embedding.
        
        Priority:
        1. Voyage AI (voyage-law-2 for legal documents)
        2. OpenAI (text-embedding-3-small)
        3. Simulated embedding (for testing)
        """
        if not text or not text.strip():
            return None
        
        text = text[:8000]
        
        if self.voyage_key:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        'https://api.voyageai.com/v1/embeddings',
                        headers={
                            'Content-Type': 'application/json',
                            'Authorization': f'Bearer {self.voyage_key}'
                        },
                        json={
                            'model': 'voyage-law-2',
                            'input': text
                        }
                    )
                    if response.status_code == 200:
                        data = response.json()
                        return self._ensure_dimension(data['data'][0]['embedding'])
            except Exception as e:
                logger.warning(f"Voyage AI error, trying fallback: {e}")
        
        if self.openai_key:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        'https://api.openai.com/v1/embeddings',
                        headers={
                            'Content-Type': 'application/json',
                            'Authorization': f'Bearer {self.openai_key}'
                        },
                        json={
                            'model': 'text-embedding-3-small',
                            'input': text
                        }
                    )
                    if response.status_code == 200:
                        data = response.json()
                        return self._ensure_dimension(data['data'][0]['embedding'])
                    else:
                        logger.error(f"OpenAI API error: {response.status_code}")
            except Exception as e:
                logger.error(f"OpenAI embeddings error: {e}")
                return None
        
        logger.warning("No embedding API configured. Generating simulated embedding.")
        return self._generate_simulated_embedding(text)
    
    async def generate_embeddings_batch(
        self,
        texts: List[str],
        batch_size: int = 20
    ) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts in batches.
        Returns list of 1536-dimensional vectors.
        """
        if not texts:
            return []
        
        texts = [t[:8000] if t else "" for t in texts]
        
        if self.voyage_key:
            result = await self._voyage_batch(texts, batch_size)
            if result and len(result) == len(texts):
                return result
        
        if self.openai_key:
            result = await self._openai_batch(texts, batch_size)
            if result:
                return result
        
        logger.warning("No embedding API for batch, generating simulated embeddings")
        return [self._generate_simulated_embedding(t) for t in texts]
    
    async def _voyage_batch(
        self,
        texts: List[str],
        batch_size: int
    ) -> Optional[List[List[float]]]:
        """Generate embeddings in batches using Voyage AI."""
        try:
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                batch = [t if t.strip() else " " for t in batch]
                
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        'https://api.voyageai.com/v1/embeddings',
                        headers={
                            'Content-Type': 'application/json',
                            'Authorization': f'Bearer {self.voyage_key}'
                        },
                        json={
                            'model': 'voyage-law-2',
                            'input': batch
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        embeddings = [self._ensure_dimension(d['embedding']) for d in data['data']]
                        all_embeddings.extend(embeddings)
                    else:
                        logger.warning(f"Voyage batch error: {response.status_code}")
                        return None
                
                if i + batch_size < len(texts):
                    await asyncio.sleep(0.3)
            
            return all_embeddings
            
        except Exception as e:
            logger.warning(f"Voyage AI batch error: {e}")
            return None
    
    async def _openai_batch(
        self,
        texts: List[str],
        batch_size: int
    ) -> Optional[List[List[float]]]:
        """Generate embeddings in batches using OpenAI."""
        try:
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                batch = [t if t.strip() else " " for t in batch]
                
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        'https://api.openai.com/v1/embeddings',
                        headers={
                            'Content-Type': 'application/json',
                            'Authorization': f'Bearer {self.openai_key}'
                        },
                        json={
                            'model': 'text-embedding-3-small',
                            'input': batch
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        embeddings = [self._ensure_dimension(d['embedding']) for d in data['data']]
                        all_embeddings.extend(embeddings)
                    else:
                        logger.warning(f"OpenAI batch error: {response.status_code}")
                        for text in batch:
                            emb = await self.generate_embedding(text)
                            all_embeddings.append(emb)
                
                if i + batch_size < len(texts):
                    await asyncio.sleep(0.2)
            
            return all_embeddings
            
        except Exception as e:
            logger.error(f"OpenAI batch error: {e}")
            return None
    
    def _ensure_dimension(self, embedding: List[float]) -> List[float]:
        """Ensure embedding has exactly 1536 dimensions."""
        if len(embedding) == self._dimension:
            return embedding
        elif len(embedding) > self._dimension:
            return embedding[:self._dimension]
        else:
            return embedding + [0.0] * (self._dimension - len(embedding))
    
    def _generate_simulated_embedding(self, text: str) -> List[float]:
        """Generate simulated embedding for testing without API."""
        import hashlib
        
        hash_val = hashlib.sha256(text.encode()).hexdigest()
        embedding = []
        
        for i in range(0, min(len(hash_val), 64), 2):
            val = int(hash_val[i:i+2], 16) / 255.0 - 0.5
            embedding.append(val)
        
        while len(embedding) < self._dimension:
            for j, char in enumerate(text[:200]):
                if len(embedding) >= self._dimension:
                    break
                val = (ord(char) * (j + 1)) % 256 / 255.0 - 0.5
                embedding.append(val * 0.1)
            if len(embedding) < self._dimension:
                embedding.extend([0.0] * (self._dimension - len(embedding)))
        
        return embedding[:self._dimension]
    
    async def compute_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """Compute cosine similarity between two embeddings."""
        if not embedding1 or not embedding2:
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
        norm1 = sum(a * a for a in embedding1) ** 0.5
        norm2 = sum(b * b for b in embedding2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)


embeddings_service = EmbeddingsService()
