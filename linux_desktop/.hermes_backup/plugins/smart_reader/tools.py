import json
import subprocess


def tail_log(filepath: str, lines: int = 50) -> str:
    try:
        if lines is None:
            lines = 50
        result = subprocess.run(['tail', '-n', str(lines), filepath], capture_output=True, text=True)
        if result.returncode == 0:
            return json.dumps(result.stdout)
        return json.dumps(result.stderr)
    except Exception as exc:
        return json.dumps(str(exc))
