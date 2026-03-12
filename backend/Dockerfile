FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# RUN apt-get update && apt-get install -y docker.io libmagic1
RUN apt-get update && apt-get install -y socat

ADD backend/app/ /app

WORKDIR /app

COPY pyproject.toml uv.lock .

ENV UV_HTTP_TIMEOUT=120

RUN uv sync --locked # --compile-bytecode

EXPOSE 5555

CMD ["socat","TCP-LISTEN:5555,reuseaddr,fork","EXEC:uv run main.py,stderr"]
