# Bright Data MCP Setup Guide

## Prerequisites

1. Bright Data account (free tier: 5,000 requests/month)
2. API token from user settings
3. For local setup: Node.js installed

## Remote MCP (Recommended)

No installation required. Use the hosted server URL in your MCP client.

**SSE:**
```text
https://mcp.brightdata.com/sse?token=YOUR_API_TOKEN
```

**Streamable HTTP:**
```text
https://mcp.brightdata.com/mcp?token=YOUR_API_TOKEN
```

With Pro mode:
```text
https://mcp.brightdata.com/sse?token=YOUR_API_TOKEN&pro=1
```

With tool groups:
```text
https://mcp.brightdata.com/sse?token=YOUR_API_TOKEN&groups=ecommerce,social
```

With custom tools:
```text
https://mcp.brightdata.com/sse?token=YOUR_API_TOKEN&tools=scrape_as_markdown,web_data_linkedin_person_profile
```

## Local MCP

```bash
API_TOKEN=<token> npx @brightdata/mcp
```

Enable Pro mode:
```bash
API_TOKEN=<token> PRO_MODE=true npx @brightdata/mcp
```

Enable groups:
```bash
API_TOKEN=<token> GROUPS=ecommerce,social npx @brightdata/mcp
```

## Remote URL Parameters

| Parameter | Description |
|-----------|-------------|
| `token` | API token (required) |
| `pro` | Enable all Pro tools |
| `groups` | Tool group IDs, comma-separated |
| `tools` | Individual tool names, comma-separated |
| `unlocker` | Custom web unlocker zone |
| `browser` | Custom browser zone |

## Verify Setup

After configuration, test with a simple search:

```text
Tool: search_engine
Input: { "query": "test query", "engine": "google" }
```

## Troubleshooting

- `spawn npx ENOENT`: use full Node path.
- Timeouts: increase timeout to 180 seconds and prefer structured `web_data_*` tools.
- Authentication: verify token permissions and remove whitespace.
