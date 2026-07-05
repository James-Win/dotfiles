# Bright Data MCP Integrations

Supported clients include Claude Desktop/Code, Codex, Cursor, VS Code, ChatGPT, LangChain, LlamaIndex, CrewAI, Google ADK, OpenAI SDK, and n8n.

## Remote vs Local

| Aspect | Remote | Local |
|--------|--------|-------|
| Setup | URL only | `npx @brightdata/mcp` |
| Updates | Automatic | Manual |
| Latency | Slightly higher | Lower |
| Offline | No | Yes after install |
| Configuration | URL parameters | Environment variables |

Recommendation: use remote for simplicity/updates; local for lower latency, offline needs, or custom zone configuration.

## Codex Remote Example

```toml
[mcp_servers.brightdata]
command = "npx"
args = ["mcp-remote", "https://mcp.brightdata.com/mcp?token=YOUR_API_TOKEN"]
```

With Pro:
```toml
[mcp_servers.brightdata]
command = "npx"
args = ["mcp-remote", "https://mcp.brightdata.com/mcp?token=YOUR_API_TOKEN&pro=1"]
```

## Browser Automation

To use browser control tools:
1. Create a Browser API zone in Bright Data.
2. Configure remote with `&browser=your_zone_name` or local with `BROWSER_ZONE=your_zone_name`.
3. Ask for confirmation before creating zones or storing tokens.

## Usage Monitoring

Use `session_stats` and Bright Data dashboard usage pages. Free tier is 5,000 requests/month.
