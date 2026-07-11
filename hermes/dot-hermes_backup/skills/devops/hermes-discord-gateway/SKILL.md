---
name: hermes-discord-gateway
description: Managing the Hermes Discord bot via the native Hermes Gateway rather than a legacy standalone script.
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    category: devops
    tags: [discord, gateway, bot, setup, config]
---

# Hermes Discord Gateway

## Context
Hermes has transitioned away from standalone bot scripts (like `discord-hermes-bot.service` using `discord.py`) towards the native `hermes gateway` command for bridging messaging platforms.

## Architecture
- **No standalone directory:** The bot project no longer lives in `~/discord-hermes-bot`.
- **No standalone service unit:** Do not look for `discord-hermes-bot.service`.
- **Token storage:** The token is set via `hermes config set DISCORD_BOT_TOKEN <token>` and is stored in `~/.hermes/.env`.
- **Execution:** Managed via `hermes gateway start` / `systemctl --user status hermes.service` (or `hermes-gateway.service` depending on install version, check `hermes status`).

## Troubleshooting missing Discord bot
If the user asks about the Discord bot and it cannot be found at legacy paths:
1. Check `hermes status` (look at Gateway Service).
2. Check `hermes config show` and `.env` for `DISCORD_BOT_TOKEN`.
3. If missing entirely, guide the user to the Discord Developer Portal to retrieve their bot token.
4. DO NOT suggest reinstalling `discord.py` or searching for the old script unless explicitly asked to retrieve old data.
5. Set token: `hermes config set DISCORD_BOT_TOKEN "<token>"`
6. Start gateway: `hermes gateway start`

## Common Pitfalls & Setup Traps

1. **Missing Message Content Intent**: If the gateway successfully connects to Discord but the bot doesn't reply or log incoming messages, the most common culprit is that the `Message Content Intent` toggle is still OFF in the Discord Developer Portal -> Bot tab. If this is off, Discord drops the messages _before_ they ever reach Hermes. **You MUST toggle this explicitly ON**.
2. **Ghost Bot Accounts**: If the user reset their bot/app in the portal, confirm they actually _kicked_ the old offline bot from the Discord server and invited the newly generated one. A user confusing a deprecated bot for the new instance will see no replies. Tell them to check the `#XXXX` discriminator tag in the gateway logs (`[Discord] Connected as...`) against the Discord account they are trying to message.
3. **Restarting the Gateway**: Any changes to Intents or Discord scopes in the Developer Portal _require_ restarting the Hermes gateway so the API connection picks up the new scopes (`hermes gateway restart`). Ensure the user runs this from outside the gateway process.

## Setup instructions for user
1. Go to Discord Developer Portal: [https://discord.com/developers/applications](https://discord.com/developers/applications)
2. Get Bot Token.
3. Enable 'Message Content Intent' in Privileged Gateway Intents (CRITICAL).
4. Invite bot via OAuth2 URL Generator (Scopes: `bot`, permissions: `Send Messages`, `Read Messages`, `Attach Files`).
5. Run `hermes config set DISCORD_BOT_TOKEN "<token>"`
6. Run `hermes gateway restart` (or `hermes gateway start` if stopped).
