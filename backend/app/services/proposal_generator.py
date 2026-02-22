"""
PresenceOS - Proposal Generator Service (Content Library)

Generates AI content proposals using the Knowledge Base context.
Uses Claude Haiku for simple generation, Sonnet for complex cases.
"""
import json
from datetime import datetime, timezone
from typing import Any

import anthropic
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.ai_proposal import AIProposal, ProposalSource, ProposalStatus
from app.models.compiled_kb import CompiledKB
from app.models.dish import Dish
from app.models.media import MediaAsset
from app.services.prompt_builder import PromptBuilder

logger = structlog.get_logger()


class ProposalGenerator:
    """Generates AI proposals from various sources using the Knowledge Base."""

    HAIKU_MODEL = "claude-haiku-4-5-20251001"
    SONNET_MODEL = "claude-sonnet-4-6"

    def __init__(self, db: AsyncSession):
        self.db = db
        self.prompt_builder = PromptBuilder()
        self._client: anthropic.AsyncAnthropic | None = None

    def _get_client(self) -> anthropic.AsyncAnthropic:
        if self._client is None:
            if not settings.anthropic_api_key:
                raise RuntimeError(
                    "Anthropic API key is not configured. "
                    "Set ANTHROPIC_API_KEY in your environment."
                )
            self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        return self._client

    async def _get_kb_dict(self, brand_id: str) -> dict:
        """Load compiled KB as dict. Returns empty dict if not found."""
        stmt = select(CompiledKB).where(CompiledKB.brand_id == brand_id)
        result = await self.db.execute(stmt)
        kb = result.scalar_one_or_none()
        if not kb:
            return {}
        return {
            "identity": kb.identity or {},
            "menu": kb.menu or {},
            "media": kb.media or {},
            "today": kb.today or {},
            "posting_history": kb.posting_history or {},
            "performance": kb.performance or {},
            "kb_version": kb.kb_version,
        }

    # ── Generation Methods ────────────────────────────────────────────────

    async def generate_from_brief(
        self,
        brand_id: str,
        brief_response: str,
        proposal_id: str | None = None,
    ) -> AIProposal:
        """Generate a proposal from a daily brief response."""
        kb_dict = await self._get_kb_dict(brand_id)
        system_prompt = self.prompt_builder.build_system_prompt(kb_dict)
        user_prompt = self.prompt_builder.build_generation_prompt(
            kb_dict,
            source_type="brief",
            source_data={"response": brief_response},
        )

        result = await self._call_llm(system_prompt, user_prompt, complex=False)

        proposal = await self._upsert_proposal(
            proposal_id=proposal_id,
            brand_id=brand_id,
            source=ProposalSource.BRIEF.value,
            source_id=datetime.now(timezone.utc).date().isoformat(),
            result=result,
            kb_version=kb_dict.get("kb_version", 0),
        )

        logger.info("Proposal generated from brief", proposal_id=str(proposal.id))
        return proposal

    async def generate_from_asset(
        self,
        brand_id: str,
        asset_id: str,
        proposal_id: str | None = None,
    ) -> AIProposal:
        """Generate a proposal from a media asset."""
        # Load asset info
        stmt = select(MediaAsset).where(MediaAsset.id == asset_id)
        result = await self.db.execute(stmt)
        asset = result.scalar_one_or_none()
        if not asset:
            raise ValueError(f"Asset {asset_id} not found")

        # Check if linked to a dish
        dish_name = None
        if asset.linked_dish_id:
            dish_stmt = select(Dish).where(Dish.id == asset.linked_dish_id)
            dish_result = await self.db.execute(dish_stmt)
            dish = dish_result.scalar_one_or_none()
            if dish:
                dish_name = dish.name

        kb_dict = await self._get_kb_dict(brand_id)
        system_prompt = self.prompt_builder.build_system_prompt(kb_dict)
        user_prompt = self.prompt_builder.build_generation_prompt(
            kb_dict,
            source_type="asset",
            source_data={
                "description": asset.ai_description or "Photo du restaurant",
                "label": asset.asset_label,
                "dish_name": dish_name,
            },
        )

        result = await self._call_llm(system_prompt, user_prompt, complex=False)

        proposal = await self._upsert_proposal(
            proposal_id=proposal_id,
            brand_id=brand_id,
            source=ProposalSource.ASSET.value,
            source_id=str(asset_id),
            result=result,
            kb_version=kb_dict.get("kb_version", 0),
            image_url=asset.improved_url or asset.public_url,
        )

        logger.info("Proposal generated from asset", proposal_id=str(proposal.id))
        return proposal

    async def generate_from_request(
        self,
        brand_id: str,
        request_text: str,
        content_type: str = "post",
        platform: str = "instagram",
        proposal_id: str | None = None,
    ) -> AIProposal:
        """Generate a proposal from a free-text request."""
        kb_dict = await self._get_kb_dict(brand_id)
        system_prompt = self.prompt_builder.build_system_prompt(kb_dict)
        user_prompt = self.prompt_builder.build_generation_prompt(
            kb_dict,
            source_type="request",
            source_data={"text": request_text},
            content_type=content_type,
            platform=platform,
        )

        # Use Sonnet for free-text requests (more creative control needed)
        result = await self._call_llm(system_prompt, user_prompt, complex=True)

        proposal = await self._upsert_proposal(
            proposal_id=proposal_id,
            brand_id=brand_id,
            source=ProposalSource.REQUEST.value,
            source_id=None,
            result=result,
            kb_version=kb_dict.get("kb_version", 0),
            proposal_type=content_type,
            platform=platform,
        )

        logger.info("Proposal generated from request", proposal_id=str(proposal.id))
        return proposal

    async def regenerate_variant(self, proposal_id: str) -> AIProposal:
        """Generate a new variant from an existing proposal's source."""
        stmt = select(AIProposal).where(AIProposal.id == proposal_id)
        result = await self.db.execute(stmt)
        original = result.scalar_one_or_none()
        if not original:
            raise ValueError(f"Proposal {proposal_id} not found")

        brand_id = str(original.brand_id)

        if original.source == ProposalSource.BRIEF.value:
            return await self.generate_from_brief(brand_id, "Variante du brief précédent")
        elif original.source == ProposalSource.ASSET.value and original.source_id:
            return await self.generate_from_asset(brand_id, original.source_id)
        else:
            return await self.generate_from_request(
                brand_id,
                f"Génère une variante de ce post : {(original.caption or '')[:200]}",
                original.proposal_type,
                original.platform,
            )

    # ── LLM Interaction ───────────────────────────────────────────────────

    async def _call_llm(
        self, system_prompt: str, user_prompt: str, complex: bool = False
    ) -> dict[str, Any]:
        """Call Claude and parse JSON response."""
        model = self.SONNET_MODEL if complex else self.HAIKU_MODEL
        client = self._get_client()

        response = await client.messages.create(
            model=model,
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )

        raw = response.content[0].text

        # Parse JSON from response
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start == -1 or end == 0:
            raise ValueError("No JSON found in LLM response")

        return json.loads(raw[start:end])

    async def _upsert_proposal(
        self,
        proposal_id: str | None,
        brand_id: str,
        source: str,
        source_id: str | None,
        result: dict,
        kb_version: int,
        image_url: str | None = None,
        proposal_type: str = "post",
        platform: str = "instagram",
    ) -> AIProposal:
        """Create or update an AIProposal with generation results."""
        if proposal_id:
            stmt = select(AIProposal).where(AIProposal.id == proposal_id)
            db_result = await self.db.execute(stmt)
            proposal = db_result.scalar_one_or_none()
        else:
            proposal = None

        caption = result.get("caption", "")
        hashtags = result.get("hashtags", [])
        confidence = float(result.get("confidence", 0.0))

        if proposal:
            proposal.caption = caption
            proposal.hashtags = hashtags
            proposal.confidence_score = confidence
            proposal.kb_version = kb_version
            proposal.status = ProposalStatus.PENDING.value
            if image_url:
                proposal.image_url = image_url
        else:
            proposal = AIProposal(
                brand_id=brand_id,
                proposal_type=proposal_type,
                platform=platform,
                caption=caption,
                hashtags=hashtags,
                source=source,
                source_id=source_id,
                status=ProposalStatus.PENDING.value,
                kb_version=kb_version,
                confidence_score=confidence,
                image_url=image_url,
            )
            self.db.add(proposal)

        await self.db.commit()
        await self.db.refresh(proposal)
        return proposal
