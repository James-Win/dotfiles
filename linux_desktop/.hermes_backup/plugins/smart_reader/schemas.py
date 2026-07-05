SCHEMA = {
    "name": "tail_log",
    "description": "Read the last N lines of a file or log. ALWAYS use this instead of reading an entire file to save context tokens.",
    "parameters": {
        "type": "object",
        "properties": {
            "filepath": {
                "type": "string",
                "description": "Path to the file or log to read"
            },
            "lines": {
                "type": "integer",
                "description": "Number of trailing lines to read",
                "default": 50
            }
        },
        "required": [
            "filepath"
        ]
    }
}
