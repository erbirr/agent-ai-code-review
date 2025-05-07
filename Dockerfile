FROM python:3.11-slim

WORKDIR /app

# Copiar e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY . .


# Variables de entorno
ENV PORT=8080

# Comando de inicio en formato JSON recomendado
CMD ["sh", "-c", "uvicorn src.api.main:app --host 0.0.0.0 --port $PORT"]