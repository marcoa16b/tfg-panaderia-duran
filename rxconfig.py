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

config_kwargs = dict(
    app_name="dev",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ],
    db_url=os.environ.get("DATABASE_URL", "sqlite:///reflex.db"),
    cors_allowed_origins=["*"],
    api_url="https://duran.nandev.online",
)

config = rx.Config(**config_kwargs)
