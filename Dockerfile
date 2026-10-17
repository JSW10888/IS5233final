FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY app/requirements.txt ./requirements.txt

RUN python -m pip install --no-cache-dir -r requirements.txt \
    && groupadd --gid 10001 appuser \
    && useradd --uid 10001 --gid appuser --create-home appuser

COPY --chown=appuser:appuser app/ ./app/

USER appuser

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "main:app", "--app-dir", "app", "--host", "0.0.0.0", "--port", "8000"]