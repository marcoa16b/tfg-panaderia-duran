import os

import reflex as rx

config = rx.Config(
    app_name="dev",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ],
    db_url=os.environ.get("DATABASE_URL", "sqlite:///reflex.db"),
)
