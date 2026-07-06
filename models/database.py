from __future__ import annotations

import sqlite3
from pathlib import Path


def init_database(db_path: Path) -> None:
    db_path.parent.mkdir(exist_ok=True)
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS inquiries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT NOT NULL,
                percentile REAL NOT NULL,
                category TEXT NOT NULL,
                branch TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.commit()
