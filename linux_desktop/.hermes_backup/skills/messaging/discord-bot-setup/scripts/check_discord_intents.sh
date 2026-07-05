#!/bin/bash
# Description: Verifies if the Discord bot token configured in Hermes has the 
# 'Message Content Intent' enabled at the API level. Useful for debugging silent bots.

if [ ! -f ~/.hermes/.env ]; then
    echo "Error: ~/.hermes/.env not found."
    exit 1
fi

source ~/.hermes/.env

if [ -z "$DISCORD_BOT_TOKEN" ]; then
    echo "Error: DISCORD_BOT_TOKEN is not set in ~/.hermes/.env"
    exit 1
fi

echo "Querying Discord API for bot application info..."
curl -s -H "Authorization: Bot $DISCORD_BOT_TOKEN" https://discord.com/api/v10/oauth2/applications/@me | \
python3 -c '
import sys, json

try:
    data = json.load(sys.stdin)
except json.JSONDecodeError:
    print("Error: Invalid JSON response from Discord API.")
    sys.exit(1)

if "message" in data and data.get("code") == 0:
    print(f"API Error: {data.get(\"message\")}")
    sys.exit(1)

bot_name = data.get("bot", {}).get("username", "Unknown")
flags = data.get("flags", 0)

# Message Content Intent is flag bit 18 (1 << 18) or 19 (1 << 19) depending on gateway version/context
content_intent = bool(flags & (1 << 18) or flags & (1 << 19))

print(f"Bot Username: {bot_name}")
print(f"App Flags:    {flags}")
print(f"Message Content Intent Enabled: {content_intent}")

if not content_intent:
    print("\nWARNING: Message Content Intent is FALSE. The bot will not receive MESSAGE_CREATE events.")
    print("Fix: Go to Discord Developer Portal -> Bot -> Privileged Gateway Intents -> Enable Message Content Intent.")
else:
    print("\nSUCCESS: Message Content Intent is TRUE. The bot is authorized to read messages.")
'