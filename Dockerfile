FROM python:3.11-slim-bookworm

WORKDIR /app

# Instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Exponer puerto (Railway usa $PORT dinámico)
EXPOSE 8000

# Usar $PORT inyectado por Railway
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]