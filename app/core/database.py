from app.models.seo import SEOData
import json
import sqlite3
from pathlib import Path

class SEODatabaseManager:
    def __init__(self):
        # Resolves database in the project root folder (parents[2] from app/core/database.py)
        self.db_path = Path(__file__).resolve().parents[2] / "seo_cache.db"
        self.conn = None
        
    def _init_db(self):
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS seo_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_target TEXT NOT NULL,
            seo_title TEXT NOT NULL,
            seo_description TEXT NOT NULL,
            seo_keywords TEXT NOT NULL,
            seo_content TEXT NOT NULL
        )
        """)
        self.conn.commit()
        
    def save_to_database(self, response: SEOData) -> None:
        self._init_db()
        self.cursor.execute("""
        INSERT INTO seo_cache (file_target, seo_title, seo_description, seo_keywords, seo_content)
        VALUES (?, ?, ?, ?, ?)
        """, (response.file_target, response.title, response.description, response.keywords, response.content))
        self.conn.commit()
        self.close_connection()
        
    def get_from_database(self, file_target: str) -> SEOData:
        self._init_db()
        self.cursor.execute("SELECT * FROM seo_cache WHERE file_target = ?", (file_target,))
        row = self.cursor.fetchone()
        self.close_connection()
        if row:
            return SEOData(row[1], row[2], row[3], row[4], row[5])
        return None
        
    def update_database(self, response: SEOData) -> None:
        self._init_db()
        self.cursor.execute("""
        UPDATE seo_cache SET seo_title = ?, seo_description = ?, seo_keywords = ?, seo_content = ? WHERE file_target = ?
        """, (response.title, response.description, response.keywords, response.content, response.file_target))
        self.conn.commit()
        self.close_connection()
        
    def delete_from_database(self, file_target: str) -> None:
        self._init_db()
        self.cursor.execute("DELETE FROM seo_cache WHERE file_target = ?", (file_target,))
        self.conn.commit()
        self.close_connection()
        
    def close_connection(self) -> None:
        if self.conn:
            self.conn.close()
