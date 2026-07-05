# Bright Data MCP Tools Reference

## Modes

| Mode | Activation | Description |
|------|------------|-------------|
| Rapid | Default | Web search and basic scraping; 5,000 req/month free |
| Pro | `&pro=1` or `PRO_MODE=true` | All 60+ tools including structured data and browser |
| Groups | `&groups=` or `GROUPS=` | Domain-specific tool bundles |
| Custom | `&tools=` or `TOOLS=` | Cherry-pick individual tools |

`GROUPS` or `TOOLS` override `PRO_MODE` when specified.

## Groups

| Group ID | Description | Key Tools |
|----------|-------------|-----------|
| `ecommerce` | Retail and marketplace data | `web_data_amazon_product`, `web_data_walmart_product`, `web_data_google_shopping` |
| `social` | Social media and creator insights | `web_data_linkedin_posts`, `web_data_tiktok_posts`, `web_data_youtube_videos` |
| `browser` | Browser automation | `scraping_browser_*` |
| `finance` | Financial intelligence | `web_data_yahoo_finance_business` |
| `business` | Company and location data | `web_data_crunchbase_company`, `web_data_zoominfo_company_profile`, `web_data_zillow_properties_listing` |
| `research` | News and developer data | `web_data_github_repository_file`, `web_data_reuter_news` |
| `app_stores` | App store data | `web_data_google_play_store`, `web_data_apple_app_store` |
| `travel` | Travel information | `web_data_booking_hotel_listings` |
| `advanced_scraping` | Batch and AI extraction | `search_engine_batch`, `scrape_batch`, `extract` |

## Core Tools

### `search_engine`
```json
{ "query": "search terms", "engine": "google", "cursor": null }
```

### `scrape_as_markdown`
```json
{ "url": "https://example.com/page" }
```

## Advanced Scraping

- `search_engine_batch`: up to 10 searches in parallel
- `scrape_batch`: up to 10 URLs in one request
- `scrape_as_html`: raw HTML
- `extract`: scrape page and extract structured JSON using AI
- `session_stats`: report tool usage during current MCP session

## Browser Automation

- `scraping_browser_navigate`
- `scraping_browser_snapshot`
- `scraping_browser_click_ref`
- `scraping_browser_type_ref`
- `scraping_browser_screenshot`
- `scraping_browser_wait_for_ref`
- `scraping_browser_scroll`
- `scraping_browser_get_text`
- `scraping_browser_get_html`
- `scraping_browser_network_requests`

## Structured Data

E-commerce: Amazon, Walmart, eBay, Google Shopping, Home Depot, Best Buy, Etsy, Zara.

Social: LinkedIn, Instagram, Facebook, TikTok, X/Twitter, YouTube, Reddit.

Business/finance/research/app/travel: Crunchbase, ZoomInfo, Google Maps reviews, Zillow, Yahoo Finance, Reuters, GitHub repository files, Google Play, Apple App Store, Booking.com.
