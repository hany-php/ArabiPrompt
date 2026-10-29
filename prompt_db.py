# prompt_db.py
import sqlite3
import os

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompts_library.db")

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """تهيئة جدول قاعدة البيانات للبرومبتات المحفوظة"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prompts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT DEFAULT 'عام',
                arabic_input TEXT,
                english_prompt TEXT NOT NULL,
                task_type TEXT DEFAULT 'General',
                model_used TEXT DEFAULT '',
                is_favorite INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

def save_prompt(title, english_prompt, arabic_input="", task_type="General", model_used="", category="عام", is_favorite=0):
    """حفظ برومبت جديد في قاعدة البيانات"""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO prompts (title, category, arabic_input, english_prompt, task_type, model_used, is_favorite)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (title.strip(), category.strip(), arabic_input.strip(), english_prompt.strip(), task_type.strip(), model_used.strip(), 1 if is_favorite else 0))
        conn.commit()
        return cursor.lastrowid

def get_prompts(search_query="", category_filter="الكل", favorites_only=False):
    """البحث واسترجاع البرومبتات مع الفلترة حسب النص أو الفئة أو المفضلة"""
    init_db()
    query = "SELECT * FROM prompts WHERE 1=1"
    params = []

    if search_query and search_query.strip():
        term = f"%{search_query.strip()}%"
        query += " AND (title LIKE ? OR english_prompt LIKE ? OR arabic_input LIKE ?)"
        params.extend([term, term, term])

    if category_filter and category_filter != "الكل":
        query += " AND category = ?"
        params.append(category_filter)

    if favorites_only:
        query += " AND is_favorite = 1"

    query += " ORDER BY is_favorite DESC, created_at DESC"

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

def get_prompt_by_id(prompt_id):
    """جلب تفاصيل برومبت محدد بواسطة المعرف"""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM prompts WHERE id = ?", (prompt_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def toggle_favorite(prompt_id):
    """تبديل حالة المفضلة لبرومبت معين"""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE prompts SET is_favorite = 1 - is_favorite WHERE id = ?", (prompt_id,))
        conn.commit()
        cursor.execute("SELECT is_favorite FROM prompts WHERE id = ?", (prompt_id,))
        row = cursor.fetchone()
        return row[0] if row else 0

def delete_prompt(prompt_id):
    """حذف برومبت من قاعدة البيانات"""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM prompts WHERE id = ?", (prompt_id,))
        conn.commit()
        return cursor.rowcount > 0

def get_categories():
    """جلب قائمة الفئات المتوفرة لاستخدامها في التصفية"""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT category FROM prompts WHERE category IS NOT NULL AND category != ''")
        rows = cursor.fetchall()
        default_cats = ["صور / تصميم", "نصوص / مقالات", "برمجة / كود", "عام"]
        existing = [r[0] for r in rows if r[0]]
        all_cats = list(dict.fromkeys(default_cats + existing))
        return all_cats
