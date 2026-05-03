FROM python:3.12-slim

WORKDIR /app

# Dependencias del sistema
RUN apt-get update && apt-get install -y \
    curl unzip nodejs npm && \
    rm -rf /var/lib/apt/lists/*

# Dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Inicializar Reflex
RUN reflex init

EXPOSE 8000

CMD ["reflex", "run", "--env", "prod", "--backend-only"]