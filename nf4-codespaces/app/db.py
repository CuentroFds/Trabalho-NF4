import os
from contextlib import contextmanager
import pymysql

@contextmanager
def conexao():
    db = pymysql.connect(host=os.getenv("DB_HOST", "db"),
        user=os.getenv("DB_USER", "api_lab"), password=os.getenv("DB_PASSWORD", "api_local"),
        database=os.getenv("DB_NAME", "loja_cerrado"), charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor, autocommit=False,
        connect_timeout=3, read_timeout=5, write_timeout=5)
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
