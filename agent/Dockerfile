FROM python:3.12-slim

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /agent

COPY pyproject.toml uv.lock ./
RUN apt update && \
    apt install -y make && \
    uv sync --frozen --no-cache 

COPY app/ ./app/
COPY .env* Makefile ./

ENV PYTHONPATH=/agent

EXPOSE 8010

CMD [ "uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8010"]