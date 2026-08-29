FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY argus_agent/ ./argus_agent/

ENV PYTHONPATH=/app
EXPOSE 8000

CMD ["python", "-m", "uvicorn", "argus_agent.main:app", "--host", "0.0.0.0", "--port", "8000"]
