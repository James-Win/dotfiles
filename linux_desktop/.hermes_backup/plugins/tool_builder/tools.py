import os
import json
from pathlib import Path

def scaffold_custom_tool(plugin_name: str, tool_name: str, description: str, parameters_schema: dict, python_code: str) -> str:
    """Takes the agent's generated code and writes it as a valid Hermes plugin."""
    try:
        # Resolve the Hermes plugins directory
        base_dir = Path(os.path.expanduser("~/.hermes/plugins")) / plugin_name
        base_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. Generate plugin.yaml
        yaml_content = f"""name: {plugin_name}
version: 1.0.0
description: {description}
provides_tools:
  - {tool_name}
"""
        (base_dir / "plugin.yaml").write_text(yaml_content)
        
        # 2. Generate schemas.py
        schema_obj = {
            "name": tool_name,
            "description": description,
            "parameters": parameters_schema
        }
        (base_dir / "schemas.py").write_text(f"SCHEMA = {json.dumps(schema_obj, indent=4)}\n")
        
        # 3. Generate tools.py
        (base_dir / "tools.py").write_text(python_code)
        
        # 4. Generate __init__.py
        init_content = f"""from .schemas import SCHEMA
from .tools import {tool_name}

def register(ctx):
    ctx.register_tool(
        name="{tool_name}",
        schema=SCHEMA,
        handler=lambda args, **kwargs: {tool_name}(**args)
    )
"""
        (base_dir / "__init__.py").write_text(init_content)
        
        return json.dumps({
            "status": "success", 
            "message": f"Successfully created the '{tool_name}' tool in the '{plugin_name}' plugin. Tell the user they must restart the Hermes Agent process so the new tool can be loaded into memory."
        })
        
    except Exception as e:
        return json.dumps({"error": f"Failed to scaffold tool: {str(e)}"})
