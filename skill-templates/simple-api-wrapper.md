# Simple API Wrapper Template

For wrapping external APIs that require minimal processing. Perfect for weather services, news feeds, status checks, or any HTTP-based data source.

## Template Files

### SKILL.md
```markdown
---
name: your-service
description: Brief description of what this service provides and when to use it.
homepage: https://service-docs.example.com
metadata: { "openclaw": { "emoji": "🌐", "requires": { "bins": ["curl"] } } }
---

# Your Service Name

Brief description. Mention if API keys are required or if it's free.

## Quick Usage

```bash
# Basic query
curl -s "https://api.example.com/v1/endpoint?param=value"
```

## Common Patterns

### Get current status
```bash
curl -s "https://api.example.com/status"
```

### Query with parameters
```bash
# URL-encode spaces and special chars
curl -s "https://api.example.com/search?q=your+query"
```

### JSON processing
```bash
curl -s "https://api.example.com/data" | jq '.field.subfield'
```

## Response Format

Describe the typical response structure and key fields.

## Error Handling

Common error responses and what they mean:
- 429: Rate limited (wait and retry)
- 401: Invalid API key
- 404: Resource not found

## Alternatives

List backup services or alternative approaches if this API fails.
```

### Example Implementation

Based on the weather skill pattern:

```markdown
---
name: news-headlines
description: Get current news headlines (no API key required).
homepage: https://newsapi.org/docs
metadata: { "openclaw": { "emoji": "📰", "requires": { "bins": ["curl", "jq"] } } }
---

# News Headlines

Get current headlines from multiple free sources without API keys.

## Quick Headlines

```bash
# Top headlines (RSS to JSON)
curl -s "https://rss-to-json-api.vercel.app/api?rss_url=https://feeds.reuters.com/reuters/topNews" | jq -r '.items[0:5][] | "• \(.title)"'
```

## Multiple Sources

```bash
# Reuters
curl -s "https://rss-to-json-api.vercel.app/api?rss_url=https://feeds.reuters.com/reuters/topNews" | jq -r '.items[0:3][] | "• \(.title)"'

# BBC
curl -s "https://rss-to-json-api.vercel.app/api?rss_url=http://feeds.bbci.co.uk/news/rss.xml" | jq -r '.items[0:3][] | "• \(.title)"'
```

## Formatted Output

```bash
# With timestamp and source
curl -s "https://rss-to-json-api.vercel.app/api?rss_url=https://feeds.reuters.com/reuters/topNews" | jq -r '.items[0:5][] | "\(.pubDate | .[0:10]) | \(.title)"'
```

## Filtering

```bash
# Filter by keyword
curl -s "https://rss-to-json-api.vercel.app/api?rss_url=https://feeds.reuters.com/reuters/topNews" | jq -r '.items[] | select(.title | contains("Climate")) | "• \(.title)"'
```

## Fallback Sources

If primary RSS fails:
- HackerNews: `https://hnrss.org/frontpage`
- Reddit: `https://www.reddit.com/r/news/.rss`
```

## Customization Checklist

- [ ] Replace `your-service` with actual service name
- [ ] Update API endpoints and parameters
- [ ] Add authentication if required (env vars, headers)
- [ ] Test response parsing and error scenarios  
- [ ] Document rate limits and usage guidelines
- [ ] Add fallback sources or offline functionality
- [ ] Include relevant emoji in metadata

## Dependencies

- `curl` - HTTP client
- `jq` - JSON processing (if API returns JSON)
- Environment variables for API keys (if needed)

## Integration Tips

1. **Error Handling**: Always check HTTP status codes
2. **Rate Limiting**: Implement backoff for 429 responses
3. **Caching**: Cache responses locally to reduce API calls
4. **Monitoring**: Log failures for debugging
5. **Documentation**: Include example responses in SKILL.md