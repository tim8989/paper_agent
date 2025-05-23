-- scripts/init_db.sql

-- 切換到 postgres 預設資料庫（執行前需在 psql 中）
CREATE DATABASE llm_papers;

\c llm_papers

-- 建立儲存論文的資料表
CREATE TABLE IF NOT EXISTS papers (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    abstract TEXT,
    source TEXT, -- 'internal_upload' or 'web_search'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);