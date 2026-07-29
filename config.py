import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

DB_PATH = BASE_DIR / 'sent_articles.db'
DASHBOARD_HTML_PATH = BASE_DIR / 'dashboard.html'
DASHBOARD_TEMP_PATH = BASE_DIR / 'dashboard_temp.html'
LOGS_DIR = BASE_DIR / 'logs'

MAX_ARTICLES_PER_SOURCE = 5

USER_AGENT = (
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/120.0.0.0 Safari/537.36'
)
