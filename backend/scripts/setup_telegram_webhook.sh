#!/usr/bin/env bash
# PresenceOS - Setup Telegram Bot Webhook
#
# Usage:
#   ./scripts/setup_telegram_webhook.sh <YOUR_PUBLIC_URL>
#
# Example:
#   ./scripts/setup_telegram_webhook.sh https://api.presenceos.com
#   ./scripts/setup_telegram_webhook.sh https://abc123.ngrok.io
#
# This registers the Telegram webhook so that updates are sent to:
#   POST <YOUR_PUBLIC_URL>/webhooks/telegram

set -euo pipefail

# Load .env if available
if [ -f "$(dirname "$0")/../.env" ]; then
    # shellcheck disable=SC1091
    export $(grep -v '^#' "$(dirname "$0")/../.env" | grep TELEGRAM_ | xargs)
fi

if [ -z "${TELEGRAM_BOT_TOKEN:-}" ]; then
    echo "Error: TELEGRAM_BOT_TOKEN is not set."
    echo "Set it in backend/.env or export it before running this script."
    exit 1
fi

PUBLIC_URL="${1:-}"
if [ -z "$PUBLIC_URL" ]; then
    echo "Usage: $0 <PUBLIC_URL>"
    echo "Example: $0 https://api.presenceos.com"
    exit 1
fi

WEBHOOK_URL="${PUBLIC_URL}/webhooks/telegram"
SECRET="${TELEGRAM_WEBHOOK_SECRET:-}"

echo "Setting Telegram webhook..."
echo "  Bot Token: ${TELEGRAM_BOT_TOKEN:0:10}..."
echo "  Webhook URL: ${WEBHOOK_URL}"
echo "  Secret Token: ${SECRET:+(set)}"
echo ""

# Build the API URL
API_URL="https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook"

# Build curl args
CURL_ARGS=(
    -X POST
    "$API_URL"
    -d "url=${WEBHOOK_URL}"
)

if [ -n "$SECRET" ]; then
    CURL_ARGS+=(-d "secret_token=${SECRET}")
fi

# Set allowed updates
CURL_ARGS+=(-d 'allowed_updates=["message","callback_query"]')

RESPONSE=$(curl -s "${CURL_ARGS[@]}")

echo "Response from Telegram:"
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"

# Verify webhook info
echo ""
echo "Webhook info:"
curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getWebhookInfo" | python3 -m json.tool 2>/dev/null
