from .schemas import SCHEMA
from .tools import tail_log

def register(ctx):
    ctx.register_tool(
        name="tail_log",
        schema=SCHEMA,
        handler=lambda args, **kwargs: tail_log(**args)
    )
