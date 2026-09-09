# Placeholder — filled in once dependencies (pyproject.toml) are pinned during implementation.
FROM python:3.11-slim

WORKDIR /app

COPY . .

CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
