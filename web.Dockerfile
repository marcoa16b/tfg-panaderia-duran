FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl unzip nodejs npm && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# API_URL se inyecta en build time
ARG API_URL=https://duran.nandev.online
ENV API_URL=$API_URL

COPY . .
RUN reflex init
RUN reflex export --frontend-only --no-zip

# Imagen final con nginx
FROM nginx:alpine
COPY --from=builder /app/.web/_static /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 3000