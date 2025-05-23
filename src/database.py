# src/database.py
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
import os

load_dotenv()

DB_PARAMS = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD")
}

class Database:
    def __init__(self):
        self.conn = psycopg2.connect(**DB_PARAMS)
        self.setup_database()

    def setup_database(self):
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS papers (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    abstract TEXT,
                    source TEXT,
                    file_hash TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            self.conn.commit()

    def insert_metadata(self, title, abstract, file_hash, source="internal_upload"):
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO papers (title, abstract, source, file_hash) VALUES (%s, %s, %s, %s) ON CONFLICT (file_hash) DO NOTHING",
                (title, abstract, source, file_hash)
            )
            self.conn.commit()
            return cur.rowcount > 0

    def get_papers(self, limit=None):
        with self.conn.cursor() as cur:
            query = "SELECT id, title, abstract FROM papers ORDER BY id"
            if limit:
                query += f" LIMIT {limit}"
            cur.execute(query)
            return cur.fetchall()

    def get_paper_by_id(self, paper_id):
        with self.conn.cursor() as cur:
            cur.execute("SELECT title, abstract FROM papers WHERE id = %s", (paper_id,))
            return cur.fetchone()

    def delete_papers(self, paper_ids):
        with self.conn.cursor() as cur:
            cur.execute("DELETE FROM papers WHERE id = ANY(%s)", (paper_ids,))
            self.conn.commit()
            return cur.rowcount

    def get_known_hashes(self):
        with self.conn.cursor() as cur:
            cur.execute("SELECT file_hash FROM papers")
            return set(row[0] for row in cur.fetchall())

    def close(self):
        self.conn.close()