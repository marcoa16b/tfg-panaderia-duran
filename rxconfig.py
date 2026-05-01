import os

from dotenv import load_dotenv

load_dotenv()

import reflex as rx

ENV = os.environ.get("APP_ENV", "local")

cors_origins = (
    [
        "http://127.0.0.1:3020",
        "http://localhost:3020",
        "http://127.0.0.1:3040",
        "http://localhost:3040",
    ]
    if ENV == "local"
    else [
        "https://duran.nandev.online",
    ]
)

config = rx.Config(
    app_name="dev",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ],
    db_url=os.environ.get("DATABASE_URL", "sqlite:///reflex.db"),
    frontend_port=int(os.environ.get("APP_PORT", 3020)),
    backend_port=int(os.environ.get("BACKEND_PORT", 8020)),
    cors_allowed_origins=cors_origins,
    deploy_url="https://duran.nandev.online",
    api_url=(
        "https://duran-api.nandev.online"
        if ENV == "production"
        else None # Local: Reflex usa la misma host
    ),
)
