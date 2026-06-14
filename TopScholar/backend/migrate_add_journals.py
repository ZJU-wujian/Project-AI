"""为 journals 表添加 issn, crossref_filter 列"""
import sys
sys.path.insert(0, '.')
from app.database import engine
from app.config import settings
from sqlalchemy import text

print("数据库:", settings.DATABASE_URL)

with engine.connect() as conn:
    result = conn.execute(text('PRAGMA table_info(journals)'))
    cols = [row[1] for row in result.fetchall()]
    print("现有列:", cols)

with engine.connect() as conn:
    if 'issn' not in cols:
        conn.execute(text('ALTER TABLE journals ADD COLUMN issn VARCHAR(20)'))
        print("✓ 新增 issn 列")
    if 'crossref_filter' not in cols:
        conn.execute(text('ALTER TABLE journals ADD COLUMN crossref_filter VARCHAR(500)'))
        print("✓ 新增 crossref_filter 列")
    conn.commit()

with engine.connect() as conn:
    result = conn.execute(text('PRAGMA table_info(journals)'))
    cols = [row[1] for row in result.fetchall()]
    print("最终列:", cols)
