"""
PresenceOS - Embedding Service for RAG
"""
import structlog
from typing import Any

import openai
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings

logger = structlog.get_logger()


class EmbeddingService:
    """Service for generating text embeddings using OpenAI."""

    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_embedding_model
        self.dimensions = 1536  # text-embedding-3-small

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        if not text.strip():
            return [0.0] * self.dimensions

        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=text[:8000],  # Truncate to avoid token limits
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error("Embedding generation failed", error=str(e))
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def generate_embeddings_batch(
        self, texts: list[str], batch_size: int = 100
    ) -> list[list[float]]:
        """Generate embeddings for multiple texts in batches."""
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            # Clean and truncate
            batch = [t[:8000] if t.strip() else " " for t in batch]

            try:
                response = await self.client.embeddings.create(
                    model=self.model,
                    input=batch,
                )
                embeddings = [d.embedding for d in response.data]
                all_embeddings.extend(embeddings)
            except Exception as e:
                logger.error(
                    "Batch embedding generation failed",
                    batch_start=i,
                    error=str(e),
                )
                # Return zero embeddings for failed batch
                all_embeddings.extend([[0.0] * self.dimensions] * len(batch))

        return all_embeddings

    def cosine_similarity(
        self, embedding1: list[float], embedding2: list[float]
    ) -> float:
        """Calculate cosine similarity between two embeddings."""
        import math

        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
        norm1 = math.sqrt(sum(a * a for a in embedding1))
        norm2 = math.sqrt(sum(b * b for b in embedding2))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)
