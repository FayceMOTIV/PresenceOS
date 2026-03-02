"""
PresenceOS - BrandBrain Service
Textual memory system: remember, recall, learn, reflect.
Uses JSONB embeddings with cosine similarity in Python.
"""
import json
import math
import uuid
from datetime import datetime, timezone

import structlog
from openai import AsyncOpenAI
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.brain import BrainMemory

logger = structlog.get_logger()


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


async def _get_embedding(text: str) -> list[float]:
    """Get embedding from OpenAI."""
    if not settings.openai_api_key:
        return []
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    response = await client.embeddings.create(
        model=settings.openai_embedding_model,
        input=text[:8000],
    )
    return response.data[0].embedding


class BrandBrain:
    def __init__(self, brand_id: uuid.UUID, db: AsyncSession):
        self.brand_id = brand_id
        self.db = db

    async def remember(
        self,
        content: str,
        memory_type: str = "episodic",
        source: str | None = None,
        confidence: float = 0.5,
        metadata: dict | None = None,
    ) -> BrainMemory:
        """Store a new memory with embedding."""
        embedding = await _get_embedding(content)

        memory = BrainMemory(
            brand_id=self.brand_id,
            memory_type=memory_type,
            content=content,
            source=source,
            confidence=confidence,
            embedding=embedding,
            metadata_json=metadata or {},
        )
        self.db.add(memory)
        await self.db.commit()
        await self.db.refresh(memory)
        logger.info("Memory stored", brand_id=str(self.brand_id), type=memory_type)
        return memory

    async def recall(
        self,
        query: str,
        memory_type: str | None = None,
        top_k: int = 5,
        min_similarity: float = 0.3,
    ) -> list[dict]:
        """Recall relevant memories using cosine similarity on JSONB embeddings."""
        query_embedding = await _get_embedding(query)
        if not query_embedding:
            return []

        # Fetch all memories for this brand (filtered by type if specified)
        stmt = select(BrainMemory).where(BrainMemory.brand_id == self.brand_id)
        if memory_type:
            stmt = stmt.where(BrainMemory.memory_type == memory_type)
        result = await self.db.execute(stmt)
        memories = result.scalars().all()

        # Compute similarity in Python
        scored = []
        for m in memories:
            if m.embedding:
                sim = _cosine_similarity(query_embedding, m.embedding)
                if sim >= min_similarity:
                    scored.append((m, sim))

        scored.sort(key=lambda x: x[1], reverse=True)
        top = scored[:top_k]

        # Update access counts
        for m, _ in top:
            await self.db.execute(
                update(BrainMemory)
                .where(BrainMemory.id == m.id)
                .values(
                    access_count=BrainMemory.access_count + 1,
                    last_accessed_at=datetime.now(timezone.utc),
                )
            )
        await self.db.commit()

        return [
            {
                "id": str(m.id),
                "content": m.content,
                "memory_type": m.memory_type,
                "confidence": m.confidence,
                "similarity": round(sim, 3),
                "source": m.source,
            }
            for m, sim in top
        ]

    async def get_context_for_generation(self, topic: str, platform: str = "instagram") -> dict:
        """Build rich context for content generation."""
        memories = await self.recall(topic, top_k=8)
        rules = await self.recall(f"content rules for {platform}", memory_type="procedural", top_k=3)

        return {
            "relevant_memories": memories,
            "content_rules": rules,
            "topic": topic,
            "platform": platform,
        }

    async def weekly_reflection(self) -> str:
        """Generate a weekly reflection, synthesizing patterns into new procedural memories."""
        if not settings.openai_api_key:
            return "No API key configured"

        # Get recent episodic memories
        stmt = (
            select(BrainMemory)
            .where(
                BrainMemory.brand_id == self.brand_id,
                BrainMemory.memory_type == "episodic",
            )
            .order_by(BrainMemory.created_at.desc())
            .limit(20)
        )
        result = await self.db.execute(stmt)
        recent = result.scalars().all()

        if not recent:
            return "No recent memories to reflect on"

        memories_text = "\n".join([f"- {m.content} (confidence: {m.confidence})" for m in recent])

        client = AsyncOpenAI(api_key=settings.openai_api_key)
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Tu es un analyste de contenu social media pour restaurants. Synthétise les souvenirs récents en 3-5 règles de contenu concrètes.",
                },
                {
                    "role": "user",
                    "content": f"Souvenirs récents:\n{memories_text}\n\nGénère des règles de contenu en JSON array: [{{\"rule\": \"...\", \"confidence\": 0.0-1.0}}]",
                },
            ],
            max_tokens=500,
            temperature=0.5,
            response_format={"type": "json_object"},
        )

        try:
            data = json.loads(response.choices[0].message.content)
            rules = data.get("rules", data) if isinstance(data, dict) else data
            if isinstance(rules, list):
                for rule in rules:
                    rule_text = rule.get("rule", str(rule)) if isinstance(rule, dict) else str(rule)
                    confidence = rule.get("confidence", 0.7) if isinstance(rule, dict) else 0.7
                    await self.remember(
                        content=rule_text,
                        memory_type="procedural",
                        source="weekly_reflection",
                        confidence=confidence,
                    )
            logger.info("Weekly reflection completed", brand_id=str(self.brand_id), rules_count=len(rules) if isinstance(rules, list) else 0)
            return f"Reflection complete: {len(rules) if isinstance(rules, list) else 0} new rules"
        except Exception as e:
            logger.error("Reflection parsing failed", error=str(e))
            return f"Reflection failed: {str(e)}"

    async def post_published_learning(self, caption: str, platform: str, engagement: dict) -> None:
        """Learn from a published post's engagement."""
        engagement_text = ", ".join(f"{k}: {v}" for k, v in engagement.items())
        content = f"Post published on {platform}: '{caption[:100]}...' — Engagement: {engagement_text}"
        await self.remember(
            content=content,
            memory_type="episodic",
            source="post_published",
            confidence=0.6,
            metadata={"platform": platform, "engagement": engagement},
        )

    async def seed_initial_memories(self, brand_info: dict) -> int:
        """Seed initial memories from brand onboarding data."""
        count = 0
        if brand_info.get("description"):
            await self.remember(brand_info["description"], "semantic", "onboarding", 0.9)
            count += 1
        if brand_info.get("niche"):
            await self.remember(f"Restaurant niche: {brand_info['niche']}", "semantic", "onboarding", 0.95)
            count += 1
        if brand_info.get("target_persona"):
            persona = json.dumps(brand_info["target_persona"], ensure_ascii=False)
            await self.remember(f"Target audience: {persona}", "semantic", "onboarding", 0.9)
            count += 1
        if brand_info.get("constraints"):
            constraints = json.dumps(brand_info["constraints"], ensure_ascii=False)
            await self.remember(f"Business constraints: {constraints}", "semantic", "onboarding", 0.95)
            count += 1
        logger.info("Initial memories seeded", brand_id=str(self.brand_id), count=count)
        return count

    async def get_brain_status(self) -> dict:
        """Get brain maturity status."""
        result = await self.db.execute(
            select(
                BrainMemory.memory_type,
                func.count(BrainMemory.id),
            )
            .where(BrainMemory.brand_id == self.brand_id)
            .group_by(BrainMemory.memory_type)
        )
        counts = {row[0]: row[1] for row in result.all()}
        total = sum(counts.values())

        # Calculate maturity (0-100)
        maturity = min(100, total * 2)  # 50 memories = 100%

        return {
            "total_memories": total,
            "memory_counts": counts,
            "maturity": maturity,
            "maturity_label": (
                "Nouveau-né" if maturity < 20
                else "Apprenti" if maturity < 40
                else "Compétent" if maturity < 60
                else "Expert" if maturity < 80
                else "Maître"
            ),
        }
