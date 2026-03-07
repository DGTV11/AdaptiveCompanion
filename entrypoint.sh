#!/bin/sh
set -e

# exec uv run fastapi run main.py --host 0.0.0.0 --port 5555
exec socat TCP-LISTEN:5555,reuseaddr,fork EXEC:'uv run main.py',stderr
