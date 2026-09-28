FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && useradd --create-home appuser
COPY backend /app/backend
COPY frontend/src/preparation.json /app/frontend/src/preparation.json
RUN mkdir -p /app/data && chown -R appuser:appuser /app
USER appuser
EXPOSE 10000
CMD ["python", "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "10000", "--workers", "1"]