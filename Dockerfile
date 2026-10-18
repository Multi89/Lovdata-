FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MCP_HOST=0.0.0.0 \
    MCP_PORT=8000 \
    LOVDATA_DB_PATH=/app/data/lovdata.sqlite3 \
    LOVDATA_SERVER_MODE=actions

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY data ./data
COPY scripts/docker-entrypoint.sh /usr/local/bin/lovdata-entrypoint
RUN pip install --no-cache-dir . && chmod +x /usr/local/bin/lovdata-entrypoint

EXPOSE 8000
ENTRYPOINT ["lovdata-entrypoint"]
