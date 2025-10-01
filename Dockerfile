FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app /app
# Tests directory removed as it doesn't exist

# ---- LIGNE CORRIGÉE ----
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]