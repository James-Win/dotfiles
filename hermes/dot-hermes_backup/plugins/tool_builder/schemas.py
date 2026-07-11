SCAFFOLD_SCHEMA = {
    "name": "scaffold_custom_tool",
    "description": "Create a new custom Python tool for yourself. Use this when you need to write a permanent script to interact with APIs, databases, or local hardware. You MUST provide the full Python logic.",
    "parameters": {
        "type": "object",
        "properties": {
            "plugin_name": {
                "type": "string",
                "description": "The folder name for the plugin (e.g., 'docker_manager', 'network_tools')"
            },
            "tool_name": {
                "type": "string",
                "description": "The exact python function name (e.g., 'restart_container')"
            },
            "description": {
                "type": "string",
                "description": "A clear description of what the tool does. This becomes your future prompt."
            },
            "parameters_schema": {
                "type": "object",
                "description": "The JSON schema defining the arguments your new tool will accept."
            },
            "python_code": {
                "type": "string",
                "description": "The full Python code for tools.py. Must include all necessary imports. Handlers MUST return JSON strings, never raise raw exceptions."
            }
        },
        "required": ["plugin_name", "tool_name", "description", "parameters_schema", "python_code"]
    }
}
