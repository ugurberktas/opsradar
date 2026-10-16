FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    OPSRADAR_DATABASE_URL=sqlite:////data/opsradar.db

RUN pip install --no-cache-dir --upgrade pip

COPY requirements-prod.txt .
RUN pip install --no-cache-dir -r requirements-prod.txt

COPY app ./app

RUN addgroup --system opsradar \
    && adduser --system --ingroup opsradar opsradar \
    && mkdir -p /data \
    && chown -R opsradar:opsradar /data /app

USER opsradar

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
