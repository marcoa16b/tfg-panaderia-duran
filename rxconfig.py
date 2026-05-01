import os

from dotenv import load_dotenv

load_dotenv()

import reflex as rx

config = rx.Config(
    app_name="dev",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ],
    db_url=os.environ.get("DATABASE_URL", "sqlite:///reflex.db"),
    frontend_port=int(os.environ.get("APP_PORT", 3020)),
    backend_port=int(os.environ.get("BACKEND_PORT", 8020)),
)
