# TOON Format for Token Optimization

TOON (Token-Oriented Object Notation) is a compact encoding for JSON data designed for LLM input. It can reduce token consumption by 30-60% for flat, uniform arrays.

## Example

JSON:
```json
{
  "products": [
    { "id": 1, "name": "Laptop", "price": 999 },
    { "id": 2, "name": "Mouse", "price": 29 }
  ]
}
```

TOON:
```text
products[2]{id,name,price}:
  1,Laptop,999
  2,Mouse,29
```

## When to Use

Use TOON for flat product listings, user records, logs, search results, and tables.

Avoid TOON for deeply nested data, non-uniform data, or direct nested MCP responses. Bright Data `web_data_*` responses often need flattening first.

## Pipeline

1. Fetch structured JSON with Bright Data MCP.
2. Flatten nested objects to the fields needed.
3. Encode flattened array as TOON before passing to an LLM.
4. Keep original JSON for programmatic processing.
