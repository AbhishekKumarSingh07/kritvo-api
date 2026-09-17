"""Write the committed API contract used by kritvo-web.

Usage: uv run kritvo-openapi [output-path]   (default: openapi/openapi.json)
"""

import json
import sys
from pathlib import Path

from kritvo.main_api import create_app

DEFAULT_OUTPUT = Path("openapi/openapi.json")


def render() -> str:
    spec = create_app().openapi()
    return json.dumps(spec, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main() -> None:
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUTPUT
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render(), encoding="utf-8")
    sys.stdout.write(f"Wrote {output}\n")


if __name__ == "__main__":
    main()
