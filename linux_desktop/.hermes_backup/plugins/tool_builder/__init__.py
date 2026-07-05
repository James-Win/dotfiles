from .schemas import SCAFFOLD_SCHEMA
from .tools import scaffold_custom_tool

def register(ctx):
    ctx.register_tool(
        name="scaffold_custom_tool",
        schema=SCAFFOLD_SCHEMA,
        handler=lambda args, **kwargs: scaffold_custom_tool(
            plugin_name=args.get("plugin_name"),
            tool_name=args.get("tool_name"),
            description=args.get("description"),
            parameters_schema=args.get("parameters_schema"),
            python_code=args.get("python_code")
        )
    )
