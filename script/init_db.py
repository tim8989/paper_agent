# scripts/init_db.py

import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

load_dotenv()

db_params = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}

# 1️⃣ 建立資料庫（連線到預設 postgres）
conn = psycopg2.connect(dbname="postgres", **db_params)
conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
cur = conn.cursor()

cur.execute("SELECT 1 FROM pg_database WHERE datname = 'llm_papers'")
exists = cur.fetchone()
if not exists:
    cur.execute("CREATE DATABASE llm_papers")
    print("✅ 資料庫 llm_papers 已建立")
else:
    print("⚠️ 資料庫 llm_papers 已存在")

cur.close()
conn.close()

# 2️⃣ 建立資料表（切換到 llm_papers 資料庫）
conn2 = psycopg2.connect(dbname="llm_papers", **db_params)
cur2 = conn2.cursor()

cur2.execute("""
    CREATE TABLE IF NOT EXISTS papers (
        id SERIAL PRIMARY KEY,
        title TEXT NOT NULL,
        abstract TEXT,
        source TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
""")
conn2.commit()

print("✅ 資料表 papers 已建立")

cur2.close()
conn2.close()