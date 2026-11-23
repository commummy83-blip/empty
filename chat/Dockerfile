FROM python:3.13-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY webchat.py container_app.py ./
USER 10001:10001
EXPOSE 8765
CMD ["python", "-m", "uvicorn", "container_app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8765", "--workers", "1", "--ws-max-size", "65536"]
