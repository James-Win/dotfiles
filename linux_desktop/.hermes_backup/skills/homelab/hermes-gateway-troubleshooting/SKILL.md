---
name: hermes-gateway-troubleshooting
description: Debugging the native Hermes Gateway (Discord, Telegram) when running as a systemd user service.
version: 1.0.0
platforms: [linux]
metadata:
  hermes:
    category: homelab
    tags: [hermes, gateway, discord, systemd, troubleshooting]
---

# Hermes Gateway Troubleshooting

Use this skill when investigating connection issues or restarts with `hermes gateway`.

## Background Context
The Hermes Gateway is the native messaging integration engine linking Discord, Telegram, Signal, etc., to a Hermes instance. It typically runs as a systemd user service (`hermes-gateway.service`).

## Pitfall: Restarting from the Inside
**CRITICAL:** Never attempt to restart the gateway (`hermes gateway restart`, `systemctl --user restart hermes-gateway`) from _within_ a workflow that the gateway is actively executing. 

Doing so will issue a SIGTERM that propagates down, killing the agent instantly and stranding the user without a response. Instead, run diagnostics, instruct the user to bounce the service themselves from an external terminal, or structure the command to detach fully.

## Pitfall: Discord Silent Drops (Intents & Old Bots)
If the gateway's logs (`~/.hermes/logs/gateway.log`) show a successful connection (e.g. `[Discord] Connected as...`) but the bot ignores DMs or server messages:
1. **Message Content Intent**: Check the Discord Developer Portal -> Bot -> Privileged Gateway Intents -> "Message Content Intent". If off, the API drops inbound text completely. The bot will appear online but be deaf.
2. **Ghost Bots**: The user may have invited the bot, then created a *new* app in the portal to get a new token, but never kicked the old offline bot and invited the new app. The user might be DMing the offline 'ghost' bot while the new gateway token belongs to a different app ID. Check the discriminator (e.g. `#6024` vs `#0116`) or use an explicitly generated invite URL with the correct Client ID.
3. The user must fix Intents on the dev portal website and then restart the local gateway process.

## Tracing Activity
- `journalctl --user -u hermes-gateway -n 50 --no-pager`
- `tail -n 100 ~/.hermes/logs/gateway*.log` (verbose internal connection state, check `gateway-debug.log` and `gateway-exit-diag.log` too)

## Hardcore Debugging (WebSocket Level)
If Discord connects but messages still seemingly vanish despite Intents being enabled and the bot being online, force `hermes gateway run -vv` to dump raw WebSocket traffic.
Wait for `[Discord] Connected`, send a test message, and look for `discord.gateway: For Shard ID None: Dispatching event MESSAGE_CREATE`.
If only heartbeat (`op: 11`) events appear and NO `MESSAGE_CREATE` block appears upon sending, Discord is physically withholding the event at the source API level. This definitively confirms it is a Discord-side permission issue (e.g., bot lacks "View Channel" right, or Discord DM setting is disabled).
