"""
PresenceOS - Push Notification Service (Expo)
Sends push notifications to mobile app via Expo Push API.
"""
import structlog
import httpx

logger = structlog.get_logger()

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"

# Template dictionary for all notification types
PUSH_TEMPLATES = {
    "validation_ready": {
        "title": "📱 {count} post{s} à valider",
        "body": "{brand_name} — Vos posts IA sont prêts. Validez-les avant publication.",
        "data_screen": "ValidationInbox",
    },
    "post_published": {
        "title": "✅ Post publié !",
        "body": "Votre post a été publié sur {platform}.",
        "data_screen": "ProposalsList",
    },
    "trend_detected": {
        "title": "🔥 Tendance détectée",
        "body": "{brand_name} — \"{trend}\" est en tendance. Un post a été généré pour vous.",
        "data_screen": "ValidationInbox",
    },
    "weekly_plan_ready": {
        "title": "📅 Plan de la semaine prêt",
        "body": "{brand_name} — Votre planning hebdomadaire a été généré. {count} posts à valider.",
        "data_screen": "ValidationInbox",
    },
    "daily_brief": {
        "title": "☀️ Brief du jour",
        "body": "{brand_name} — Votre brief quotidien est prêt.",
        "data_screen": "Brief",
    },
}


async def send_templated_notification(
    expo_push_token: str,
    template_key: str,
    **kwargs,
) -> dict:
    """Send a notification using a template from PUSH_TEMPLATES."""
    template = PUSH_TEMPLATES.get(template_key)
    if not template:
        return {"status": "unknown_template", "template_key": template_key}

    title = template["title"].format(**kwargs)
    body = template["body"].format(**kwargs)
    data = {"screen": template["data_screen"]}
    data.update({k: v for k, v in kwargs.items() if k not in ("brand_name", "s")})

    return await send_push_notification(
        expo_push_token=expo_push_token,
        title=title,
        body=body,
        data=data,
    )


async def send_push_notification(
    expo_push_token: str,
    title: str,
    body: str,
    data: dict | None = None,
) -> dict:
    """Send a push notification via Expo Push API."""
    if not expo_push_token or not expo_push_token.startswith("ExponentPushToken"):
        logger.warning("Invalid Expo push token", token=expo_push_token[:20] if expo_push_token else "None")
        return {"status": "invalid_token"}

    payload = {
        "to": expo_push_token,
        "title": title,
        "body": body,
        "sound": "default",
        "priority": "high",
    }
    if data:
        payload["data"] = data

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                EXPO_PUSH_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            result = response.json()
            logger.info("Push notification sent", token=expo_push_token[:30], status=response.status_code)
            return {"status": "sent", "response": result}
    except Exception as exc:
        logger.error("Push notification failed", error=str(exc))
        return {"status": "failed", "error": str(exc)}


async def send_validation_notification(
    expo_push_token: str,
    posts_count: int,
    brand_name: str = "PresenceOS",
) -> dict:
    """Send notification when new posts are ready for validation."""
    return await send_push_notification(
        expo_push_token=expo_push_token,
        title=f"📱 {posts_count} nouveau{'x' if posts_count > 1 else ''} post{'s' if posts_count > 1 else ''} à valider",
        body=f"{brand_name} — Vos posts IA sont prêts. Validez-les avant publication.",
        data={"screen": "ValidationInbox", "count": posts_count},
    )


async def send_published_notification(
    expo_push_token: str,
    platform: str,
    brand_name: str = "PresenceOS",
) -> dict:
    """Send notification when a post is published."""
    return await send_push_notification(
        expo_push_token=expo_push_token,
        title="✅ Post publié !",
        body=f"Votre post a été publié sur {platform}.",
        data={"screen": "ProposalsList", "platform": platform},
    )
