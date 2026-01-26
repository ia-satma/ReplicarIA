"""
Embedding Service for RAG Vector Search
Uses OpenAI embeddings (text-embedding-3-small) for Spanish legal/fiscal documents
"""

import os
import logging
from typing import List, Optional
import asyncio

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings using OpenAI."""
    
    def __init__(self):
        self.model = "text-embedding-3-small"
        self.dimensions = 1536
        self._client = None
    
    def _get_client(self):
        """Lazy-load OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI
                
                api_key = os.environ.get('AI_INTEGRATIONS_OPENAI_API_KEY')
                base_url = os.environ.get('AI_INTEGRATIONS_OPENAI_BASE_URL')
                
                if api_key and base_url:
                    self._client = OpenAI(api_key=api_key, base_url=base_url)
                elif os.environ.get('OPENAI_API_KEY'):
                    self._client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
                else:
                    logger.warning("OpenAI not configured for embeddings")
                    return None
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                return None
        return self._client
    
    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for a single text."""
        client = self._get_client()
        if not client:
            return None
        
        try:
            text = text.replace("\n", " ").strip()
            if len(text) < 10:
                return None
            
            if len(text) > 8000:
                text = text[:8000]
            
            response = await asyncio.to_thread(
                client.embeddings.create,
                model=self.model,
                input=text
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return None
    
    async def generate_batch_embeddings(
        self, 
        texts: List[str], 
        batch_size: int = 50
    ) -> List[Optional[List[float]]]:
        """Generate embeddings for multiple texts in batches."""
        client = self._get_client()
        if not client:
            return [None] * len(texts)
        
        all_embeddings = []
        
        processed_texts = []
        for text in texts:
            text = text.replace("\n", " ").strip()
            if len(text) > 8000:
                text = text[:8000]
            processed_texts.append(text)
        
        for i in range(0, len(processed_texts), batch_size):
            batch = processed_texts[i:i + batch_size]
            
            try:
                response = await asyncio.to_thread(
                    client.embeddings.create,
                    model=self.model,
                    input=batch
                )
                
                batch_embeddings = [e.embedding for e in response.data]
                all_embeddings.extend(batch_embeddings)
                
            except Exception as e:
                logger.error(f"Batch embedding failed at index {i}: {e}")
                all_embeddings.extend([None] * len(batch))
        
        return all_embeddings


embedding_service = EmbeddingService()
