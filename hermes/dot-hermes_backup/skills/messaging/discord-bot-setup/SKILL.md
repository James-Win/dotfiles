---
name: discord-bot-setup
description: Complete guide to safely deploying a Hermes Discord bot from scratch, including auth, intents, and troubleshooting silent bots.
version: 1.0.0
platforms: [linux]
metadata:
  hermes:
    category: messaging
    tags:
      - discord
      - gateway
      - auth
---

# Discord Bot Setup & Troubleshooting Skill

## Purpose
Use this skill when James needs to create, deploy, or debug the Hermes Discord Gateway integration. 

## Requirements
- Access to the [Discord Developer Portal](https://discord.com/developers/applications).
- Running Hermes Agent with `gateway` subcommand available.

## Deployment Steps (From Scratch)

### 1. Developer Portal Config
1. Create a **New Application** in the Developer Portal.
2. Go to the **Bot** tab:
   - Click "Reset Token" to obtain the `DISCORD_BOT_TOKEN`.
   - **CRITICAL**: Scroll down to **Privileged Gateway Intents** and turn **ON** the **Message Content Intent**. (If skipped, the bot connects but receives zero `MESSAGE_CREATE` events).
   - If intending to use DMs, ensure **Enable direct messages from other users** is turned ON.

### 2. Add to Server
1. Go to **OAuth2 -> URL Generator**.
2. Check `bot` and `applications.commands` scopes.
3. Select `Administrator` (or explicitly `Send Messages` and `Read Messages/View Channels`).
4. Copy the URL and authorize the bot into the target server.

### 3. Hermes Configuration
Set the token and authorize James using his specific Discord ID so the bot doesn't ignore him:

```bash
hermes config set DISCORD_BOT_TOKEN "token_here"
hermes config set DISCORD_ALLOWED_USERS "360269299757219841"
```

### 4. Background Service Management
Deploy the gateway as a durable background user service:

```bash
hermes gateway install
systemctl --user restart hermes-gateway
systemctl --user status hermes-gateway
journalctl --user -u hermes-gateway -n 50 -f
```

## Troubleshooting "Silent Bot" (Connects but ignores messages)

If the `.log` says `✓ discord connected` but it ignores messages, follow this flow:

### Hypothesis 1: User Not Authorized (The Silent Ignorer)
By default, Hermes drops messages from non-allowlisted users. For slash commands, it surfaces an ephemeral error: `"You're not authorized to use this command"`. For raw text, it drops them silently. If the user receives a private Discord system message stating *"You're not authorized to use this command."* when they trigger an app mention or slash command, this is the exact signature of Hermes actively rejecting their Discord user ID.
**Check:**
```bash
grep -i "Unauthorized" ~/.hermes/logs/gateway*.log
```
**Fix:** Add user ID to `DISCORD_ALLOWED_USERS` in config.

### Hypothesis 2: Message Content Intent Missing
If Discord API doesn't pass message data, the bot receives ping events but no message payloads.
**Check:**
Run `hermes gateway run -vv` in the foreground. If `discord.gateway` shows heartbeat `op: 11` events but no `MESSAGE_CREATE` events when a user types, Discord is withholding the data.
Or, run the verification script included in this skill:
`bash ~/.hermes/skills/messaging/discord-bot-setup/scripts/check_discord_intents.sh`
**Fix:** Open the Discord Developer Portal, go to the **Bot** tab, scroll down to the "Privileged Gateway Intents" section, and ensure "Message Content Intent" is enabled. It is not enough to grant the `Administrator` permission via the OAuth URL; the intent must be explicitly toggled on the website. If the intent evaluates to True via API checks and the bot is still deaf, the server may have cached a bad invite configuration. Generate a strict invite URL forcing the scopes: `https://discord.com/oauth2/authorize?client_id=<YOUR_ID>&permissions=8&integration_type=0&scope=bot+applications.commands` and authorize it over the existing bot.

### Hypothesis 3: Ghost/Zombie Bot
User created a new bot in the dev portal but is DMing the *old* offline bot in their Discord list.
**Fix:** Delete the old DM thread. Ensure they are messaging the bot that shows a green "Online" status. 

### Hypothesis 4: Channel Permissions
The bot role doesn't have `View Channel` privileges for the channel the user is typing in.
**Fix:** Use a default public channel or grant the bot role explicit access.