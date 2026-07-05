# Bright Data MCP Usage Examples

## Quick Examples

### Web Search
```text
Tool: search_engine
Input: { "query": "latest AI news", "engine": "google" }
```

### Company Research
```text
Tool: web_data_linkedin_company_profile
Input: { "url": "https://linkedin.com/company/bright-data" }
```

### Dynamic Site Interaction
```text
Tools: scraping_browser_navigate → scraping_browser_snapshot → scraping_browser_click_ref → scrape_as_markdown
```

## Workflow Patterns

### Research Agent Flow
1. Search for relevant sources with `search_engine`.
2. Scrape top results with `scrape_as_markdown`.
3. Summarize findings and cite URLs.

### E-commerce Monitoring
1. Use platform-specific tools like `web_data_amazon_product` or `web_data_walmart_product`.
2. Track price/availability fields.
3. Use batch tools when comparing multiple URLs.

### Social Media Analysis
1. Use platform-specific `web_data_*` tools when available.
2. Fall back to `scrape_as_markdown` + `extract` for unsupported platforms.

## Best Practices

- Choose the most specific structured tool available.
- Fall back gracefully to general scraping.
- Batch requests when possible.
- Monitor usage with `session_stats`.
- Respect rate limits, terms, robots.txt, and privacy expectations.
