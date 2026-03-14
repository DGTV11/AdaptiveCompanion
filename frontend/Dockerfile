FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# RUN apt-get update && apt-get install -y docker.io libmagic1
RUN apt-get update && apt-get install -y socat

WORKDIR /app

COPY pyproject.toml uv.lock .

ENV UV_HTTP_TIMEOUT=120

RUN uv sync --locked # --compile-bytecode

ADD frontend/app/ .

EXPOSE 5555

CMD ["uv", "run", "textual", "serve", "main.py", "-h", "0.0.0.0", "-p", "5555"]
