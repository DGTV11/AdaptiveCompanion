FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# RUN apt-get update && apt-get install -y docker.io libmagic1
RUN apt-get update && apt-get install -y socat

WORKDIR /app

COPY pyproject.toml uv.lock .

ENV UV_HTTP_TIMEOUT=120

RUN uv sync --locked # --compile-bytecode

ADD backend/app/ .

EXPOSE 5555

# CMD ["socat","TCP-LISTEN:5555,reuseaddr,fork","EXEC:uv run main.py,stderr"]
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5555"]
