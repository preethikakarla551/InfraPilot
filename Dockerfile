FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 INFRAPILOT_DB=/data/infrapilot.db
WORKDIR /app
RUN useradd --create-home --uid 10001 appuser && mkdir -p /data && chown 10001:10001 /data
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
USER 10001
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
