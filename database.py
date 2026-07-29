import sqlite3
from datetime import datetime
from config import DB_PATH

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    """SQLite 데이터베이스 초기화 및 테이블 생성"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sent_articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                source TEXT NOT NULL,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

def is_article_recorded(url: str) -> bool:
    """기사 URL의 기록 여부 확인"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM sent_articles WHERE url = ?", (url,))
        return cursor.fetchone() is not None

# Alias for backwards compatibility
is_article_sent = is_article_recorded

def record_article(url: str, title: str, source: str):
    """수집 완료된 기사 URL 저장"""
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT OR IGNORE INTO sent_articles (url, title, source, sent_at) VALUES (?, ?, ?, ?)",
                (url, title, source, datetime.now().isoformat())
            )
            conn.commit()
        except sqlite3.Error as e:
            print(f"[DB Error] 기사 기록 실패: {e}")

mark_article_sent = record_article

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully.")
